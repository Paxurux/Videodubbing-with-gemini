#!/usr/bin/env python3
"""
Installation validation script for Video Dubbing Pipeline
"""
import sys
import importlib
import subprocess

def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: OK")
        return True
    except ImportError as e:
        print(f"❌ {description}: FAILED - {str(e)}")
        return False

def test_command(command, description):
    """Test if a command is available"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ {description}: OK")
            return True
        else:
            print(f"❌ {description}: FAILED - {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}: FAILED - {str(e)}")
        return False

def main():
    print("🔍 Video Dubbing Pipeline - Installation Validation")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Core Python modules
    tests = [
        ("gradio", "Gradio Web Interface"),
        ("torch", "PyTorch Deep Learning"),
        ("pandas", "Data Processing"),
        ("numpy", "Numerical Computing"),
        ("soundfile", "Audio File I/O"),
        ("scipy", "Scientific Computing"),
        ("nemo.collections.asr", "NeMo ASR Toolkit"),
        ("google.generativeai", "Google Generative AI"),
        ("requests", "HTTP Requests"),
        ("edge_tts", "Edge TTS"),
        ("json", "JSON Processing"),
        ("pathlib", "Path Handling"),
        ("tempfile", "Temporary Files"),
        ("subprocess", "Process Management"),
    ]
    
    print("\n📦 Python Dependencies:")
    for module, desc in tests:
        if test_import(module, desc):
            success_count += 1
        total_tests += 1
    
    # Project modules
    print("\n🔧 Project Modules:")
    project_tests = [
        ("real_gemini_service", "Gemini Translation Service"),
        ("final_working_tts", "TTS Generation Service"),
        ("simple_edge_tts", "Edge TTS Integration"),
    ]
    
    for module, desc in project_tests:
        if test_import(module, desc):
            success_count += 1
        total_tests += 1
    
    # System commands
    print("\n💻 System Commands:")
    command_tests = [
        ("ffmpeg -version", "FFmpeg Video Processing"),
        ("python --version", "Python Interpreter"),
    ]
    
    for command, desc in command_tests:
        if test_command(command, desc):
            success_count += 1
        total_tests += 1
    
    # GPU and CUDA check
    print("\n🎮 GPU Support:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA GPU: Available ({torch.cuda.get_device_name(0)})")
            print(f"✅ CUDA Version: {torch.version.cuda}")
            success_count += 2
        else:
            print("⚠️ CUDA GPU: Not available (CPU mode will be used)")
            success_count += 1
        total_tests += 2
    except:
        print("❌ GPU Check: Failed")
        total_tests += 2
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Validation Summary: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Installation is complete and ready.")
        return 0
    elif success_count >= total_tests * 0.8:
        print("⚠️ Most tests passed. Some optional features may not work.")
        return 0
    else:
        print("❌ Multiple tests failed. Please check installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())