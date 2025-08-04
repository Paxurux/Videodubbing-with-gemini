#!/usr/bin/env python3
"""
Test Kokoro Model Validation
Validates that the Kokoro model is properly downloaded and can generate real speech.
"""

import os
import numpy as np
from pathlib import Path

def validate_model_files():
    """Validate that all required Kokoro model files exist."""
    print("🔍 Validating Kokoro Model Files")
    print("=" * 40)
    
    model_dir = Path("Kokoro-82M")
    
    # Check if model directory exists
    if not model_dir.exists():
        print(f"❌ Model directory not found: {model_dir}")
        return False
    
    # Required files
    required_files = [
        "model.pt",
        "kokoro-v1_0.pth", 
        "config.json",
        "voice_metadata.json",
        "lang_metadata.json",
        "voices"
    ]
    
    print("📁 Checking required files:")
    all_exist = True
    
    for file in required_files:
        file_path = model_dir / file
        if file_path.exists():
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"✅ {file}: {size:,} bytes")
            else:
                print(f"✅ {file}: directory")
        else:
            print(f"❌ {file}: MISSING")
            all_exist = False
    
    # Check voice files
    voices_dir = model_dir / "voices"
    if voices_dir.exists():
        voice_files = list(voices_dir.glob("*.pt"))
        print(f"✅ Found {len(voice_files)} voice files in voices/")
        
        # Show first few voice files
        for voice_file in voice_files[:5]:
            size = voice_file.stat().st_size
            print(f"   • {voice_file.name}: {size:,} bytes")
        
        if len(voice_files) > 5:
            print(f"   ... and {len(voice_files) - 5} more")
    else:
        print("❌ voices/ directory not found")
        all_exist = False
    
    return all_exist

def test_kokoro_import():
    """Test if Kokoro can be imported and initialized."""
    print("\\n🧪 Testing Kokoro Import and Initialization")
    print("=" * 40)
    
    try:
        # Set environment variable
        os.environ["KOKORO_MODEL_PATH"] = os.path.abspath("Kokoro-82M")
        print(f"🌍 KOKORO_MODEL_PATH = {os.environ['KOKORO_MODEL_PATH']}")
        
        # Try to import Kokoro
        from kokoro import KPipeline
        print("✅ Kokoro import successful")
        
        # Try to initialize pipeline
        print("🔧 Initializing KPipeline...")
        pipeline = KPipeline(lang_code="a")  # American English
        print("✅ KPipeline initialized successfully")
        
        return pipeline
        
    except ImportError as e:
        print(f"❌ Kokoro import failed: {str(e)}")
        print("💡 Make sure Kokoro is installed: pip install kokoro")
        return None
    except Exception as e:
        print(f"❌ KPipeline initialization failed: {str(e)}")
        return None

def test_kokoro_generation(pipeline):
    """Test actual Kokoro TTS generation."""
    print("\\n🎤 Testing Kokoro TTS Generation")
    print("=" * 40)
    
    if not pipeline:
        print("❌ No pipeline available for testing")
        return False
    
    try:
        # Test text
        test_text = "Hello, this is a test of Kokoro TTS generation."
        voice = "af_heart"  # American English female
        
        print(f"📝 Text: '{test_text}'")
        print(f"🎵 Voice: {voice}")
        
        # Generate audio
        print("🔄 Generating audio...")
        output = pipeline(test_text, voice=voice)
        
        # Process output
        audio_segments = list(output)
        print(f"📊 Generated {len(audio_segments)} audio segments")
        
        if not audio_segments:
            print("❌ No audio segments generated")
            return False
        
        # Analyze first segment
        for i, (_, _, audio) in enumerate(audio_segments):
            print(f"\\n🔍 Segment {i} analysis:")
            
            if hasattr(audio, 'shape'):
                print(f"   Shape: {audio.shape}")
                print(f"   Type: {type(audio)}")
                print(f"   Min: {np.min(audio):.6f}")
                print(f"   Max: {np.max(audio):.6f}")
                print(f"   Mean: {np.mean(audio):.6f}")
                print(f"   Std: {np.std(audio):.6f}")
                
                # Check if audio is silent or flat
                if np.abs(audio).mean() < 0.001:
                    print("⚠️ Audio appears to be silent!")
                    return False
                elif np.std(audio) < 0.001:
                    print("⚠️ Audio appears to be flat (constant tone)!")
                    return False
                else:
                    print("✅ Audio has proper variation")
                
                # Save test audio
                import soundfile as sf
                test_file = f"kokoro_test_segment_{i}.wav"
                
                # Ensure audio is in correct format
                audio_normalized = np.clip(audio, -1.0, 1.0).astype(np.float32)
                sf.write(test_file, audio_normalized, 24000)
                
                file_size = os.path.getsize(test_file)
                print(f"✅ Saved: {test_file} ({file_size:,} bytes)")
                
                # Only process first segment for testing
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Kokoro generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_voice_variations():
    """Test different voices to ensure they produce different outputs."""
    print("\\n🎭 Testing Voice Variations")
    print("=" * 40)
    
    try:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code="a")
        
        test_text = "This is a voice variation test."
        voices = ["af_heart", "af_bella", "am_adam"]
        
        results = {}
        
        for voice in voices:
            try:
                print(f"🎵 Testing voice: {voice}")
                output = pipeline(test_text, voice=voice)
                
                for i, (_, _, audio) in enumerate(output):
                    audio_mean = np.mean(np.abs(audio))
                    audio_std = np.std(audio)
                    results[voice] = (audio_mean, audio_std)
                    print(f"   Mean: {audio_mean:.6f}, Std: {audio_std:.6f}")
                    break
                    
            except Exception as e:
                print(f"❌ Voice {voice} failed: {str(e)}")
                results[voice] = None
        
        # Check if voices produce different outputs
        valid_results = {k: v for k, v in results.items() if v is not None}
        
        if len(valid_results) < 2:
            print("⚠️ Not enough valid voice results to compare")
            return False
        
        # Compare results
        values = list(valid_results.values())
        if len(set(values)) == 1:
            print("⚠️ All voices produce identical output (possible issue)")
            return False
        else:
            print("✅ Voices produce different outputs")
            return True
            
    except Exception as e:
        print(f"❌ Voice variation test failed: {str(e)}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Kokoro Model Validation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Model Files Validation", validate_model_files),
        ("Kokoro Import Test", test_kokoro_import),
    ]
    
    results = {}
    pipeline = None
    
    # Run basic tests
    for test_name, test_func in tests:
        print(f"\\n🧪 Running: {test_name}")
        try:
            result = test_func()
            if test_name == "Kokoro Import Test":
                pipeline = result
                results[test_name] = pipeline is not None
            else:
                results[test_name] = result
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results[test_name] = False
    
    # Run generation tests if pipeline is available
    if pipeline:
        print(f"\\n🧪 Running: Kokoro Generation Test")
        try:
            results["Kokoro Generation Test"] = test_kokoro_generation(pipeline)
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results["Kokoro Generation Test"] = False
        
        print(f"\\n🧪 Running: Voice Variations Test")
        try:
            results["Voice Variations Test"] = test_voice_variations()
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results["Voice Variations Test"] = False
    
    # Summary
    print(f"\\n" + "=" * 50)
    print("📊 Validation Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Kokoro model is properly set up and generating real speech!")
        return True
    else:
        print("⚠️ Some issues found with Kokoro model setup")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\\n✅ Kokoro Model Validation PASSED!")
        exit(0)
    else:
        print("\\n❌ Kokoro Model Validation FAILED!")
        exit(1)