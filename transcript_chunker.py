#!/usr/bin/env python3
"""
Transcript Chunker
Smart chunking of ASR transcript segments by time interval for better TTS performance.
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ChunkConfig:
    """Configuration for transcript chunking."""
    max_duration: float = 30.0  # Maximum chunk duration in seconds
    use_model_chunking: bool = False  # Use model-level chunking if available
    min_chunk_duration: float = 5.0  # Minimum chunk duration to avoid very short chunks
    sentence_break_buffer: float = 2.0  # Buffer time to find natural sentence breaks

class TranscriptChunker:
    """
    Smart transcript chunker that groups ASR segments into optimal chunks for TTS.
    """
    
    def __init__(self, config: ChunkConfig = None):
        """Initialize chunker with configuration."""
        self.config = config or ChunkConfig()
        
    def chunk_transcript_by_time(self, asr_segments: List[Dict], max_duration: float = None) -> List[Dict]:
        """
        Group transcript segments into chunks by time interval.
        
        Args:
            asr_segments: List of ASR segments with start, end, text
            max_duration: Maximum chunk duration (overrides config)
            
        Returns:
            List of chunked segments with combined text
        """
        if not asr_segments:
            return []
        
        max_dur = max_duration or self.config.max_duration
        chunks = []
        
        current_chunk = {
            'start': asr_segments[0]['start'],
            'end': None,
            'text_segments': [],
            'segment_count': 0
        }
        
        for i, segment in enumerate(asr_segments):
            segment_start = float(segment['start'])
            segment_end = float(segment['end'])
            segment_text = str(segment['text']).strip()
            
            # Calculate potential chunk duration if we add this segment
            potential_duration = segment_end - current_chunk['start']
            
            # Check if adding this segment would exceed max duration
            if potential_duration <= max_dur:
                # Add segment to current chunk
                current_chunk['text_segments'].append(segment_text)
                current_chunk['end'] = segment_end
                current_chunk['segment_count'] += 1
            else:
                # Current chunk is full, finalize it
                if current_chunk['text_segments']:
                    chunks.append(self._finalize_chunk(current_chunk))
                
                # Start new chunk with current segment
                current_chunk = {
                    'start': segment_start,
                    'end': segment_end,
                    'text_segments': [segment_text],
                    'segment_count': 1
                }
        
        # Add the last chunk if it has content
        if current_chunk['text_segments']:
            chunks.append(self._finalize_chunk(current_chunk))
        
        # Post-process chunks to optimize boundaries
        optimized_chunks = self._optimize_chunk_boundaries(chunks, asr_segments)
        
        print(f"📊 Chunking results:")
        print(f"  • Original segments: {len(asr_segments)}")
        print(f"  • Generated chunks: {len(optimized_chunks)}")
        print(f"  • Average chunk duration: {sum(c['duration'] for c in optimized_chunks) / len(optimized_chunks):.1f}s")
        print(f"  • Max chunk duration: {max(c['duration'] for c in optimized_chunks):.1f}s")
        
        return optimized_chunks
    
    def _finalize_chunk(self, chunk_data: Dict) -> Dict:
        """Finalize a chunk by combining text and calculating metadata."""
        combined_text = ' '.join(chunk_data['text_segments'])
        duration = chunk_data['end'] - chunk_data['start']
        
        return {
            'start': chunk_data['start'],
            'end': chunk_data['end'],
            'text': combined_text,
            'duration': duration,
            'segment_count': chunk_data['segment_count'],
            'word_count': len(combined_text.split()),
            'char_count': len(combined_text)
        }
    
    def _optimize_chunk_boundaries(self, chunks: List[Dict], original_segments: List[Dict]) -> List[Dict]:
        """
        Optimize chunk boundaries to avoid cutting sentences mid-way.
        Look for natural breaks like sentence endings.
        """
        if len(chunks) <= 1:
            return chunks
        
        optimized = []
        
        for i, chunk in enumerate(chunks):
            # For all chunks except the last one, try to find better boundary
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                
                # Look for sentence-ending patterns near the boundary
                boundary_time = chunk['end']
                
                # Find segments near the boundary
                boundary_segments = [
                    seg for seg in original_segments
                    if abs(float(seg['end']) - boundary_time) <= self.config.sentence_break_buffer
                ]
                
                # Look for segments ending with sentence terminators
                for seg in boundary_segments:
                    text = str(seg['text']).strip()
                    if text.endswith(('.', '!', '?', '।', '।।')):  # Include Hindi sentence endings
                        # This is a good place to break
                        new_boundary = float(seg['end'])
                        
                        # Only adjust if it doesn't make chunks too unbalanced
                        chunk_duration = new_boundary - chunk['start']
                        if chunk_duration >= self.config.min_chunk_duration:
                            chunk['end'] = new_boundary
                            chunk['duration'] = chunk_duration
                            
                            # Recalculate text for this chunk
                            chunk_segments = [
                                s for s in original_segments
                                if chunk['start'] <= float(s['start']) < chunk['end']
                            ]
                            chunk['text'] = ' '.join(str(s['text']).strip() for s in chunk_segments)
                            chunk['segment_count'] = len(chunk_segments)
                            chunk['word_count'] = len(chunk['text'].split())
                            chunk['char_count'] = len(chunk['text'])
                            break
            
            optimized.append(chunk)
        
        return optimized
    
    def save_chunked_transcript(self, chunks: List[Dict], output_file: str = "chunked_transcript.json") -> bool:
        """Save chunked transcript to JSON file."""
        try:
            # Add metadata
            metadata = {
                'total_chunks': len(chunks),
                'total_duration': sum(c['duration'] for c in chunks),
                'average_chunk_duration': sum(c['duration'] for c in chunks) / len(chunks) if chunks else 0,
                'max_chunk_duration': max(c['duration'] for c in chunks) if chunks else 0,
                'min_chunk_duration': min(c['duration'] for c in chunks) if chunks else 0,
                'total_segments': sum(c['segment_count'] for c in chunks),
                'chunking_config': {
                    'max_duration': self.config.max_duration,
                    'use_model_chunking': self.config.use_model_chunking,
                    'min_chunk_duration': self.config.min_chunk_duration
                }
            }
            
            output_data = {
                'metadata': metadata,
                'chunks': chunks
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved chunked transcript to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save chunked transcript: {str(e)}")
            return False
    
    def load_chunked_transcript(self, input_file: str = "chunked_transcript.json") -> Optional[List[Dict]]:
        """Load chunked transcript from JSON file."""
        try:
            if not os.path.exists(input_file):
                return None
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both old and new format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'chunks' in data:
                return data['chunks']
            else:
                return None
                
        except Exception as e:
            print(f"❌ Failed to load chunked transcript: {str(e)}")
            return None
    
    def analyze_chunking_efficiency(self, original_segments: List[Dict], chunks: List[Dict]) -> Dict:
        """Analyze the efficiency of chunking for TTS performance."""
        if not original_segments or not chunks:
            return {}
        
        original_count = len(original_segments)
        chunk_count = len(chunks)
        reduction_ratio = (original_count - chunk_count) / original_count
        
        # Calculate average segment vs chunk durations
        avg_segment_duration = sum(float(s['end']) - float(s['start']) for s in original_segments) / original_count
        avg_chunk_duration = sum(c['duration'] for c in chunks) / chunk_count
        
        # Estimate TTS API call reduction
        api_call_reduction = reduction_ratio
        
        analysis = {
            'original_segments': original_count,
            'generated_chunks': chunk_count,
            'reduction_ratio': reduction_ratio,
            'api_call_reduction_percent': api_call_reduction * 100,
            'average_segment_duration': avg_segment_duration,
            'average_chunk_duration': avg_chunk_duration,
            'duration_increase_factor': avg_chunk_duration / avg_segment_duration,
            'estimated_tts_time_savings': f"{api_call_reduction * 100:.1f}% fewer API calls",
            'chunk_size_distribution': {
                'small_chunks_5s': len([c for c in chunks if c['duration'] < 5]),
                'medium_chunks_5_15s': len([c for c in chunks if 5 <= c['duration'] < 15]),
                'large_chunks_15_30s': len([c for c in chunks if 15 <= c['duration'] < 30]),
                'very_large_chunks_30s+': len([c for c in chunks if c['duration'] >= 30])
            }
        }
        
        return analysis

def test_transcript_chunker():
    """Test the transcript chunker with sample data."""
    print("🧪 Testing Transcript Chunker")
    print("=" * 50)
    
    # Sample ASR segments (simulating short segments from Parakeet)
    sample_segments = [
        {"start": 0.0, "end": 2.5, "text": "Hello everyone, welcome to our channel."},
        {"start": 2.5, "end": 5.0, "text": "Today we're going to talk about AI."},
        {"start": 5.0, "end": 8.2, "text": "Artificial intelligence is changing the world."},
        {"start": 8.2, "end": 11.5, "text": "It's being used in many different industries."},
        {"start": 11.5, "end": 14.8, "text": "From healthcare to entertainment."},
        {"start": 14.8, "end": 18.0, "text": "The possibilities are endless."},
        {"start": 18.0, "end": 21.3, "text": "But we need to be careful about how we use it."},
        {"start": 21.3, "end": 24.5, "text": "Ethics and responsibility are important."},
        {"start": 24.5, "end": 27.8, "text": "We should always consider the impact."},
        {"start": 27.8, "end": 31.0, "text": "On society and individuals."},
        {"start": 31.0, "end": 34.2, "text": "Thank you for watching."},
        {"start": 34.2, "end": 36.5, "text": "Please subscribe and like this video."}
    ]
    
    try:
        # Test with different chunk durations
        for max_duration in [15, 30, 45]:
            print(f"\n📊 Testing with max duration: {max_duration}s")
            
            config = ChunkConfig(max_duration=max_duration)
            chunker = TranscriptChunker(config)
            
            chunks = chunker.chunk_transcript_by_time(sample_segments, max_duration)
            
            # Analyze efficiency
            analysis = chunker.analyze_chunking_efficiency(sample_segments, chunks)
            
            print(f"  • Chunks generated: {analysis['generated_chunks']}")
            print(f"  • API call reduction: {analysis['api_call_reduction_percent']:.1f}%")
            print(f"  • Avg chunk duration: {analysis['average_chunk_duration']:.1f}s")
            
            # Show first few chunks
            for i, chunk in enumerate(chunks[:3]):
                print(f"  • Chunk {i+1}: {chunk['start']:.1f}s-{chunk['end']:.1f}s ({chunk['duration']:.1f}s)")
                print(f"    Text: {chunk['text'][:60]}...")
        
        # Test saving and loading
        print(f"\n💾 Testing save/load functionality...")
        config = ChunkConfig(max_duration=30)
        chunker = TranscriptChunker(config)
        chunks = chunker.chunk_transcript_by_time(sample_segments)
        
        # Save
        success = chunker.save_chunked_transcript(chunks, "test_chunked_transcript.json")
        if success:
            print("✅ Save successful")
            
            # Load
            loaded_chunks = chunker.load_chunked_transcript("test_chunked_transcript.json")
            if loaded_chunks and len(loaded_chunks) == len(chunks):
                print("✅ Load successful")
                
                # Clean up
                os.unlink("test_chunked_transcript.json")
                return True
            else:
                print("❌ Load failed")
                return False
        else:
            print("❌ Save failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_transcript_chunker()
    print(f"\n{'✅ Transcript chunker test passed!' if success else '❌ Transcript chunker test failed!'}")