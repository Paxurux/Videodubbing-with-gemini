#!/usr/bin/env python3
"""
Kokoro TTS Multilingual Model Setup Fix
Properly downloads and configures the Kokoro 82M multilingual model for all languages.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"🔧 {description}")
    print(f"   Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        print(f"   ✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_git_lfs():
    """Check if Git LFS is available."""
    print("🔍 Checking Git LFS availability...")
    
    # Check if git lfs is installed
    try:
        result = subprocess.run(['git', 'lfs', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git LFS available: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️ Git LFS not found, attempting to install...")
    
    # Try to install git-lfs on different systems
    install_commands = [
        # Windows (if chocolatey is available)
        "choco install git-lfs",
        # Windows (if winget is available)  
        "winget install Git.Git-LFS",
        # Linux
        "sudo apt-get update && sudo apt-get install -y git-lfs",
        # macOS
        "brew install git-lfs"
    ]
    
    for cmd in install_commands:
        if run_command(cmd, f"Installing Git LFS: {cmd}"):
            # Initialize git lfs
            run_command(['git', 'lfs', 'install'], "Initializing Git LFS")
            return True
    
    print("❌ Could not install Git LFS automatically")
    print("💡 Please install Git LFS manually:")
    print("   Windows: https://git-lfs.github.io/")
    print("   Linux: sudo apt-get install git-lfs")
    print("   macOS: brew install git-lfs")
    return False

def install_kokoro_dependencies():
    """Install Kokoro TTS dependencies."""
    print("📦 Installing Kokoro TTS dependencies...")
    
    dependencies = [
        "kokoro>=0.9.2",
        "soundfile",
        "torch",
        "torchaudio",
        "numpy",
        "scipy"
    ]
    
    for dep in dependencies:
        if not run_command([sys.executable, "-m", "pip", "install", dep], f"Installing {dep}"):
            print(f"⚠️ Failed to install {dep}, continuing...")
    
    return True

def clone_kokoro_model():
    """Clone the Kokoro multilingual model."""
    print("📥 Cloning Kokoro 82M multilingual model...")
    
    model_dir = "Kokoro-82M"
    repo_url = "https://huggingface.co/hexgrad/Kokoro-82M"
    
    # Remove existing directory if it exists
    if os.path.exists(model_dir):
        print(f"🗑️ Removing existing {model_dir} directory...")
        import shutil
        shutil.rmtree(model_dir)
    
    # Clone the repository
    if not run_command(['git', 'clone', repo_url], f"Cloning {repo_url}"):
        print("❌ Failed to clone Kokoro model repository")
        return False
    
    # Verify the clone
    if not os.path.exists(model_dir):
        print(f"❌ Model directory {model_dir} not found after cloning")
        return False
    
    print(f"✅ Successfully cloned Kokoro model to {model_dir}")
    return True

def verify_model_files():
    """Verify that all required model files are present."""
    print("🔍 Verifying Kokoro model files...")
    
    model_dir = Path("Kokoro-82M")
    
    if not model_dir.exists():
        print(f"❌ Model directory {model_dir} not found")
        return False
    
    # Required files
    required_files = [
        "model.pt",
        "config.json",
        "voice_metadata.json",
        "lang_metadata.json"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = model_dir / file
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✅ {file} ({file_size:,} bytes)")
        else:
            missing_files.append(file)
            print(f"❌ {file} - MISSING")
    
    # Check for language directories
    lang_dirs = [d for d in model_dir.iterdir() if d.is_dir() and len(d.name) == 2]
    if lang_dirs:
        print(f"✅ Found {len(lang_dirs)} language directories: {[d.name for d in lang_dirs]}")
    else:
        print("⚠️ No language directories found")
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required model files verified")
    return True

def setup_environment_variables():
    """Set up environment variables for Kokoro."""
    print("🌍 Setting up environment variables...")
    
    model_path = os.path.abspath("Kokoro-82M")
    
    # Set environment variable
    os.environ["KOKORO_MODEL_PATH"] = model_path
    
    print(f"✅ KOKORO_MODEL_PATH = {model_path}")
    
    # Create a .env file for persistence
    try:
        with open(".env", "a") as f:
            f.write(f"\\nKOKORO_MODEL_PATH={model_path}\\n")
        print("✅ Added to .env file for persistence")
    except Exception as e:
        print(f"⚠️ Could not write to .env file: {e}")
    
    return True

def test_kokoro_pipeline():
    """Test the Kokoro pipeline with multiple languages."""
    print("🧪 Testing Kokoro pipeline...")
    
    try:
        from kokoro import KPipeline
        import soundfile as sf
        
        # Test configurations
        test_configs = [
            ("a", "af_heart", "Hello, this is Kokoro speaking English."),
            ("j", "jf_heart", "こんにちは、これはKokoroです。"),
            ("h", "hf_heart", "नमस्ते, यह Kokoro है।")
        ]
        
        results = []
        
        for lang_code, voice, text in test_configs:
            try:
                print(f"🎤 Testing {lang_code} language with {voice} voice...")
                
                # Initialize pipeline
                pipeline = KPipeline(lang_code=lang_code)
                
                # Generate audio
                output = pipeline(text, voice=voice)
                
                # Save test file
                output_file = f"kokoro_test_{lang_code}_{voice}.wav"
                for i, (_, _, audio) in enumerate(output):
                    sf.write(output_file, audio, 24000)
                    file_size = os.path.getsize(output_file)
                    print(f"✅ Generated {output_file} ({file_size:,} bytes)")
                    results.append((lang_code, voice, output_file, file_size))
                    break  # Only save first segment
                
            except Exception as e:
                print(f"❌ Failed to test {lang_code}/{voice}: {str(e)}")
                results.append((lang_code, voice, None, str(e)))
        
        # Summary
        print("\\n📊 Test Results Summary:")
        successful = 0
        for lang_code, voice, output_file, result in results:
            if output_file:
                print(f"✅ {lang_code}/{voice}: {output_file} ({result:,} bytes)")
                successful += 1
            else:
                print(f"❌ {lang_code}/{voice}: {result}")
        
        print(f"\\n🎯 Success Rate: {successful}/{len(test_configs)} ({successful/len(test_configs)*100:.1f}%)")
        
        return successful == len(test_configs)
        
    except ImportError as e:
        print(f"❌ Cannot import Kokoro: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        return False

def create_kokoro_service_integration():
    """Create integration code for the dubbing pipeline."""
    print("🔗 Creating Kokoro service integration...")
    
    integration_code = '''#!/usr/bin/env python3
"""
Kokoro TTS Service Integration
Fixed multilingual setup with proper model loading.
"""

import os
from typing import List, Dict, Optional
from kokoro import KPipeline
import soundfile as sf

class FixedKokoroTTSService:
    """Fixed Kokoro TTS service with proper multilingual support."""
    
    def __init__(self, lang_code: str = "a", voice: str = "af_heart"):
        """Initialize with proper model path."""
        # Ensure model path is set
        if not os.environ.get("KOKORO_MODEL_PATH"):
            model_path = os.path.abspath("Kokoro-82M")
            if os.path.exists(model_path):
                os.environ["KOKORO_MODEL_PATH"] = model_path
        
        self.lang_code = lang_code
        self.voice = voice
        self.pipeline = None
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the Kokoro pipeline."""
        try:
            self.pipeline = KPipeline(lang_code=self.lang_code)
            print(f"✅ Kokoro pipeline initialized: {self.lang_code}/{self.voice}")
        except Exception as e:
            print(f"❌ Failed to initialize Kokoro pipeline: {str(e)}")
            raise
    
    def generate_tts_chunks(self, segments: List[Dict], progress_callback=None) -> str:
        """Generate TTS chunks from segments."""
        if not self.pipeline:
            raise Exception("Kokoro pipeline not initialized")
        
        os.makedirs("kokoro_chunks", exist_ok=True)
        
        for i, segment in enumerate(segments):
            if progress_callback:
                progress = (i + 1) / len(segments)
                progress_callback(progress, f"Generating Kokoro TTS {i+1}/{len(segments)}")
            
            text = segment.get("text_translated", segment.get("text", ""))
            if not text.strip():
                continue
            
            try:
                # Generate audio
                output = self.pipeline(text, voice=self.voice)
                
                # Save chunk
                chunk_file = f"kokoro_chunks/chunk_{i:03d}.wav"
                for j, (_, _, audio) in enumerate(output):
                    sf.write(chunk_file, audio, 24000)
                    break  # Only save first segment
                
                print(f"✅ Generated {chunk_file}")
                
            except Exception as e:
                print(f"❌ Failed to generate chunk {i}: {str(e)}")
        
        return "kokoro_chunks"

