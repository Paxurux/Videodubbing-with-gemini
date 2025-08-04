#!/usr/bin/env python3
"""
Simple Edge TTS Service - Basic implementation that works without complex dependencies.
"""

import asyncio
import os
import json
import tempfile
from typing import List, Dict, Optional, Callable
from datetime import datetime

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    print("✅ Edge TTS library available")
except ImportError as e:
    EDGE_TTS_AVAILABLE = False
    print(f"⚠️ Edge TTS not available: {str(e)}")

class SimpleEdgeTTS:
    """
    Simple Edge TTS service that generates audio files without complex processing.
    """
    
    def __init__(self, voice_name: str = "hi-IN-MadhurNeural"):
        """Initialize Simple Edge TTS service."""
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("Edge TTS not available")
        
        self.voice_name = voice_name
        
        # Create output directories
        os.makedirs("simple_edge_output", exist_ok=True)
        
        print(f"🎙️ Simple Edge TTS initialized with voice: {voice_name}")
    
    async def generate_audio_async(self, text: str, output_file: str) -> bool:
        """Generate audio using Edge TTS."""
        try:
            print(f"🎤 Generating: {text[:50]}...")
            
            communicate = edge_tts.Communicate(text, self.voice_name)
            await communicate.save(output_file)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ Generated: {output_file} ({os.path.getsize(output_file)} bytes)")
                return True
            else:
                print(f"❌ Failed to generate: {output_file}")
                return False
                
        except Exception as e:
            print(f"❌ Generation error: {str(e)}")
            return False
    
    def generate_audio(self, text: str, output_file: str) -> bool:
        """Generate audio (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.generate_audio_async(text, output_file))
        finally:
            loop.close()
    
    def parse_time(self, timestr) -> float:
        """Parse time string to seconds."""
        try:
            if isinstance(timestr, (int, float)):
                return float(timestr)
            
            if isinstance(timestr, str) and ":" in timestr:
                if timestr.count(':') == 2:
                    dt = datetime.strptime(timestr, "%H:%M:%S.%f")
                    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
                elif timestr.count(':') == 1:
                    parts = timestr.split(':')
                    return int(parts[0]) * 60 + float(parts[1])
            
            return float(timestr)
        except:
            return 0.0
    
    def process_subtitle_json(self, subtitle_data: List[Dict], progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        Process subtitle JSON and generate individual audio files.
        
        Args:
            subtitle_data: List of subtitle dictionaries
            progress_callback: Optional progress callback
            
        Returns:
            Directory containing generated audio files
        """
        print(f"🎬 Processing {len(subtitle_data)} subtitles with Simple Edge TTS")
        
        if progress_callback:
            progress_callback(0.1, "Starting Simple Edge TTS processing...")
        
        generated_files = []
        
        for i, segment in enumerate(subtitle_data):
            if progress_callback:
                progress = 0.1 + (0.8 * (i + 1) / len(subtitle_data))
                progress_callback(progress, f"Processing segment {i + 1}/{len(subtitle_data)}")
            
            # Parse timing
            start_time = self.parse_time(segment.get("start", 0))
            end_time = self.parse_time(segment.get("end", 0))
            duration = end_time - start_time
            
            # Get text
            text = segment.get("text_translated", segment.get("text", "")).strip()
            
            if not text or duration <= 0:
                continue
            
            print(f"[{i}] 📝 {start_time:.2f}s-{end_time:.2f}s ({duration:.2f}s): {text[:50]}...")
            
            # Generate audio file
            output_file = f"simple_edge_output/segment_{i:03d}.mp3"
            
            if self.generate_audio(text, output_file):
                generated_files.append({
                    'file': output_file,
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                    'text': text,
                    'index': i
                })
                print(f"[{i}] ✅ Generated successfully")
            else:
                print(f"[{i}] ❌ Generation failed")
        
        if not generated_files:
            print("❌ No audio files generated")
            return None
        
        # Create a simple playlist/info file
        playlist_file = "simple_edge_output/playlist.json"
        with open(playlist_file, 'w', encoding='utf-8') as f:
            json.dump(generated_files, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated {len(generated_files)} audio files")
        print(f"📁 Files saved in: simple_edge_output/")
        print(f"📋 Playlist: {playlist_file}")
        
        if progress_callback:
            progress_callback(1.0, "Simple Edge TTS processing complete!")
        
        return "simple_edge_output"
    
    async def preview_voice_async(self, test_text: str = "Testing Edge TTS voice quality") -> Optional[str]:
        """Generate voice preview."""
        try:
            preview_file = f"simple_edge_output/voice_preview_{self.voice_name.replace(':', '_')}.mp3"
            
            if await self.generate_audio_async(test_text, preview_file):
                return preview_file
            else:
                return None
                
        except Exception as e:
            print(f"❌ Preview failed: {str(e)}")
            return None
    
    def preview_voice(self, test_text: str = "Testing Edge TTS voice quality") -> Optional[str]:
        """Generate voice preview (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.preview_voice_async(test_text))
        finally:
            loop.close()

# Test function
def test_simple_edge_tts():
    """Test Simple Edge TTS."""
    if not EDGE_TTS_AVAILABLE:
        print("❌ Edge TTS not available")
        return False
    
    print("🧪 Testing Simple Edge TTS")
    print("=" * 50)
    
    # Test data
    sample_subtitles = [
        {"start": 0.0, "end": 3.0, "text": "नमस्ते, यह Edge TTS का परीक्षण है।"},
        {"start": 3.0, "end": 6.0, "text": "यह बहुत अच्छी आवाज़ है।"}
    ]
    
    try:
        # Initialize service
        edge_service = SimpleEdgeTTS("hi-IN-MadhurNeural")
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"[{progress*100:5.1f}%] {message}")
        
        # Process subtitles
        output_dir = edge_service.process_subtitle_json(sample_subtitles, progress_callback)
        
        if output_dir and os.path.exists(output_dir):
            # List generated files
            files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
            total_size = sum(os.path.getsize(os.path.join(output_dir, f)) for f in files)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📁 Output directory: {output_dir}")
            print(f"🎵 Generated files: {len(files)}")
            print(f"📊 Total size: {total_size:,} bytes")
            
            # Test voice preview
            print(f"\n🎧 Testing voice preview...")
            preview_file = edge_service.preview_voice("यह आवाज़ का नमूना है।")
            if preview_file and os.path.exists(preview_file):
                preview_size = os.path.getsize(preview_file)
                print(f"✅ Preview generated: {preview_file} ({preview_size} bytes)")
            else:
                print(f"❌ Preview generation failed")
            
            return True
        else:
            print(f"\n❌ No output generated")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_edge_tts()
    
    if success:
        print("\n🎉 Simple Edge TTS is working!")
    else:
        print("\n❌ Simple Edge TTS test failed.")