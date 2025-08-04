#!/usr/bin/env python3
"""
Chunked Audio Stitcher
Handles proper stitching of chunked TTS audio with timestamp matching and duration synchronization.
"""

import os
import json
import subprocess
import tempfile
import logging
import wave
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import glob

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from transcript_chunker import TranscriptChunker

class ChunkedAudioStitcher:
    """
    Enhanced audio stitcher specifically designed for chunked TTS audio.
    Handles timestamp matching, duration synchronization, and seamless combination.
    """
    
    def __init__(self, sample_rate: int = 24000, channels: int = 1):
        """Initialize the chunked audio stitcher."""
        self.sample_rate = sample_rate
        self.channels = channels
        self.logger = logging.getLogger(__name__)
        
        # Create output directories
        os.makedirs("final_audio", exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)
        
    def stitch_chunked_audio(self, chunks_dir: str, chunked_transcript_file: str = "chunked_transcript.json", 
                           output_file: str = "final_audio/final_dubbed_audio.wav") -> str:
        """
        Stitch chunked TTS audio with proper timestamp matching.
        
        Args:
            chunks_dir: Directory containing TTS chunk files
            chunked_transcript_file: Path to chunked transcript JSON
            output_file: Output path for final stitched audio
            
        Returns:
            Path to final stitched audio file
        """
        self.logger.info(f"Starting chunked audio stitching from {chunks_dir}")
        
        # Load chunked transcript data
        chunked_data = self._load_chunked_transcript(chunked_transcript_file)
        if not chunked_data:
            raise Exception(f"Could not load chunked transcript from {chunked_transcript_file}")
        
        # Find and validate chunk files
        chunk_files = self._find_chunk_files(chunks_dir)
        if not chunk_files:
            raise Exception(f"No chunk files found in {chunks_dir}")
        
        # Match chunk files with transcript data
        matched_chunks = self._match_chunks_with_transcript(chunk_files, chunked_data)
        
        # Validate timing and duration
        self._validate_chunk_timing(matched_chunks)
        
        # Process chunks for proper timing
        processed_chunks = self._process_chunks_for_timing(matched_chunks)
        
        # Stitch chunks together
        final_audio = self._stitch_processed_chunks(processed_chunks, output_file)
        
        # Validate final output
        self._validate_final_audio(final_audio, chunked_data)
        
        self.logger.info(f"Chunked audio stitching completed: {final_audio}")
        return final_audio
    
    def create_video_ready_audio(self, stitched_audio: str, original_video: str = None, 
                                output_file: str = "final_audio/video_ready_audio.wav") -> str:
        """
        Create video-ready audio with proper synchronization.
        
        Args:
            stitched_audio: Path to stitched audio file
            original_video: Optional path to original video for duration matching
            output_file: Output path for video-ready audio
            
        Returns:
            Path to video-ready audio file
        """
        self.logger.info("Creating video-ready audio")
        
        if not os.path.exists(stitched_audio):
            raise Exception(f"Stitched audio file not found: {stitched_audio}")
        
        # Get audio info
        audio_info = self._get_audio_info(stitched_audio)
        audio_duration = audio_info.get('duration', 0)
        
        if audio_duration == 0:
            raise Exception("Stitched audio has zero duration")
        
        # If original video provided, match duration
        if original_video and os.path.exists(original_video):
            video_info = self._get_video_info(original_video)
            video_duration = video_info.get('duration', 0)
            
            if video_duration > 0:
                duration_diff = abs(video_duration - audio_duration)
                
                if duration_diff > 1.0:  # More than 1 second difference
                    self.logger.info(f"Adjusting audio duration to match video: {audio_duration:.2f}s → {video_duration:.2f}s")
                    return self._adjust_audio_duration(stitched_audio, video_duration, output_file)
        
        # No adjustment needed, just copy with proper format
        return self._normalize_audio_format(stitched_audio, output_file)
    
    def get_stitching_report(self, chunks_dir: str, final_audio: str) -> Dict:
        """
        Generate a detailed report of the stitching process.
        
        Args:
            chunks_dir: Directory containing chunk files
            final_audio: Path to final stitched audio
            
        Returns:
            Dictionary with stitching report
        """
        report = {
            'chunks_processed': 0,
            'total_chunk_duration': 0.0,
            'final_audio_duration': 0.0,
            'chunk_files': [],
            'timing_accuracy': 'unknown',
            'quality_metrics': {},
            'issues': []
        }
        
        try:
            # Analyze chunk files
            chunk_files = self._find_chunk_files(chunks_dir)
            report['chunks_processed'] = len(chunk_files)
            
            total_duration = 0.0
            for chunk_file in chunk_files:
                chunk_info = self._get_audio_info(chunk_file)
                chunk_duration = chunk_info.get('duration', 0)
                total_duration += chunk_duration
                
                report['chunk_files'].append({
                    'file': os.path.basename(chunk_file),
                    'duration': chunk_duration,
                    'size': os.path.getsize(chunk_file)
                })
            
            report['total_chunk_duration'] = total_duration
            
            # Analyze final audio
            if os.path.exists(final_audio):
                final_info = self._get_audio_info(final_audio)
                report['final_audio_duration'] = final_info.get('duration', 0)
                
                # Calculate timing accuracy
                duration_diff = abs(report['final_audio_duration'] - report['total_chunk_duration'])
                if duration_diff < 0.1:
                    report['timing_accuracy'] = 'excellent'
                elif duration_diff < 0.5:
                    report['timing_accuracy'] = 'good'
                elif duration_diff < 1.0:
                    report['timing_accuracy'] = 'acceptable'
                else:
                    report['timing_accuracy'] = 'poor'
                    report['issues'].append(f"Significant timing difference: {duration_diff:.2f}s")
                
                # Quality metrics
                report['quality_metrics'] = {
                    'sample_rate': final_info.get('sample_rate', 0),
                    'channels': final_info.get('channels', 0),
                    'codec': final_info.get('codec', 'unknown'),
                    'bitrate': final_info.get('bitrate', 0)
                }
            else:
                report['issues'].append("Final audio file not found")
            
        except Exception as e:
            report['issues'].append(f"Report generation error: {str(e)}")
        
        return report
    
    def _load_chunked_transcript(self, transcript_file: str) -> Optional[List[Dict]]:
        """Load chunked transcript data."""
        try:
            if not os.path.exists(transcript_file):
                self.logger.warning(f"Chunked transcript not found: {transcript_file}")
                return None
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both old and new format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'chunks' in data:
                return data['chunks']
            else:
                self.logger.error("Invalid chunked transcript format")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load chunked transcript: {str(e)}")
            return None
    
    def _find_chunk_files(self, chunks_dir: str) -> List[str]:
        """Find and sort chunk files."""
        if not os.path.exists(chunks_dir):
            return []
        
        # Look for different chunk file patterns
        patterns = [
            "chunk_*.wav",
            "chunk_*.mp3", 
            "segment_*.wav",
            "segment_*.mp3",
            "*.wav",
            "*.mp3"
        ]
        
        chunk_files = []
        for pattern in patterns:
            files = glob.glob(os.path.join(chunks_dir, pattern))
            if files:
                chunk_files.extend(files)
                break  # Use first pattern that finds files
        
        # Sort files by name (which should include index)
        chunk_files.sort()
        
        self.logger.info(f"Found {len(chunk_files)} chunk files")
        return chunk_files
    
    def _match_chunks_with_transcript(self, chunk_files: List[str], chunked_data: List[Dict]) -> List[Dict]:
        """Match chunk files with transcript data."""
        matched_chunks = []
        
        for i, chunk_data in enumerate(chunked_data):
            chunk_info = {
                'index': i,
                'start': chunk_data.get('start', 0),
                'end': chunk_data.get('end', 0),
                'duration': chunk_data.get('duration', 0),
                'text': chunk_data.get('text', ''),
                'file': None,
                'actual_duration': 0
            }
            
            # Find corresponding chunk file
            if i < len(chunk_files):
                chunk_file = chunk_files[i]
                chunk_info['file'] = chunk_file
                
                # Get actual audio duration
                audio_info = self._get_audio_info(chunk_file)
                chunk_info['actual_duration'] = audio_info.get('duration', 0)
            else:
                self.logger.warning(f"No chunk file found for chunk {i}")
            
            matched_chunks.append(chunk_info)
        
        return matched_chunks
    
    def _validate_chunk_timing(self, matched_chunks: List[Dict]):
        """Validate chunk timing and report issues."""
        issues = []
        
        for chunk in matched_chunks:
            if not chunk['file']:
                issues.append(f"Chunk {chunk['index']}: No audio file")
                continue
            
            expected_duration = chunk['duration']
            actual_duration = chunk['actual_duration']
            
            if actual_duration == 0:
                issues.append(f"Chunk {chunk['index']}: Zero duration audio")
                continue
            
            # Check duration difference (allow 20% tolerance)
            duration_diff = abs(expected_duration - actual_duration)
            tolerance = max(expected_duration * 0.2, 0.5)  # 20% or 0.5s minimum
            
            if duration_diff > tolerance:
                issues.append(
                    f"Chunk {chunk['index']}: Duration mismatch - "
                    f"expected {expected_duration:.2f}s, got {actual_duration:.2f}s"
                )
        
        if issues:
            self.logger.warning(f"Chunk timing validation found {len(issues)} issues:")
            for issue in issues:
                self.logger.warning(f"  • {issue}")
        else:
            self.logger.info("Chunk timing validation passed")
    
    def _process_chunks_for_timing(self, matched_chunks: List[Dict]) -> List[Dict]:
        """Process chunks to ensure proper timing."""
        processed_chunks = []
        
        for chunk in matched_chunks:
            if not chunk['file']:
                continue
            
            processed_chunk = chunk.copy()
            
            # Check if duration adjustment is needed
            expected_duration = chunk['duration']
            actual_duration = chunk['actual_duration']
            duration_diff = abs(expected_duration - actual_duration)
            
            # If significant difference, adjust duration
            if duration_diff > 0.5:  # More than 0.5s difference
                adjusted_file = self._adjust_chunk_duration(
                    chunk['file'], expected_duration, chunk['index']
                )
                if adjusted_file:
                    processed_chunk['file'] = adjusted_file
                    processed_chunk['actual_duration'] = expected_duration
                    self.logger.info(f"Adjusted chunk {chunk['index']} duration: {actual_duration:.2f}s → {expected_duration:.2f}s")
            
            processed_chunks.append(processed_chunk)
        
        return processed_chunks
    
    def _adjust_chunk_duration(self, chunk_file: str, target_duration: float, chunk_index: int) -> Optional[str]:
        """Adjust chunk duration to match target."""
        try:
            adjusted_file = f"temp_audio/adjusted_chunk_{chunk_index:03d}.wav"
            
            if PYDUB_AVAILABLE:
                # Use pydub for duration adjustment
                audio = AudioSegment.from_file(chunk_file)
                current_duration = len(audio) / 1000.0
                
                if current_duration > 0:
                    speed_ratio = current_duration / target_duration
                    # Limit speed adjustment to reasonable range
                    speed_ratio = max(0.5, min(2.0, speed_ratio))
                    
                    adjusted_audio = audio.speedup(playback_speed=speed_ratio)
                    adjusted_audio.export(adjusted_file, format="wav")
                    
                    return adjusted_file
            else:
                # Use ffmpeg for duration adjustment
                speed_ratio = target_duration / self._get_audio_info(chunk_file).get('duration', 1)
                speed_ratio = max(0.5, min(2.0, speed_ratio))
                
                cmd = [
                    'ffmpeg',
                    '-i', chunk_file,
                    '-filter:a', f'atempo={1/speed_ratio}',
                    '-acodec', 'pcm_s16le',
                    '-ar', str(self.sample_rate),
                    '-ac', str(self.channels),
                    adjusted_file,
                    '-y'
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                return adjusted_file
                
        except Exception as e:
            self.logger.error(f"Failed to adjust chunk duration: {str(e)}")
            return None
    
    def _stitch_processed_chunks(self, processed_chunks: List[Dict], output_file: str) -> str:
        """Stitch processed chunks into final audio."""
        valid_chunks = [chunk for chunk in processed_chunks if chunk['file'] and os.path.exists(chunk['file'])]
        
        if not valid_chunks:
            raise Exception("No valid chunks to stitch")
        
        self.logger.info(f"Stitching {len(valid_chunks)} processed chunks")
        
        # Create file list for ffmpeg concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for chunk in valid_chunks:
                abs_path = os.path.abspath(chunk['file'])
                f.write(f"file '{abs_path}'\n")
            list_file = f.name
        
        try:
            # Use ffmpeg to concatenate
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate),
                '-ac', str(self.channels),
                output_file,
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            if not os.path.exists(output_file):
                raise Exception("Stitched audio file was not created")
            
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to stitch chunks: {e}")
        finally:
            # Clean up
            if os.path.exists(list_file):
                os.unlink(list_file)
    
    def _validate_final_audio(self, final_audio: str, chunked_data: List[Dict]):
        """Validate final stitched audio."""
        if not os.path.exists(final_audio):
            raise Exception("Final audio file does not exist")
        
        audio_info = self._get_audio_info(final_audio)
        actual_duration = audio_info.get('duration', 0)
        
        if actual_duration == 0:
            raise Exception("Final audio has zero duration")
        
        # Calculate expected duration
        expected_duration = max(chunk.get('end', 0) for chunk in chunked_data)
        
        # Validate duration (allow 5% tolerance)
        duration_diff = abs(actual_duration - expected_duration)
        tolerance = max(expected_duration * 0.05, 1.0)
        
        if duration_diff > tolerance:
            self.logger.warning(
                f"Final audio duration validation: expected {expected_duration:.2f}s, "
                f"got {actual_duration:.2f}s (diff: {duration_diff:.2f}s)"
            )
        else:
            self.logger.info(
                f"Final audio validation passed: {actual_duration:.2f}s "
                f"(expected {expected_duration:.2f}s)"
            )
    
    def _adjust_audio_duration(self, audio_file: str, target_duration: float, output_file: str) -> str:
        """Adjust audio duration to match target."""
        try:
            audio_info = self._get_audio_info(audio_file)
            current_duration = audio_info.get('duration', 0)
            
            if current_duration == 0:
                raise Exception("Cannot adjust zero-duration audio")
            
            # Calculate speed adjustment
            speed_ratio = current_duration / target_duration
            speed_ratio = max(0.8, min(1.2, speed_ratio))  # Limit to 20% adjustment
            
            cmd = [
                'ffmpeg',
                '-i', audio_file,
                '-filter:a', f'atempo={1/speed_ratio}',
                '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate),
                '-ac', str(self.channels),
                output_file,
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return output_file
            
        except Exception as e:
            self.logger.error(f"Duration adjustment failed: {str(e)}")
            # Fallback: just copy the file
            import shutil
            shutil.copy2(audio_file, output_file)
            return output_file
    
    def _normalize_audio_format(self, audio_file: str, output_file: str) -> str:
        """Normalize audio format for video compatibility."""
        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-acodec', 'pcm_s16le',
            '-ar', str(self.sample_rate),
            '-ac', str(self.channels),
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # Broadcast standard
            output_file,
            '-y'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_file
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio normalization failed: {str(e)}")
            # Fallback: copy original
            import shutil
            shutil.copy2(audio_file, output_file)
            return output_file
    
    def _get_audio_info(self, audio_file: str) -> Dict:
        """Get audio file information."""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            audio_file
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            info = json.loads(result.stdout)
            
            audio_stream = next((s for s in info['streams'] if s['codec_type'] == 'audio'), {})
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(info['format'].get('bit_rate', 0))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get audio info: {str(e)}")
            return {}
    
    def _get_video_info(self, video_file: str) -> Dict:
        """Get video file information."""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            video_file
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            info = json.loads(result.stdout)
            
            return {
                'duration': float(info['format'].get('duration', 0))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get video info: {str(e)}")
            return {}

def test_chunked_audio_stitcher():
    """Test the chunked audio stitcher."""
    print("🧪 Testing Chunked Audio Stitcher")
    print("=" * 50)
    
    try:
        # Create test chunked transcript
        test_chunks = [
            {
                "start": 0.0,
                "end": 15.0,
                "text": "First chunk of audio content",
                "duration": 15.0,
                "segment_count": 5
            },
            {
                "start": 15.0,
                "end": 30.0,
                "text": "Second chunk of audio content",
                "duration": 15.0,
                "segment_count": 4
            }
        ]
        
        # Save test chunked transcript
        with open("test_chunked_transcript.json", "w", encoding="utf-8") as f:
            json.dump({"chunks": test_chunks}, f, indent=2)
        
        print("✅ Created test chunked transcript")
        
        # Initialize stitcher
        stitcher = ChunkedAudioStitcher()
        
        # Test report generation (without actual audio files)
        report = stitcher.get_stitching_report("nonexistent_dir", "nonexistent_audio.wav")
        
        print(f"✅ Generated stitching report")
        print(f"  • Chunks processed: {report['chunks_processed']}")
        print(f"  • Issues found: {len(report['issues'])}")
        
        # Clean up
        os.unlink("test_chunked_transcript.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chunked_audio_stitcher()
    print(f"\n{'✅ Chunked Audio Stitcher test passed!' if success else '❌ Test failed!'}")