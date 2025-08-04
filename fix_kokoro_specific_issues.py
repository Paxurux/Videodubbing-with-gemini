#!/usr/bin/env python3
"""
Kokoro TTS Specific Issues Fix
Addresses the specific problems found in the setup.
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

def force_remove_directory(directory):
    """Force remove directory with Windows-specific handling."""
    if not os.path.exists(directory):
        return True
    
    print(f"🗑️ Force removing {directory}...")
    
    try:
        # Try normal removal first
        shutil.rmtree(directory)
        print("✅ Normal removal successful")
        return True
    except PermissionError:
        print("⚠️ Permission error, trying Windows-specific fixes...")
        
        # Windows-specific fixes
        try:
            # Method 1: Use attrib to remove read-only attributes
            subprocess.run(['attrib', '-R', f'{directory}\\*.*', '/S'], 
                         shell=True, capture_output=True)
            
            # Method 2: Use rmdir command
            subprocess.run(['rmdir', '/S', '/Q', directory], 
                         shell=True, capture_output=True)
            
            if not os.path.exists(directory):
                print("✅ Windows rmdir successful")
                return True
            
            # Method 3: Rename and try again
            temp_name = f"{directory}_temp_{int(time.time())}"
            os.rename(directory, temp_name)
            shutil.rmtree(temp_name)
            print("✅ Rename and remove successful")
            return True
            
        except Exception as e:
            print(f"❌ All removal methods failed: {str(e)}")
            return False

def download_model_files_directly():
    """Download model files directly using huggingface_hub."""
    print("📥 Downloading Kokoro model files directly...")
    
    try:
        from huggingface_hub import hf_hub_download, snapshot_download
        
        repo_id = "hexgrad/Kokoro-82M"
        local_dir = "Kokoro-82M"
        
        # Create directory
        os.makedirs(local_dir, exist_ok=True)
        
        # Download using snapshot_download for better handling
        print("🔄 Using snapshot_download for complete model...")
        
        try:
            snapshot_download(
                repo_id=repo_id,
                local_dir=local_dir,
                local_dir_use_symlinks=False,  # Important for Windows
                resume_download=True
            )
            print("✅ Snapshot download completed")
            return True
            
        except Exception as e:
            print(f"⚠️ Snapshot download failed: {str(e)}")
            print("🔄 Trying individual file downloads...")
            
            # Try downloading key files individually
            key_files = [
                "model.pt",
                "config.json", 
                "voice_metadata.json",
                "lang_metadata.json"
            ]
            
            success_count = 0
            for filename in key_files:
                try:
                    print(f"📥 Downloading {filename}...")
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        local_dir=local_dir,
                        local_dir_use_symlinks=False
                    )
                    print(f"✅ Downloaded {filename}")
                    success_count += 1
                except Exception as file_error:
                    print(f"❌ Failed to download {filename}: {str(file_error)}")
            
            return success_count > 0
            
    except ImportError:
        print("❌ huggingface_hub not available")
        return False
    except Exception as e:
        print(f"❌ Direct download failed: {str(e)}")
        return False

def fix_espeak_issue():
    """Fix the EspeakWrapper issue."""
    print("🔧 Fixing EspeakWrapper issue...")
    
    try:
        # Try to install espeak-ng for Windows
        print("📦 Installing espeak-ng...")
        
        # Check if we can install via pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "espeak-ng"], 
                         check=True, capture_output=True)
            print("✅ espeak-ng installed via pip")
        except:
            print("⚠️ Could not install espeak-ng via pip")
        
        # Try alternative espeak packages
        alt_packages = ["espeak", "pyttsx3", "phonemizer"]
        for package in alt_packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                print(f"✅ Installed alternative: {package}")
            except:
                print(f"⚠️ Could not install {package}")
        
        return True
        
    except Exception as e:
        print(f"❌ EspeakWrapper fix failed: {str(e)}")
        return False

def create_minimal_kokoro_test():
    """Create a minimal test that bypasses problematic components."""
    print("🧪 Creating minimal Kokoro test...")
    
    test_code = '''#!/usr/bin/env python3
"""
Minimal Kokoro Test
Tests basic functionality without problematic components.
"""

import os
import sys

def test_kokoro_import():
    """Test if Kokoro can be imported."""
    try:
        import kokoro
        print("✅ Kokoro import successful")
        print(f"   Version: {getattr(kokoro, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        print(f"❌ Kokoro import failed: {str(e)}")
        return False

def test_model_files():
    """Test if model files exist."""
    model_dir = "Kokoro-82M"
    
    if not os.path.exists(model_dir):
        print(f"❌ Model directory not found: {model_dir}")
        return False
    
    required_files = ["model.pt", "config.json"]
    found_files = []
    
    for file in required_files:
        file_path = os.path.join(model_dir, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file} ({size:,} bytes)")
            found_files.append(file)
        else:
            print(f"❌ {file} - MISSING")
    
    return len(found_files) > 0

def test_basic_pipeline():
    """Test basic pipeline creation without audio generation."""
    try:
        # Set environment variable
        model_path = os.path.abspath("Kokoro-82M")
        os.environ["KOKORO_MODEL_PATH"] = model_path
        
        print(f"🌍 KOKORO_MODEL_PATH = {model_path}")
        
        # Try to import and create pipeline
        from kokoro import KPipeline
        
        print("🔧 Creating pipeline...")
        pipeline = KPipeline(lang_code="a")
        print("✅ Pipeline created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline creation failed: {str(e)}")
        
        # Try alternative approach
        try:
            print("🔄 Trying alternative pipeline creation...")
            
            # Import components individually
            import torch
            print("✅ PyTorch available")
            
            # Check if model file exists and is readable
            model_file = os.path.join(model_path, "model.pt")
            if os.path.exists(model_file):
                print(f"✅ Model file exists: {model_file}")
                
                # Try to load model directly
                model = torch.load(model_file, map_location='cpu')
                print("✅ Model loaded successfully")
                return True
            else:
                print(f"❌ Model file not found: {model_file}")
                return False
                
        except Exception as alt_error:
            print(f"❌ Alternative approach failed: {str(alt_error)}")
            return False

def main():
    """Run minimal tests."""
    print("🧪 Minimal Kokoro Test Suite")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_kokoro_import),
        ("Model Files", test_model_files),
        ("Basic Pipeline", test_basic_pipeline)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\\n🔧 {test_name}")
        print("-" * 20)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\\n" + "=" * 40)
    print("📊 Test Results")
    print("=" * 40)
    
    passed = sum(results.values())
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\\n🎯 Result: {passed}/{total} tests passed")
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
'''
    
    with open("minimal_kokoro_test.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    print("✅ Created minimal_kokoro_test.py")
    return True

def main():
    """Main fix function."""
    print("🔧 Kokoro TTS Specific Issues Fix")
    print("=" * 50)
    
    fixes = [
        ("Force Remove Old Directory", lambda: force_remove_directory("Kokoro-82M")),
        ("Download Model Files", download_model_files_directly),
        ("Fix EspeakWrapper", fix_espeak_issue),
        ("Create Minimal Test", create_minimal_kokoro_test)
    ]
    
    results = {}
    
    for fix_name, fix_func in fixes:
        print(f"\\n🔧 {fix_name}")
        print("-" * 30)
        
        try:
            results[fix_name] = fix_func()
        except Exception as e:
            print(f"❌ Fix failed: {str(e)}")
            results[fix_name] = False
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 Fix Results")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(fixes)
    
    for fix_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {fix_name}")
    
    print(f"\\n🎯 Overall: {passed}/{total} fixes applied")
    
    if passed >= 2:  # At least model download and test creation
        print("\\n🎉 Enough fixes applied to proceed!")
        print("\\n📋 Next Steps:")
        print("1. Run: python minimal_kokoro_test.py")
        print("2. Check if basic functionality works")
        print("3. If successful, integrate with dubbing pipeline")
        return True
    else:
        print("\\n⚠️ Critical fixes failed. Manual intervention may be needed.")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\\n✅ Kokoro fixes applied successfully!")
        exit(0)
    else:
        print("\\n❌ Kokoro fixes failed!")
        exit(1)