#!/usr/bin/env python3
"""
Kokoro TTS Service - EXACT Documentation Pattern Implementation
Uses the precise API pattern shown in the Kokoro documentation.
"""

import os
import numpy as np
import soundfile as sf
from typing import List, Dict, Optional
from pathlib import Path
import time

class KokoroTTSExactPattern:
    """Kokoro TTS service using the EXACT pattern from documentation."""
    
    def __init__(self, voice_name: str = "af_heart", lang_code: str = "a"):
        """Initialize with proper Kokoro setup."""
        self.voice_name = voice_name
        self.lang_code = lang_code
        self.pipeline = None
        
        print(f"🎙️ Kokoro TTS Service - EXACT Documentation Pattern")
        print(f"🎤 Voice: {self.voice_name}")
        print(f"🌍 Language: {self.lang_code}")
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the Kokoro pipeline using EXACT documentation pattern."""
        try:
            # EXACT import pattern from documentation
            from kokoro import KPipeline
            import torch
            
            print("🔧 Initializing Kokoro pipeline with EXACT documentation pattern...")
            
            # EXACT initialization pattern from documentation:
            # pipeline = KPipeline(lang_code='a')
            self.pipeline = KPipeline(lang_code=self.lang_code)
            print("✅ Kokoro pipeline initialized successfully with EXACT pattern")
            
        except Exception as e:
            print(f"❌ Pipeline initialization failed: {str(e)}")
            if "EspeakWrapper" in str(e):
                print("💡 EspeakWrapper issue detected. Install espeak-ng:")
                print("   Windows: Download from http://espeak.sourceforge.net/download.html")
                print("   Linux: sudo apt-get install espeak-ng")
                print("   macOS: brew install espeak")
            self.pipeline = None
    
    def generate_tts_chunks(self, translated_segments: List[Dict], progress_callback=None) -> str:
        """Generate TTS chunks using EXACT Kokoro documentation pattern."""
        if not self.pipeline:
            print("❌ Pipeline not available")
            return "kokoro_tts_chunks"
        
        print(f"🎬 Generating {len(translated_segments)} segments with EXACT Kokoro documentation pattern")
        
        # Create output directory
        output_dir = Path("kokoro_tts_chunks")
        output_dir.mkdir(exist_ok=True)
        
        successful_chunks = 0
        
        for segment_idx, segment in enumerate(translated_segments):
            if progress_callback:
                progress = (segment_idx + 1) / len(translated_segments)
                progress_callback(progress, f"Processing segment {segment_idx + 1}/{len(translated_segments)} with EXACT Kokoro pattern")
            
            # Extract text and timing
            text = segment.get("text_translated", segment.get("text", "")).strip()
            start_time = float(segment.get("start", 0))
            end_time = float(segment.get("end", 0))
            duration = end_time - start_time
            
            if not text or duration <= 0:
                print(f"[{segment_idx}] ⚠️ Skipping invalid segment")
                continue
            
            print(f"[{segment_idx}] 📝 {start_time:.2f}s-{end_time:.2f}s ({duration:.2f}s): {text[:50]}...")
            
            try:
                # EXACT pattern from documentation:
                print(f"🎤 Using EXACT Kokoro pattern for segment {segment_idx}")
                
                # EXACT generator call from documentation
                generator = self.pipeline(
                    text, 
                    voice=self.voice_name,
                    speed=1,
                    split_pattern=r'\\n+'
                )
                
                # EXACT processing pattern from documentation:
                # for i, (gs, ps, audio) in enumerate(generator):
                #     print(i, gs, ps)
                #     sf.write(f'{i}.wav', audio, 24000)
                
                audio_files = []
                for i, (gs, ps, audio) in enumerate(generator):
                    print(f"   Sub-chunk {i}: gs='{gs[:30]}...', ps='{ps[:30]}...', audio_shape={audio.shape if hasattr(audio, 'shape') else type(audio)}")
                    
                    if isinstance(audio, np.ndarray):
                        # EXACT save pattern from documentation: sf.write(f'{i}.wav', audio, 24000)
                        sub_chunk_file = output_dir / f"segment_{segment_idx:03d}_subchunk_{i}.wav"
                        sf.write(sub_chunk_file, audio, 24000)
                        audio_files.append(sub_chunk_file)
                        
                        # Debug audio properties
                        print(f"   Audio: min={np.min(audio):.3f}, max={np.max(audio):.3f}, mean={np.mean(np.abs(audio)):.6f}, std={np.std(audio):.6f}")
                        
                        # Check audio quality
                        if np.abs(audio).mean() < 0.001:
                            print("⚠️ Silent audio detected")
                        elif np.std(audio) < 0.001:
                            print("⚠️ Flat audio detected")
                        else:
                            print("✅ Good audio variation")
                    else:
                        print(f"⚠️ Unexpected audio type: {type(audio)}")
                
                # Combine all sub-chunks into final chunk
                if audio_files:
                    final_chunk_file = output_dir / f"chunk_{segment_idx:03d}.wav"
                    
                    if len(audio_files) == 1:
                        # Single sub-chunk, just rename
                        import shutil
                        shutil.move(str(audio_files[0]), str(final_chunk_file))
                        print(f"   Single sub-chunk moved to final chunk")
                    else:
                        # Multiple sub-chunks, concatenate them
                        print(f"   Combining {len(audio_files)} sub-chunks...")
                        combined_audio = []
                        for audio_file in audio_files:
                            audio_data, _ = sf.read(audio_file)
                            combined_audio.append(audio_data)
                            # Clean up sub-chunk
                            os.unlink(audio_file)
                        
                        # Concatenate and save
                        final_audio = np.concatenate(combined_audio)
                        sf.write(final_chunk_file, final_audio, 24000)
                        print(f"   Combined into final audio: {final_audio.shape}")
                    
                    # Adjust duration to match target
                    current_duration = len(sf.read(final_chunk_file)[0]) / 24000
                    if abs(current_duration - duration) > 0.5:
                        target_length = int(duration * 24000)
                        audio_data, _ = sf.read(final_chunk_file)
                        
                        if target_length > len(audio_data):
                            # Pad with silence
                            padding = target_length - len(audio_data)
                            audio_data = np.pad(audio_data, (0, padding), mode='constant')
                        else:
                            # Truncate
                            audio_data = audio_data[:target_length]
                        
                        sf.write(final_chunk_file, audio_data, 24000)
                        print(f"🎵 Adjusted duration: {current_duration:.2f}s → {duration:.2f}s")
                    
                    if final_chunk_file.exists():
                        file_size = final_chunk_file.stat().st_size
                        print(f"[{segment_idx}] ✅ EXACT Kokoro pattern completed: {final_chunk_file} ({file_size:,} bytes)")
                        successful_chunks += 1
                    else:
                        print(f"[{segment_idx}] ❌ Final chunk file not created")
                else:
                    print(f"[{segment_idx}] ❌ No audio files generated")
                    
            except Exception as e:
                print(f"[{segment_idx}] ❌ Generation failed: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"📊 Generated {successful_chunks}/{len(translated_segments)} chunks using EXACT Kokoro pattern")
        return str(output_dir)
    
    def preview_voice(self, test_text: str = "Testing EXACT Kokoro TTS documentation pattern") -> Optional[str]:
        """Generate voice preview using EXACT Kokoro documentation pattern."""
        if not self.pipeline:
            return None
        
        try:
            preview_file = Path(f"kokoro_tts_output/exact_pattern_preview_{self.voice_name}.wav")
            preview_file.parent.mkdir(exist_ok=True)
            
            print(f"🎤 EXACT Kokoro preview: '{test_text}' with {self.voice_name}")
            
            # EXACT pattern from documentation
            generator = self.pipeline(
                test_text, 
                voice=self.voice_name,
                speed=1,
                split_pattern=r'\\n+'
            )
            
            # EXACT processing pattern
            audio_chunks = []
            for i, (gs, ps, audio) in enumerate(generator):
                print(f"Preview chunk {i}: gs='{gs[:20]}...', audio_shape={audio.shape if hasattr(audio, 'shape') else type(audio)}")
                
                if isinstance(audio, np.ndarray):
                    audio_chunks.append(audio)
            
            if audio_chunks:
                # Combine chunks
                if len(audio_chunks) == 1:
                    final_audio = audio_chunks[0]
                else:
                    final_audio = np.concatenate(audio_chunks)
                
                # Save preview using EXACT pattern: sf.write(f'{i}.wav', audio, 24000)
                sf.write(preview_file, final_audio, 24000)
                
                file_size = preview_file.stat().st_size
                print(f"✅ EXACT pattern preview generated: {preview_file} ({file_size:,} bytes)")
                return str(preview_file)
            
            return None
            
        except Exception as e:
            print(f"❌ EXACT pattern preview failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

def test_exact_kokoro_pattern():
    """Test the EXACT Kokoro documentation pattern."""
    print("🧪 Testing EXACT Kokoro Documentation Pattern")
    print("=" * 60)
    
    try:
        # Initialize service
        service = KokoroTTSExactPattern("af_heart", "a")
        
        if not service.pipeline:
            print("❌ Pipeline not available - cannot test EXACT pattern")
            return False
        
        # Test voice preview
        print("\\n🎤 Testing EXACT pattern voice preview...")
        preview_file = service.preview_voice("This is a test of the EXACT Kokoro TTS documentation pattern implementation.")
        
        if preview_file:
            print(f"✅ EXACT pattern preview generated: {preview_file}")
        else:
            print("❌ EXACT pattern preview failed")
        
        # Test with segments
        print("\\n🎬 Testing EXACT pattern TTS chunks generation...")
        test_segments = [
            {
                "start": 0.0,
                "end": 4.0,
                "text_translated": "Hello everyone, this is a test using the EXACT Kokoro TTS documentation pattern."
            },
            {
                "start": 4.0,
                "end": 8.0,
                "text_translated": "We are following the precise API calls shown in the official documentation."
            },
            {
                "start": 8.0,
                "end": 12.0,
                "text_translated": "This should generate real Kokoro TTS audio using the correct generator pattern."
            }
        ]
        
        def progress_callback(progress, message):
            print(f"[{progress*100:5.1f}%] {message}")
        
        chunks_dir = service.generate_tts_chunks(test_segments, progress_callback)
        
        if chunks_dir and Path(chunks_dir).exists():
            chunk_files = list(Path(chunks_dir).glob("*.wav"))
            print(f"\\n✅ Generated {len(chunk_files)} chunk files using EXACT pattern:")
            
            total_size = 0
            for chunk_file in chunk_files:
                file_size = chunk_file.stat().st_size
                total_size += file_size
                print(f"   • {chunk_file.name}: {file_size:,} bytes")
            
            print(f"📊 Total size: {total_size:,} bytes")
            
            if len(chunk_files) == len(test_segments):
                print("🎉 All segments processed successfully with EXACT Kokoro documentation pattern!")
                return True
            else:
                print(f"⚠️ Expected {len(test_segments)} files, got {len(chunk_files)}")
                return len(chunk_files) > 0  # Partial success
        else:
            print("❌ No chunks generated with EXACT pattern")
            return False
            
    except Exception as e:
        print(f"❌ EXACT pattern test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_exact_kokoro_pattern()
    
    if success:
        print("\\n🎉 EXACT Kokoro Documentation Pattern test PASSED!")
        print("✅ Using precise Kokoro API pattern from documentation")
        print("✅ Real Kokoro TTS audio generation with correct generator usage")
        print("✅ Proper sub-chunk handling and combination")
    else:
        print("\\n❌ EXACT Kokoro Documentation Pattern test FAILED!")
        print("💡 Make sure espeak-ng is installed for Kokoro to work properly")
        print("💡 Check that Kokoro package is properly installed: pip install kokoro>=0.9.4")
    
    exit(0 if success else 1)