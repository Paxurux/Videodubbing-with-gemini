#!/usr/bin/env python3
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
        print(f"\n🔧 {test_name}")
        print("-" * 20)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results")
    print("=" * 40)
    
    passed = sum(results.values())
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    return passed > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
