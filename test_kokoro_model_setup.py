#!/usr/bin/env python3
"""
Test script to verify Kokoro model setup and auto-download
"""

import os
import sys

def test_kokoro_model_setup():
    """Test Kokoro model setup and auto-download functionality"""
    print("🧪 Testing Kokoro Model Setup")
    print("=" * 40)
    
    try:
        from kokoro_tts_service import KokoroTTSService, DEFAULT_MODEL_PATH
        
        # Check if model directory exists
        model_exists = os.path.exists(DEFAULT_MODEL_PATH)
        print(f"📁 Model directory exists: {model_exists}")
        print(f"📍 Model path: {DEFAULT_MODEL_PATH}")
        
        if model_exists:
            # Check for required files
            required_files = ["kokoro-v0_19.onnx", "voices"]
            for file in required_files:
                file_path = os.path.join(DEFAULT_MODEL_PATH, file)
                exists = os.path.exists(file_path)
                print(f"📄 {file}: {'✅' if exists else '❌'}")
        
        # Test service initialization
        print("\n🔧 Testing service initialization...")
        service = KokoroTTSService(voice_name="af_bella")
        print(f"✅ Service initialized")
        print(f"   Voice: {service.voice_name}")
        print(f"   Model available: {service.model_available}")
        
        # Test auto-download if model not available
        if not service.model_available:
            print("\n📥 Testing auto-download...")
            success = service._ensure_model_available()
            print(f"   Auto-download success: {success}")
            
            if success:
                print("✅ Model is now available after auto-download")
            else:
                print("❌ Auto-download failed")
                print("💡 Manual setup required:")
                print("   1. Ensure Git and Git LFS are installed")
                print("   2. Run: git clone https://huggingface.co/hexgrad/Kokoro-82M kokoro_models/Kokoro-82M")
        
        # Test model loading
        print("\n🧠 Testing model loading...")
        load_success = service._load_model()
        print(f"   Model load success: {load_success}")
        
        if load_success:
            print("✅ Model loaded successfully")
            
            # Test voice preview
            print("\n🎤 Testing voice preview...")
            preview_file = service.preview_voice("Testing Kokoro TTS setup")
            
            if preview_file and os.path.exists(preview_file):
                file_size = os.path.getsize(preview_file)
                print(f"✅ Preview generated: {preview_file} ({file_size} bytes)")
            else:
                print("❌ Preview generation failed")
        
        print("\n" + "=" * 40)
        print("🎉 Kokoro model setup test completed!")
        
        return service.model_available
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def manual_setup_instructions():
    """Provide manual setup instructions"""
    print("\n📋 Manual Setup Instructions")
    print("=" * 40)
    print("If auto-download fails, follow these steps:")
    print()
    print("1. Install Git LFS:")
    print("   git lfs install")
    print()
    print("2. Create model directory:")
    print("   mkdir -p kokoro_models")
    print()
    print("3. Clone Kokoro model:")
    print("   cd kokoro_models")
    print("   git clone https://huggingface.co/hexgrad/Kokoro-82M")
    print()
    print("4. Verify files exist:")
    print("   ls kokoro_models/Kokoro-82M/")
    print("   # Should contain: kokoro-v0_19.onnx, voices, etc.")
    print()
    print("5. Test again:")
    print("   python test_kokoro_model_setup.py")

if __name__ == "__main__":
    success = test_kokoro_model_setup()
    
    if not success:
        manual_setup_instructions()
        sys.exit(1)
    else:
        print("✅ All tests passed! Kokoro TTS is ready to use.")
        sys.exit(0)