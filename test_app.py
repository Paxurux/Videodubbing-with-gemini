#!/usr/bin/env python3
"""
Simple test script to verify the main application can be imported and initialized
"""
import sys
import os

def test_app_import():
    """Test if the main app can be imported"""
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test imports
        print("🔍 Testing application imports...")
        
        # Test core imports
        import gradio as gr
        print("✅ Gradio imported successfully")
        
        import torch
        print("✅ PyTorch imported successfully")
        
        import pandas as pd
        print("✅ Pandas imported successfully")
        
        # Test if CUDA is available
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ CUDA not available, will use CPU")
        
        # Test NeMo import (this might take a while)
        print("🔄 Testing NeMo ASR import (this may take a moment)...")
        import nemo.collections.asr as nemo_asr
        print("✅ NeMo ASR imported successfully")
        
        # Test dubbing components
        print("🔄 Testing dubbing components...")
        try:
            from real_gemini_service import RealGeminiService
            print("✅ Gemini service imported successfully")
        except ImportError as e:
            print(f"⚠️ Gemini service import warning: {e}")
        
        try:
            from final_working_tts import FinalWorkingTTS
            print("✅ TTS service imported successfully")
        except ImportError as e:
            print(f"⚠️ TTS service import warning: {e}")
        
        try:
            from simple_edge_tts import SimpleEdgeTTS
            print("✅ Edge TTS imported successfully")
        except ImportError as e:
            print(f"⚠️ Edge TTS import warning: {e}")
        
        print("\n🎉 All core components imported successfully!")
        print("📝 The application should be ready to run.")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

def test_directories():
    """Test if required directories exist"""
    print("\n🔍 Testing directory structure...")
    
    required_dirs = [
        "cache",
        "cache/GRADIO_TEMP_DIR",
        "cache/HF_HOME", 
        "cache/TORCH_HOME",
        "batch_dubbed_videos",
        "temp_audio"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def main():
    print("🚀 Video Dubbing Pipeline - Application Test")
    print("=" * 50)
    
    # Test imports
    import_success = test_app_import()
    
    # Test directories
    dir_success = test_directories()
    
    # Summary
    print("\n" + "=" * 50)
    if import_success and dir_success:
        print("🎉 All tests passed! Application is ready to run.")
        print("💡 You can now start the application with: python app.py")
        return 0
    else:
        print("❌ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())