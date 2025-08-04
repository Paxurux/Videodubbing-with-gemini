#!/usr/bin/env python3
"""
System Validation Script for Parakeet TDT Enhanced
Validates all dependencies and system requirements are properly installed.
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires Python 3.8+)")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - MISSING")
        return False

def check_system_tool(tool_name, version_flag="--version"):
    """Check if a system tool is available."""
    try:
        result = subprocess.run([tool_name, version_flag], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
            print(f"✅ {tool_name} - {version_line}")
            return True
        else:
            print(f"❌ {tool_name} - NOT FOUND")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print(f"❌ {tool_name} - NOT FOUND")
        return False

def check_gpu_support():
    """Check GPU and CUDA support."""
    print("\n🖥️ Checking GPU support...")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            print(f"✅ GPU: {gpu_name} (CUDA {torch.version.cuda})")
            print(f"✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            return True
        else:
            print("⚠️ GPU: CUDA not available (CPU mode only)")
            return False
    except ImportError:
        print("❌ GPU: Cannot check (PyTorch not installed)")
        return False

def check_directories():
    """Check if necessary directories exist."""
    print("\n📁 Checking directories...")
    directories = [
        "cache",
        "cache/GRADIO_TEMP_DIR", 
        "cache/HF_HOME",
        "cache/TORCH_HOME",
        "tts_chunks"
    ]
    
    all_exist = True
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ {directory}")
        else:
            print(f"❌ {directory} - MISSING")
            all_exist = False
    
    return all_exist

def check_local_modules():
    """Check local Python modules."""
    print("\n🔧 Checking local modules...")
    modules = [
        "transcript_chunker",
        "chunked_audio_stitcher", 
        "api_key_manager",
        "real_gemini_service",
        "simple_edge_tts",
        "edge_tts_voice_parser",
        "kokoro_tts_service",
        "pipeline_controller",
        "state_manager",
        "audio_utils"
    ]
    
    missing_modules = []
    for module in modules:
        if check_package(module):
            continue
        else:
            missing_modules.append(module)
    
    return len(missing_modules) == 0

def main():
    """Main validation function."""
    print("🎯 Parakeet TDT Enhanced - System Validation")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check Python version
    if not check_python_version():
        all_checks_passed = False
    
    # Check core ML packages
    print("\n🤖 Checking core ML packages...")
    core_packages = [
        ("gradio", "gradio"),
        ("torch", "torch"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("soundfile", "soundfile"),
        ("scipy", "scipy"),
        ("nemo-toolkit", "nemo")
    ]
    
    for package_name, import_name in core_packages:
        if not check_package(package_name, import_name):
            all_checks_passed = False
    
    # Check dubbing pipeline packages
    print("\n🎬 Checking dubbing pipeline packages...")
    dubbing_packages = [
        ("google-generativeai", "google.generativeai"),
        ("tiktoken", "tiktoken"),
        ("requests", "requests"),
        ("pydub", "pydub"),
        ("moviepy", "moviepy"),
        ("edge-tts", "edge_tts"),
        ("onnxruntime", "onnxruntime")
    ]
    
    for package_name, import_name in dubbing_packages:
        if not check_package(package_name, import_name):
            all_checks_passed = False
    
    # Check system tools
    print("\n🛠️ Checking system tools...")
    system_tools = [
        ("ffmpeg", "-version"),
        ("ffprobe", "-version"),
        ("git", "--version")
    ]
    
    for tool_name, version_flag in system_tools:
        if not check_system_tool(tool_name, version_flag):
            if tool_name in ["ffmpeg", "ffprobe"]:
                print(f"   ⚠️ {tool_name} is required for audio/video processing")
                all_checks_passed = False
    
    # Check GPU support
    check_gpu_support()
    
    # Check directories
    if not check_directories():
        print("   ℹ️ Missing directories will be created automatically")
    
    # Check local modules
    if not check_local_modules():
        all_checks_passed = False
    
    # Final result
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ System is ready for Parakeet TDT Enhanced")
        print("🚀 You can now start the application")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("⚠️ Please install missing dependencies")
        print("💡 Run the install script or check the documentation")
        return 1

if __name__ == "__main__":
    sys.exit(main())