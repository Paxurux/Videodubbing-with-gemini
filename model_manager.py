#!/usr/bin/env python3
"""
Model Manager
Handles automatic downloading of models only when they are first used.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

class ModelManager:
    """Manages automatic model downloading and validation."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.models_dir = "models"
        self.kokoro_dir = "Kokoro-82M"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure model directories exist."""
        os.makedirs(self.models_dir, exist_ok=True)
    
    def is_kokoro_available(self) -> bool:
        """Check if Kokoro model is available."""
        kokoro_path = os.path.join(self.kokoro_dir, "kokoro-v0_19.onnx")
        return os.path.exists(kokoro_path)
    
    def download_kokoro_model(self) -> bool:
        """Download Kokoro model if not available."""
        if self.is_kokoro_available():
            print("✅ Kokoro model already available")
            return True
        
        print("📥 Downloading Kokoro model (first time only)...")
        
        try:
            # Check if directory exists but is incomplete
            if os.path.exists(self.kokoro_dir):
                print("🧹 Cleaning incomplete Kokoro directory...")
                shutil.rmtree(self.kokoro_dir)
            
            # Clone the model repository
            cmd = [
                "git", "clone", 
                "https://huggingface.co/hexgrad/Kokoro-82M",
                self.kokoro_dir
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Kokoro model downloaded successfully")
                return True
            else:
                print(f"❌ Failed to download Kokoro model: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading Kokoro model: {str(e)}")
            return False
    
    def ensure_kokoro_model(self) -> bool:
        """Ensure Kokoro model is available, download if needed."""
        if not self.is_kokoro_available():
            return self.download_kokoro_model()
        return True
    
    def get_model_info(self) -> dict:
        """Get information about available models."""
        info = {
            "kokoro": {
                "available": self.is_kokoro_available(),
                "path": self.kokoro_dir if self.is_kokoro_available() else None,
                "size": self.get_directory_size(self.kokoro_dir) if self.is_kokoro_available() else 0
            }
        }
        return info
    
    def get_directory_size(self, directory: str) -> int:
        """Get the size of a directory in bytes."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception:
            return 0
    
    def cleanup_incomplete_downloads(self):
        """Clean up any incomplete model downloads."""
        try:
            # Check for incomplete Kokoro download
            if os.path.exists(self.kokoro_dir) and not self.is_kokoro_available():
                print("🧹 Cleaning incomplete Kokoro download...")
                shutil.rmtree(self.kokoro_dir)
                print("✅ Cleanup complete")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")

# Global model manager instance
model_manager = ModelManager()

def ensure_kokoro_model() -> bool:
    """Convenience function to ensure Kokoro model is available."""
    return model_manager.ensure_kokoro_model()

def is_kokoro_available() -> bool:
    """Convenience function to check if Kokoro model is available."""
    return model_manager.is_kokoro_available()

# Test the model manager
if __name__ == "__main__":
    print("🧪 Testing Model Manager")
    print("=" * 50)
    
    manager = ModelManager()
    
    # Test model info
    info = manager.get_model_info()
    print(f"📊 Model Info:")
    for model, details in info.items():
        print(f"  {model}: {'✅ Available' if details['available'] else '❌ Not available'}")
        if details['available']:
            size_mb = details['size'] / (1024 * 1024)
            print(f"    Size: {size_mb:.1f} MB")
    
    # Test cleanup
    manager.cleanup_incomplete_downloads()
    
    print("\n🎉 Model Manager test complete!")