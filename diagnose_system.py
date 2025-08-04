#!/usr/bin/env python3
"""
System Diagnosis Script for Parakeet TDT Enhanced
Provides detailed system information and troubleshooting guidance.
"""

import sys
import os
import platform
import subprocess
import json
from pathlib import Path

def get_system_info():
    """Get basic system information."""
    print("💻 System Information")
    print("-" * 30)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print()

def check_environment_variables():
    """Check important environment variables."""
    print("🌍 Environment Variables")
    print("-" * 30)
    
    env_vars = [
        "HF_HOME",
        "TORCH_HOME", 
        "GRADIO_TEMP_DIR",
        "CUDA_VISIBLE_DEVICES",
        "PYTHONPATH"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"{var}: {value}")
    print()

def check_disk_space():
    """Check available disk space."""
    print("💾 Disk Space")
    print("-" * 30)
    
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)
        
        print(f"Total: {total_gb:.1f} GB")
        print(f"Used: {used_gb:.1f} GB")
        print(f"Free: {free_gb:.1f} GB")
        
        if free_gb < 5:
            print("⚠️ Warning: Low disk space (< 5 GB free)")
        elif free_gb < 2:
            print("❌ Critical: Very low disk space (< 2 GB free)")
        else:
            print("✅ Sufficient disk space available")
    except Exception as e:
        print(f"❌ Could not check disk space: {e}")
    print()

def check_model_files():
    """Check for model files and cache."""
    print("🤖 Model Files & Cache")
    print("-" * 30)
    
    # Check cache directories
    cache_dirs = [
        "cache/HF_HOME",
        "cache/TORCH_HOME",
        "cache/GRADIO_TEMP_DIR"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                size = sum(f.stat().st_size for f in Path(cache_dir).rglob('*') if f.is_file())
                size_mb = size / (1024**2)
                print(f"✅ {cache_dir}: {size_mb:.1f} MB")
            except Exception:
                print(f"✅ {cache_dir}: exists")
        else:
            print(f"❌ {cache_dir}: missing")
    
    # Check Kokoro model
    if os.path.exists("Kokoro-82M"):
        print("✅ Kokoro-82M: available")
    else:
        print("⚠️ Kokoro-82M: not found (optional)")
    
    print()

def check_gpu_details():
    """Check detailed GPU information."""
    print("🖥️ GPU Details")
    print("-" * 30)
    
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"cuDNN version: {torch.backends.cudnn.version()}")
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"GPU {i}: {props.name}")
                print(f"  Memory: {props.total_memory / 1024**3:.1f} GB")
                print(f"  Compute Capability: {props.major}.{props.minor}")
        else:
            print("Running in CPU mode")
    except ImportError:
        print("❌ PyTorch not available")
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
    print()

def check_network_connectivity():
    """Check network connectivity for API services."""
    print("🌐 Network Connectivity")
    print("-" * 30)
    
    test_urls = [
        ("Hugging Face", "https://huggingface.co"),
        ("Google AI", "https://ai.google.dev"),
        ("GitHub", "https://github.com")
    ]
    
    for name, url in test_urls:
        try:
            import requests
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: accessible")
            else:
                print(f"⚠️ {name}: status {response.status_code}")
        except ImportError:
            print(f"❌ Cannot test {name}: requests not available")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    print()

def check_file_permissions():
    """Check file permissions in working directory."""
    print("🔐 File Permissions")
    print("-" * 30)
    
    test_file = "permission_test.tmp"
    try:
        # Test write permission
        with open(test_file, 'w') as f:
            f.write("test")
        print("✅ Write permission: OK")
        
        # Test read permission
        with open(test_file, 'r') as f:
            content = f.read()
        print("✅ Read permission: OK")
        
        # Clean up
        os.remove(test_file)
        print("✅ Delete permission: OK")
        
    except Exception as e:
        print(f"❌ Permission error: {e}")
    print()

def generate_troubleshooting_report():
    """Generate troubleshooting recommendations."""
    print("🔧 Troubleshooting Recommendations")
    print("-" * 40)
    
    recommendations = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        recommendations.append("❌ Upgrade Python to 3.8 or higher")
    
    # Check critical packages
    critical_packages = ["torch", "gradio", "nemo"]
    for package in critical_packages:
        try:
            __import__(package)
        except ImportError:
            recommendations.append(f"❌ Install {package}: pip install {package}")
    
    # Check system tools
    for tool in ["ffmpeg", "ffprobe"]:
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            recommendations.append(f"❌ Install {tool} system tool")
    
    # Check disk space
    try:
        import shutil
        _, _, free = shutil.disk_usage(".")
        if free < 2 * 1024**3:  # Less than 2GB
            recommendations.append("❌ Free up disk space (need at least 2GB)")
    except:
        pass
    
    if recommendations:
        print("Issues found:")
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("✅ No critical issues detected")
    
    print("\n💡 General Tips:")
    print("  • Ensure stable internet connection for model downloads")
    print("  • Use GPU for better performance if available")
    print("  • Keep at least 5GB free disk space for models and cache")
    print("  • Update dependencies regularly with update.js")
    print()

def main():
    """Main diagnosis function."""
    print("🔍 Parakeet TDT Enhanced - System Diagnosis")
    print("=" * 50)
    print()
    
    get_system_info()
    check_environment_variables()
    check_disk_space()
    check_model_files()
    check_gpu_details()
    check_network_connectivity()
    check_file_permissions()
    generate_troubleshooting_report()
    
    print("=" * 50)
    print("📋 Diagnosis complete!")
    print("💾 Save this output for troubleshooting support")

if __name__ == "__main__":
    main()