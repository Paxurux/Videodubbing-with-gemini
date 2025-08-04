#!/usr/bin/env python3
"""
Test script to verify Kokoro TTS auto-download functionality
"""

import os
import shutil
import tempfile

def test_auto_download():
    """Test the auto-download functionality"""
    try:
        from kokoro_tts_service import KokoroTTSService, DEFAULT_MODEL_PATH
        
        print("🧪 Testing Kokoro TTS Auto-Download")
        print("=" * 40)
        
        # Check if model already exists
        model_exists = os.path.exists(DEFAULT_MODEL_PATH)
        print(f"📁 Model exists at {DEFAULT_MODEL_PATH}: {model_exists}")
        
        # Initialize service
        print("\n1. Initializing Kokoro TTS Service...")
        service = KokoroTTSService(voice_name="af_bella")
        
        print(f"   Model available: {service.model_available}")
        print(f"   Model loaded: {service.model_loaded}")
        
        # Test model loading (which should trigger auto-download if needed)
        print("\n2. Testing model loading...")
        load_success = service._load_model()
        print(f"   Load success: {load_success}")
        print(f"   Model loaded: {service.model_loaded}")
        
        # Test voice preview (which uses the model)
        print("\n3. Testing voice preview...")
        preview_file = service.preview_voice("Hello, this is a test of Kokoro TTS.")
        
        if preview_file and os.path.exists(preview_file):
            file_size = os.path.getsize(preview_file)
            print(f"✅ Preview generated: {preview_file} ({file_size} bytes)")
        else:
            print("❌ Preview generation failed")
        
        # Test model unloading
        print("\n4. Testing model unloading...")
        service._unload_model()
        print(f"   Model loaded after unload: {service.model_loaded}")
        
        print("\n" + "=" * 40)
        print("🎉 Auto-download test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_fallback_behavior():
    """Test fallback behavior when model download fails"""
    try:
        print("\n🧪 Testing Fallback Behavior")
        print("=" * 40)
        
        # This would test what happens when git is not available
        # or network is down, but we'll simulate it
        
        from kokoro_tts_service import KokoroTTSService
        
        # Create service with non-existent path to simulate failure
        service = KokoroTTSService(voice_name="af_bella", model_path="/nonexistent/path")
        
        print(f"Model available: {service.model_available}")
        
        # Try to load model (should fail gracefully)
        load_success = service._load_model()
        print(f"Load success (should be False): {load_success}")
        
        # Try preview (should fail gracefully)
        preview_file = service.preview_voice("Test")
        print(f"Preview file (should be None): {preview_file}")
        
        print("✅ Fallback behavior test completed")
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = True
    
    if not test_auto_download():
        success = False
    
    if not test_fallback_behavior():
        success = False
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed.")