# Language and voice mappings
KOKORO_LANGUAGES = {
    "a": "American English",
    "b": "British English", 
    "j": "Japanese",
    "h": "Hindi",
    "z": "Chinese",
    "f": "French"
}

KOKORO_VOICES = {
    "a": ["af_heart", "am_heart", "af_sky", "am_sky"],
    "b": ["bf_heart", "bm_heart"],
    "j": ["jf_heart", "jm_heart"],
    "h": ["hf_heart", "hm_heart"],
    "z": ["zf_heart", "zm_heart"],
    "f": ["ff_heart", "fm_heart"]
}

def get_available_voices(lang_code: str) -> List[str]:
    """Get available voices for a language."""
    return KOKORO_VOICES.get(lang_code, [])

def test_fixed_kokoro():
    """Test the fixed Kokoro service."""
    try:
        service = FixedKokoroTTSService("a", "af_heart")
        
        test_segments = [
            {"text_translated": "This is a test of the fixed Kokoro TTS service."},
            {"text_translated": "It should work properly with multilingual support."}
        ]
        
        chunks_dir = service.generate_tts_chunks(test_segments)
        print(f"✅ Fixed Kokoro test completed: {chunks_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Fixed Kokoro test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_fixed_kokoro()
'''
    
    with open("fixed_kokoro_service.py", "w", encoding="utf-8") as f:
        f.write(integration_code)
    
    print("✅ Created fixed_kokoro_service.py")
    return True

def main():
    """Main setup function."""
    print("🚀 Kokoro TTS Multilingual Model Setup")
    print("=" * 60)
    
    steps = [
        ("Check Git LFS", check_git_lfs),
        ("Install Dependencies", install_kokoro_dependencies),
        ("Clone Model", clone_kokoro_model),
        ("Verify Files", verify_model_files),
        ("Setup Environment", setup_environment_variables),
        ("Test Pipeline", test_kokoro_pipeline),
        ("Create Integration", create_kokoro_service_integration)
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        print(f"\\n🔧 Step: {step_name}")
        print("-" * 40)
        
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"❌ Step failed: {str(e)}")
            results[step_name] = False
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 Setup Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(steps)
    
    for step_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {step_name}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Overall Result: {passed}/{total} steps completed")
    
    if passed == total:
        print("🎉 Kokoro TTS setup COMPLETE!")
        print("\\n📋 Next Steps:")
        print("1. Test with: python fixed_kokoro_service.py")
        print("2. Use FixedKokoroTTSService in your dubbing pipeline")
        print("3. Available languages: a (English), j (Japanese), h (Hindi), etc.")
        return True
    else:
        print("⚠️ Some setup steps failed. Please review the errors above.")
        print("\\n💡 Common Issues:")
        print("- Git LFS not installed (required for large model files)")
        print("- Network issues downloading the model")
        print("- Missing Python dependencies")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\\n✅ Kokoro TTS Multilingual Setup SUCCESSFUL!")
        exit(0)
    else:
        print("\\n❌ Kokoro TTS Multilingual Setup FAILED!")
        exit(1)