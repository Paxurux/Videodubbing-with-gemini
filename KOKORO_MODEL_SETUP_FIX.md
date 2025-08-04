# Kokoro Model Setup Fix ✅

## 🐛 Problem
Getting error: `❌ Kokoro model not available. Please ensure Kokoro-82M is installed.`

## 🔧 Fixes Applied

### 1. **Fixed Auto-Download Directory Structure**
**File**: `kokoro_tts_service.py`
- ✅ Fixed clone command to use correct directory structure
- ✅ Clone now creates `kokoro_models/Kokoro-82M/` properly

### 2. **Enhanced Installation Script**
**File**: `install.js`
- ✅ Added proper directory creation: `mkdir -p kokoro_models`
- ✅ Fixed clone command to run in correct directory
- ✅ Added model verification step

### 3. **Created Test Script**
**File**: `test_kokoro_model_setup.py`
- ✅ Tests model availability and auto-download
- ✅ Provides manual setup instructions if needed
- ✅ Verifies complete Kokoro TTS functionality

## 🚀 How to Fix the Issue

### **Option 1: Re-run Installation**
```bash
# In Pinokio, click "Install" again to run the fixed installation script
```

### **Option 2: Manual Setup**
```bash
# 1. Install Git LFS
git lfs install

# 2. Create model directory
mkdir -p kokoro_models

# 3. Clone Kokoro model
cd kokoro_models
git clone https://huggingface.co/hexgrad/Kokoro-82M

# 4. Verify installation
python test_kokoro_model_setup.py
```

### **Option 3: Test Auto-Download**
```bash
# Run the test script to trigger auto-download
python test_kokoro_model_setup.py
```

## 📁 Expected Directory Structure
```
your-project/
├── kokoro_models/
│   └── Kokoro-82M/
│       ├── kokoro-v0_19.onnx
│       ├── voices/
│       ├── config.json
│       └── other model files...
├── app.py
├── kokoro_tts_service.py
└── other files...
```

## 🧪 Verification Steps

### **1. Check Model Directory**
```python
import os
model_path = "kokoro_models/Kokoro-82M"
print(f"Model exists: {os.path.exists(model_path)}")
```

### **2. Test Service Initialization**
```python
from kokoro_tts_service import KokoroTTSService
service = KokoroTTSService()
print(f"Model available: {service.model_available}")
```

### **3. Test Auto-Download**
```python
service = KokoroTTSService()
if not service.model_available:
    success = service._ensure_model_available()
    print(f"Auto-download success: {success}")
```

## 🔍 Troubleshooting

### **If Git LFS is not available:**
```bash
# Install Git LFS first
# On Ubuntu/Debian:
sudo apt-get install git-lfs

# On Windows: Download from https://git-lfs.github.io/
# On macOS: brew install git-lfs

git lfs install
```

### **If clone fails due to network:**
```bash
# Try with different clone options
git clone --depth 1 https://huggingface.co/hexgrad/Kokoro-82M
# or
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/hexgrad/Kokoro-82M
```

### **If model files are incomplete:**
```bash
cd kokoro_models/Kokoro-82M
git lfs pull  # Download LFS files
```

## 📊 What Each Fix Does

### **Auto-Download Fix**
- **Before**: Clone command failed due to incorrect path
- **After**: Properly clones to `kokoro_models/Kokoro-82M/`

### **Installation Fix**
- **Before**: Model not downloaded during installation
- **After**: Model automatically downloaded and verified

### **Test Script**
- **Before**: No way to verify setup
- **After**: Complete testing and manual setup instructions

## ✅ Expected Results

After applying these fixes:

1. **During Installation**: 
   ```
   ✅ Kokoro-82M model setup complete (if available)
   🔍 Checking Kokoro model...
   ✅ Kokoro model found
   ```

2. **When Using Kokoro TTS**:
   ```
   🎙️ Kokoro TTS Service initialized
   🎤 Voice: af_bella
   📁 Model path: kokoro_models/Kokoro-82M
   ✅ Model available: True
   ```

3. **Auto-Download (if needed)**:
   ```
   📥 Kokoro model not found. Starting auto-download...
   🔗 Downloading from: https://huggingface.co/hexgrad/Kokoro-82M
   🔄 Cloning model to kokoro_models/Kokoro-82M...
   ✅ Model repository cloned successfully
   📥 Kokoro TTS model downloaded and ready
   ```

## 🎯 Summary

The fixes ensure:
- ✅ Proper directory structure for Kokoro model
- ✅ Automatic model download during installation
- ✅ Fallback auto-download if model missing
- ✅ Complete testing and verification
- ✅ Clear error messages and manual setup instructions

The Kokoro TTS should now work without the "model not available" error!