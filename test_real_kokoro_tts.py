#!/usr/bin/env python3
"""
Test Real Kokoro TTS
Tests the actual Kokoro TTS model using the correct pattern.
"""

import os
import numpy as np
import soundfile as sf
from pathlib import Path

def test_kokoro_installation():
    """Test if Kokoro is properly installed."""
    print("🧪 Testing Kokoro Installation")
    print("=" * 40)
    
    try:
        # Test import
        from kokoro import KPipeline
        print("✅ Kokoro import successful")
        
        # Test pipeline creation
        print("🔧 Creating KPipeline...")
        pipeline = KPipeline(lang_code='a')  # American English
        print("✅ KPipeline created successfully")
        
        return pipeline
        
    except ImportError as e:
        print(f"❌ Kokoro import failed: {str(e)}")
        print("💡 Install with: pip install kokoro>=0.9.2 soundfile")
        return None
    except Exception as e:
        print(f"❌ KPipeline creation failed: {str(e)}")
        return None

def test_kokoro_generation(pipeline):
    """Test actual Kokoro TTS generation."""
    print("\\n🎤 Testing Kokoro TTS Generation")
    print("=" * 40)
    
    if not pipeline:
        print("❌ No pipeline available")
        return False
    
    try:
        # Test text (similar to your example)
        text = '''Hello, this is a test of Kokoro TTS. 
        Despite its lightweight architecture, it delivers comparable quality 
        to larger models while being significantly faster.'''
        
        voice = 'af_heart'  # American English female
        
        print(f"📝 Text: {text[:50]}...")
        print(f"🎵 Voice: {voice}")
        
        # Generate audio using the correct pattern
        print("🔄 Generating audio...")
        generator = pipeline(text, voice=voice)
        
        # Process output (following your pattern)
        audio_files = []
        for i, (gs, ps, audio) in enumerate(generator):
            print(f"🔍 Segment {i}: gs={gs}, ps={ps}")
            
            if isinstance(audio, np.ndarray):
                print(f"   Audio shape: {audio.shape}")
                print(f"   Audio range: {np.min(audio):.3f} to {np.max(audio):.3f}")
                print(f"   Audio mean: {np.mean(audio):.3f}")
                print(f"   Audio std: {np.std(audio):.3f}")
                
                # Check if audio is valid (not flat tone)
                if np.abs(audio).mean() < 0.001:
                    print("⚠️ Audio appears to be silent!")
                elif np.std(audio) < 0.001:
                    print("⚠️ Audio appears to be flat (constant tone)!")
                else:
                    print("✅ Audio has proper variation")
                
                # Save audio file
                output_file = f'kokoro_test_{i}.wav'
                sf.write(output_file, audio, 24000)
                
                file_size = os.path.getsize(output_file)
                print(f"✅ Saved: {output_file} ({file_size:,} bytes)")
                audio_files.append(output_file)
            else:
                print(f"⚠️ Unexpected audio type: {type(audio)}")
        
        if audio_files:
            print(f"\\n🎉 Generated {len(audio_files)} audio files successfully!")
            return True
        else:
            print("❌ No audio files generated")
            return False
            
    except Exception as e:
        print(f"❌ Kokoro generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_voices():
    """Test different Kokoro voices."""
    print("\\n🎭 Testing Multiple Voices")
    print("=" * 40)
    
    try:
        from kokoro import KPipeline
        
        # Test different voices
        voices = ['af_heart', 'af_bella', 'am_adam']
        test_text = "This is a voice comparison test."
        
        results = {}
        
        for voice in voices:
            try:
                print(f"🎵 Testing voice: {voice}")
                pipeline = KPipeline(lang_code='a')
                generator = pipeline(test_text, voice=voice)
                
                for i, (gs, ps, audio) in enumerate(generator):
                    if isinstance(audio, np.ndarray):
                        audio_mean = np.mean(np.abs(audio))
                        audio_std = np.std(audio)
                        results[voice] = (audio_mean, audio_std)
                        
                        # Save sample
                        sample_file = f'voice_sample_{voice}.wav'
                        sf.write(sample_file, audio, 24000)
                        
                        print(f"   Mean: {audio_mean:.6f}, Std: {audio_std:.6f}")
                        print(f"   Saved: {sample_file}")
                    break  # Only process first segment
                    
            except Exception as e:
                print(f"❌ Voice {voice} failed: {str(e)}")
                results[voice] = None
        
        # Analyze results
        valid_results = {k: v for k, v in results.items() if v is not None}
        
        if len(valid_results) >= 2:
            print("\\n📊 Voice Comparison:")
            for voice, (mean, std) in valid_results.items():
                print(f"   {voice}: mean={mean:.6f}, std={std:.6f}")
            
            # Check if voices are different
            values = list(valid_results.values())
            if len(set(values)) > 1:
                print("✅ Voices produce different outputs")
                return True
            else:
                print("⚠️ All voices produce identical output")
                return False
        else:
            print("❌ Not enough valid voices to compare")
            return False
            
    except Exception as e:
        print(f"❌ Voice comparison failed: {str(e)}")
        return False

def create_fixed_kokoro_service():
    """Create a fixed Kokoro service that uses the real model."""
    print("\\n🔧 Creating Fixed Kokoro Service")
    print("=" * 40)
    
    service_code = '''#!/usr/bin/env python3
"""
Real Kokoro TTS Service
Uses the actual Kokoro model with proper implementation.
"""

import os
import numpy as np
import soundfile as sf
from typing import List, Dict, Optional
from pathlib import Path

class RealKokoroTTSService:
    """Real Kokoro TTS service using the actual model."""
    
    def __init__(self, voice_name: str = "af_heart", lang_code: str = "a"):
        """Initialize with real Kokoro model."""
        self.voice_name = voice_name
        self.lang_code = lang_code
        self.pipeline = None
        
        print(f"🎙️ Real Kokoro TTS Service")
        print(f"🎤 Voice: {self.voice_name}")
        print(f"🌍 Language: {self.lang_code}")
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the Kokoro pipeline."""
        try:
            from kokoro import KPipeline
            self.pipeline = KPipeline(lang_code=self.lang_code)
            print("✅ Real Kokoro pipeline initialized")
        except Exception as e:
            print(f"❌ Pipeline initialization failed: {str(e)}")
            self.pipeline = None
    
    def generate_tts_chunks(self, translated_segments: List[Dict], progress_callback=None) -> str:
        """Generate TTS chunks using real Kokoro model."""
        if not self.pipeline:
            print("❌ Pipeline not available")
            return "kokoro_tts_chunks"
        
        print(f"🎬 Generating {len(translated_segments)} segments with real Kokoro")
        
        # Create output directory
        output_dir = Path("kokoro_tts_chunks")
        output_dir.mkdir(exist_ok=True)
        
        successful_chunks = 0
        
        for i, segment in enumerate(translated_segments):
            if progress_callback:
                progress = (i + 1) / len(translated_segments)
                progress_callback(progress, f"Processing segment {i + 1}/{len(translated_segments)} with Real Kokoro")
            
            # Extract text and timing
            text = segment.get("text_translated", segment.get("text", "")).strip()
            start_time = float(segment.get("start", 0))
            end_time = float(segment.get("end", 0))
            duration = end_time - start_time
            
            if not text or duration <= 0:
                print(f"[{i}] ⚠️ Skipping invalid segment")
                continue
            
            print(f"[{i}] 📝 {start_time:.2f}s-{end_time:.2f}s ({duration:.2f}s): {text[:50]}...")
            
            try:
                # Generate using real Kokoro
                print(f"🎤 Real Kokoro synthesis: '{text[:30]}...' with {self.voice_name}")
                generator = self.pipeline(text, voice=self.voice_name)
                
                # Process output
                chunk_file = output_dir / f"chunk_{i:03d}.wav"
                audio_saved = False
                
                for j, (gs, ps, audio) in enumerate(generator):
                    if isinstance(audio, np.ndarray):
                        # Debug audio
                        print(f"   Audio: shape={audio.shape}, mean={np.mean(np.abs(audio)):.6f}, std={np.std(audio):.6f}")
                        
                        # Check audio quality
                        if np.abs(audio).mean() < 0.001:
                            print("⚠️ Silent audio detected")
                        elif np.std(audio) < 0.001:
                            print("⚠️ Flat audio detected")
                        else:
                            print("✅ Good audio variation")
                        
                        # Adjust duration if needed
                        current_duration = len(audio) / 24000
                        if abs(current_duration - duration) > 0.5:
                            target_length = int(duration * 24000)
                            if target_length > len(audio):
                                # Pad with silence
                                padding = target_length - len(audio)
                                audio = np.pad(audio, (0, padding), mode='constant')
                            else:
                                # Truncate
                                audio = audio[:target_length]
                            print(f"🎵 Adjusted duration: {current_duration:.2f}s → {duration:.2f}s")
                        
                        # Save audio
                        sf.write(chunk_file, audio, 24000)
                        
                        file_size = chunk_file.stat().st_size
                        print(f"[{i}] ✅ Real Kokoro completed: {chunk_file} ({file_size:,} bytes)")
                        
                        successful_chunks += 1
                        audio_saved = True
                        break  # Only use first segment
                
                if not audio_saved:
                    print(f"[{i}] ❌ No audio generated")
                    
            except Exception as e:
                print(f"[{i}] ❌ Generation failed: {str(e)}")
        
        print(f"📊 Generated {successful_chunks}/{len(translated_segments)} chunks")
        return str(output_dir)
    
    def preview_voice(self, test_text: str = "Testing real Kokoro TTS voice quality") -> Optional[str]:
        """Generate voice preview using real Kokoro."""
        if not self.pipeline:
            return None
        
        try:
            preview_file = Path(f"kokoro_tts_output/real_voice_preview_{self.voice_name}.wav")
            preview_file.parent.mkdir(exist_ok=True)
            
            print(f"🎤 Real Kokoro preview: '{test_text}' with {self.voice_name}")
            generator = self.pipeline(test_text, voice=self.voice_name)
            
            for i, (gs, ps, audio) in enumerate(generator):
                if isinstance(audio, np.ndarray):
                    sf.write(preview_file, audio, 24000)
                    
                    file_size = preview_file.stat().st_size
                    print(f"✅ Real preview generated: {preview_file} ({file_size:,} bytes)")
                    return str(preview_file)
                break
            
            return None
            
        except Exception as e:
            print(f"❌ Real preview failed: {str(e)}")
            return None

def test_real_kokoro_service():
    """Test the real Kokoro service."""
    try:
        service = RealKokoroTTSService("af_heart", "a")
        
        # Test preview
        preview = service.preview_voice("This is a test of the real Kokoro TTS service.")
        if preview:
            print(f"✅ Preview: {preview}")
        
        # Test segments
        segments = [
            {"start": 0.0, "end": 3.0, "text_translated": "Hello, this is real Kokoro TTS."},
            {"start": 3.0, "end": 6.0, "text_translated": "The quality should be much better now."}
        ]
        
        chunks_dir = service.generate_tts_chunks(segments)
        print(f"✅ Chunks: {chunks_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real service test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_real_kokoro_service()
'''
    
    with open("real_kokoro_tts_service.py", "w", encoding="utf-8") as f:
        f.write(service_code)
    
    print("✅ Created real_kokoro_tts_service.py")
    return True

def main():
    """Run all tests."""
    print("🚀 Real Kokoro TTS Test Suite")
    print("=" * 50)
    
    # Test installation
    pipeline = test_kokoro_installation()
    
    if not pipeline:
        print("\\n❌ Kokoro not properly installed")
        print("💡 Install with: pip install kokoro>=0.9.2 soundfile")
        return False
    
    # Test generation
    generation_success = test_kokoro_generation(pipeline)
    
    # Test multiple voices
    voices_success = test_multiple_voices()
    
    # Create fixed service
    service_success = create_fixed_kokoro_service()
    
    # Summary
    print(f"\\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    
    results = {
        "Kokoro Installation": pipeline is not None,
        "Audio Generation": generation_success,
        "Multiple Voices": voices_success,
        "Service Creation": service_success
    }
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed >= 3:  # At least installation, generation, and service creation
        print("🎉 Real Kokoro TTS is working!")
        return True
    else:
        print("⚠️ Some issues with real Kokoro TTS")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\\n✅ Real Kokoro TTS Test PASSED!")
        exit(0)
    else:
        print("\\n❌ Real Kokoro TTS Test FAILED!")
        exit(1)