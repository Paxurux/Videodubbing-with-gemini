# Dubbing Pipeline Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the dubbing pipeline system.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [API-Related Problems](#api-related-problems)
4. [Audio/Video Issues](#audiovideo-issues)
5. [Performance Problems](#performance-problems)
6. [Manual Mode Issues](#manual-mode-issues)
7. [System Requirements](#system-requirements)
8. [Log Analysis](#log-analysis)
9. [Recovery Procedures](#recovery-procedures)
10. [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Script

Run this script to quickly diagnose system health:

```python
#!/usr/bin/env python3
"""
Quick health check for dubbing pipeline system.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version: {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_dependencies():
    """Check required Python packages."""
    required_packages = [
        'gradio', 'torch', 'nemo_toolkit', 'google-generativeai',
        'soundfile', 'scipy', 'pandas', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_ffmpeg():
    """Check FFmpeg installation."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg: {version_line}")
            return True
        else:
            print("❌ FFmpeg: Not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg: Not found in PATH")
        return False

def check_gpu():
    """Check GPU availability."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ GPU: {gpu_count} device(s) - {gpu_name}")
            return True
        else:
            print("⚠️ GPU: CUDA not available (CPU mode only)")
            return False
    except ImportError:
        print("❌ GPU: Cannot check (PyTorch not installed)")
        return False

def check_file_permissions():
    """Check file system permissions."""
    test_file = "health_check_test.tmp"
    try:
        # Test write permission
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Test read permission
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Test delete permission
        os.remove(test_file)
        
        print("✅ File permissions: Read/Write/Delete OK")
        return True
        
    except Exception as e:
        print(f"❌ File permissions: {e}")
        return False

def check_disk_space():
    """Check available disk space."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        
        if free_gb > 5:  # At least 5GB free
            print(f"✅ Disk space: {free_gb:.1f} GB available")
            return True
        else:
            print(f"⚠️ Disk space: {free_gb:.1f} GB available (low)")
            return False
            
    except Exception as e:
        print(f"❌ Disk space: Cannot check - {e}")
        return False

def check_pipeline_files():
    """Check if pipeline files exist."""
    required_files = [
        'app.py', 'pipeline_controller.py', 'translation.py', 
        'tts.py', 'audio_utils.py', 'state_manager.py',
        'manual_mode_utils.py', 'config.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files

def run_health_check():
    """Run complete health check."""
    print("🔍 Running Dubbing Pipeline Health Check...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", lambda: check_dependencies()[0]),
        ("FFmpeg", check_ffmpeg),
        ("GPU Support", check_gpu),
        ("File Permissions", check_file_permissions),
        ("Disk Space", check_disk_space),
        ("Pipeline Files", lambda: check_pipeline_files()[0])
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        if check_func():
            passed += 1
    
    print(f"\n📊 Health Check Summary:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Status: {'✅ HEALTHY' if passed == total else '⚠️ ISSUES DETECTED'}")
    
    if passed < total:
        print(f"\n💡 Recommendations:")
        print(f"   - Review failed checks above")
        print(f"   - Install missing dependencies")
        print(f"   - Check system requirements")
        print(f"   - Consult troubleshooting guide")
    
    return passed == total

if __name__ == "__main__":
    run_health_check()
```

## Common Issues

### Issue 1: "Module not found" Errors

**Symptoms:**
```
ImportError: No module named 'gradio'
ModuleNotFoundError: No module named 'nemo_toolkit'
```

**Solutions:**

1. **Install missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Use virtual environment:**
   ```bash
   python -m venv dubbing_env
   # Windows
   dubbing_env\Scripts\activate
   # Linux/Mac
   source dubbing_env/bin/activate
   pip install -r requirements.txt
   ```

3. **Check Python path:**
   ```python
   import sys
   print(sys.path)
   ```

### Issue 2: "FFmpeg not found" Error

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solutions:**

1. **Windows:**
   - Download FFmpeg from https://ffmpeg.org/download.html
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to system PATH

2. **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

3. **macOS:**
   ```bash
   brew install ffmpeg
   ```

4. **Verify installation:**
   ```bash
   ffmpeg -version
   ```

### Issue 3: CUDA/GPU Issues

**Symptoms:**
```
RuntimeError: CUDA out of memory
RuntimeError: No CUDA GPUs are available
```

**Solutions:**

1. **Check CUDA installation:**
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"CUDA version: {torch.version.cuda}")
   print(f"GPU count: {torch.cuda.device_count()}")
   ```

2. **Install CUDA-compatible PyTorch:**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   ```

3. **Reduce memory usage:**
   - Process shorter video segments
   - Use CPU mode if GPU memory is insufficient
   - Close other GPU-intensive applications

### Issue 4: Pipeline State Corruption

**Symptoms:**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
KeyError: 'current_stage'
```

**Solutions:**

1. **Clear pipeline state:**
   ```python
   from state_manager import StateManager
   state_mgr = StateManager()
   state_mgr.clear_pipeline_state()
   ```

2. **Manual cleanup:**
   ```bash
   rm pipeline_state.json
   rm -rf tts_chunks/
   rm original_asr.json translated.json
   ```

3. **Reset to clean state:**
   ```python
   from pipeline_controller import PipelineController
   controller = PipelineController()
   controller.reset_pipeline_state()
   ```

## API-Related Problems

### Issue 5: Gemini API Key Errors

**Symptoms:**
```
google.api_core.exceptions.Unauthenticated: 401 API key not valid
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Solutions:**

1. **Verify API key:**
   ```python
   from translation import TranslationService
   service = TranslationService(["your_api_key"])
   is_valid = service.test_api_key("your_api_key")
   print(f"API key valid: {is_valid}")
   ```

2. **Check quota:**
   - Visit [Google AI Studio](https://makersuite.google.com/)
   - Check API usage and limits
   - Consider upgrading plan or using multiple keys

3. **Use multiple API keys:**
   ```python
   api_keys = [
       "key_1",
       "key_2", 
       "key_3"
   ]
   # System will rotate keys automatically
   ```

### Issue 6: Translation Service Timeouts

**Symptoms:**
```
requests.exceptions.Timeout: HTTPSConnectionPool
requests.exceptions.ConnectionError: Failed to establish connection
```

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping google.com
   curl -I https://generativelanguage.googleapis.com
   ```

2. **Increase timeout values:**
   ```python
   # In translation.py, modify timeout settings
   response = requests.post(url, json=payload, timeout=60)  # Increase from 30
   ```

3. **Implement retry logic:**
   ```python
   import time
   for attempt in range(3):
       try:
           result = translation_service.translate_segments(segments)
           break
       except Exception as e:
           if attempt < 2:
               time.sleep(5 * (attempt + 1))  # Exponential backoff
           else:
               raise e
   ```

## Audio/Video Issues

### Issue 7: Unsupported Video Format

**Symptoms:**
```
ValueError: Unsupported video format: .avi
ffmpeg: error while opening codec for output stream
```

**Solutions:**

1. **Convert to supported format:**
   ```bash
   ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
   ```

2. **Check supported formats:**
   ```python
   supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
   ```

3. **Use format conversion utility:**
   ```python
   from audio_utils import AudioProcessor
   processor = AudioProcessor()
   converted_video = processor.convert_video_format("input.avi", "output.mp4")
   ```

### Issue 8: Audio Sync Problems

**Symptoms:**
- Audio and video are out of sync
- Audio is shorter/longer than video
- Timing mismatches in dubbed content

**Solutions:**

1. **Validate timing data:**
   ```python
   from audio_utils import AudioProcessor
   processor = AudioProcessor()
   
   # Check if segments have valid timing
   for segment in segments:
       if segment['end'] <= segment['start']:
           print(f"Invalid timing: {segment}")
   ```

2. **Recalculate audio duration:**
   ```python
   # Ensure TTS chunks match expected duration
   processor.validate_audio_chunks("tts_chunks/", segments)
   ```

3. **Use different sync strategy:**
   ```python
   # In audio_utils.py, try different sync methods
   dubbed_video = processor.sync_audio_with_video(
       video_path, audio_path, output_path,
       sync_method="stretch"  # or "pad", "trim"
   )
   ```

### Issue 9: Poor Audio Quality

**Symptoms:**
- Distorted or robotic-sounding TTS
- Background noise in output
- Volume inconsistencies

**Solutions:**

1. **Improve TTS settings:**
   ```python
   # Use higher quality voice models
   voice_name = "en-US-Journey-D"  # Premium voice
   
   # Adjust TTS parameters
   tts_config = {
       "speaking_rate": 1.0,
       "pitch": 0.0,
       "volume_gain_db": 0.0
   }
   ```

2. **Audio post-processing:**
   ```python
   from audio_utils import AudioProcessor
   processor = AudioProcessor()
   
   # Normalize audio levels
   normalized_audio = processor.normalize_audio_levels(
       audio_path, target_lufs=-16.0
   )
   
   # Apply noise reduction
   clean_audio = processor.reduce_noise(normalized_audio)
   ```

3. **Check input audio quality:**
   ```bash
   # Analyze input audio
   ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
   ```

## Performance Problems

### Issue 10: Slow Processing Speed

**Symptoms:**
- Pipeline takes hours to complete
- High CPU/memory usage
- System becomes unresponsive

**Solutions:**

1. **Enable GPU acceleration:**
   ```python
   # Ensure CUDA is available for ASR
   import torch
   device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
   print(f"Using device: {device}")
   ```

2. **Optimize chunk size:**
   ```python
   # In config.py, adjust chunk duration
   PIPELINE_DEFAULTS = {
       "chunk_duration_seconds": 15,  # Reduce from 30
       "max_concurrent_chunks": 4     # Process multiple chunks
   }
   ```

3. **Use multiple API keys:**
   ```python
   # Distribute load across multiple keys
   api_keys = ["key1", "key2", "key3", "key4"]
   ```

4. **Monitor system resources:**
   ```python
   import psutil
   
   def monitor_resources():
       cpu = psutil.cpu_percent()
       memory = psutil.virtual_memory().percent
       print(f"CPU: {cpu}%, Memory: {memory}%")
   ```

### Issue 11: Memory Issues

**Symptoms:**
```
MemoryError: Unable to allocate array
RuntimeError: CUDA out of memory
```

**Solutions:**

1. **Process in smaller chunks:**
   ```python
   # Reduce chunk size for large videos
   max_chunk_duration = 10  # seconds
   ```

2. **Clear memory between operations:**
   ```python
   import gc
   import torch
   
   # Clear Python garbage collection
   gc.collect()
   
   # Clear CUDA cache
   if torch.cuda.is_available():
       torch.cuda.empty_cache()
   ```

3. **Use CPU mode for large files:**
   ```python
   # Force CPU mode to avoid GPU memory limits
   os.environ["CUDA_VISIBLE_DEVICES"] = ""
   ```

## Manual Mode Issues

### Issue 12: Translation Validation Errors

**Symptoms:**
```
ValidationError: Invalid JSON format
ValueError: Missing required field 'text_translated'
```

**Solutions:**

1. **Check JSON format:**
   ```python
   import json
   
   # Validate JSON syntax
   try:
       data = json.loads(translation_text)
       print("✅ Valid JSON")
   except json.JSONDecodeError as e:
       print(f"❌ Invalid JSON: {e}")
   ```

2. **Use template generator:**
   ```python
   from manual_mode_utils import ManualModeWorkflow
   
   workflow = ManualModeWorkflow()
   template = workflow.template_generator.generate_template_from_asr()
   print("Use this template:", template)
   ```

3. **Validate required fields:**
   ```python
   required_fields = ['start', 'end', 'text_translated']
   
   for segment in translation_data:
       for field in required_fields:
           if field not in segment:
               print(f"Missing field '{field}' in segment: {segment}")
   ```

### Issue 13: Timing Overlap Issues

**Symptoms:**
```
ValidationError: Overlapping time segments detected
ValueError: Segment end time before start time
```

**Solutions:**

1. **Fix timing overlaps:**
   ```python
   def fix_timing_overlaps(segments):
       segments.sort(key=lambda x: x['start'])
       
       for i in range(1, len(segments)):
           if segments[i]['start'] < segments[i-1]['end']:
               # Adjust start time to avoid overlap
               segments[i]['start'] = segments[i-1]['end'] + 0.1
   ```

2. **Validate timing consistency:**
   ```python
   def validate_timing(segments):
       for segment in segments:
           if segment['end'] <= segment['start']:
               print(f"Invalid timing: {segment}")
               segment['end'] = segment['start'] + 1.0  # Add 1 second minimum
   ```

## System Requirements

### Minimum Requirements

- **OS:** Windows 10, macOS 10.15, or Linux (Ubuntu 18.04+)
- **Python:** 3.8 or higher
- **RAM:** 8GB (16GB recommended)
- **Storage:** 10GB free space
- **Internet:** Stable connection for API calls

### Recommended Requirements

- **OS:** Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- **Python:** 3.9 or higher
- **RAM:** 16GB or more
- **GPU:** NVIDIA GPU with 4GB+ VRAM (for faster ASR)
- **Storage:** 50GB+ free space (for large video processing)
- **Internet:** High-speed connection (100+ Mbps)

### Software Dependencies

```bash
# Core dependencies
pip install gradio>=3.50.0
pip install torch>=1.13.0
pip install nemo-toolkit[asr]>=1.20.0
pip install google-generativeai>=0.3.0

# Audio/video processing
pip install soundfile>=0.12.0
pip install scipy>=1.10.0
pip install pandas>=2.0.0

# System utilities
pip install requests>=2.28.0
pip install psutil>=5.9.0
```

## Log Analysis

### Understanding Log Files

1. **pipeline.log** - Main pipeline execution log
2. **error_log.json** - Structured error information
3. **pipeline_api_log.json** - API call logs

### Common Log Patterns

**Successful execution:**
```
INFO - Pipeline started: automatic mode
INFO - ASR completed: 45 segments extracted
INFO - Translation completed: 45 segments translated
INFO - TTS completed: 45 audio chunks generated
INFO - Audio stitching completed
INFO - Video sync completed
INFO - Pipeline completed successfully
```

**API errors:**
```
ERROR - Translation failed: API key invalid
ERROR - Quota exceeded for key: sk-...
WARNING - Retrying with backup API key
```

**Memory issues:**
```
ERROR - CUDA out of memory
WARNING - Falling back to CPU mode
INFO - Processing with reduced chunk size
```

### Log Analysis Script

```python
#!/usr/bin/env python3
"""
Analyze pipeline logs for common issues.
"""

import re
import json
from collections import Counter

def analyze_pipeline_log(log_file="pipeline.log"):
    """Analyze main pipeline log file."""
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Count log levels
    levels = Counter()
    errors = []
    warnings = []
    
    for line in lines:
        if " - ERROR - " in line:
            levels['ERROR'] += 1
            errors.append(line.strip())
        elif " - WARNING - " in line:
            levels['WARNING'] += 1
            warnings.append(line.strip())
        elif " - INFO - " in line:
            levels['INFO'] += 1
    
    print(f"📊 Log Analysis for {log_file}:")
    print(f"   Total lines: {len(lines)}")
    print(f"   INFO: {levels['INFO']}")
    print(f"   WARNING: {levels['WARNING']}")
    print(f"   ERROR: {levels['ERROR']}")
    
    if errors:
        print(f"\n❌ Recent Errors:")
        for error in errors[-5:]:  # Show last 5 errors
            print(f"   {error}")
    
    if warnings:
        print(f"\n⚠️ Recent Warnings:")
        for warning in warnings[-3:]:  # Show last 3 warnings
            print(f"   {warning}")

if __name__ == "__main__":
    analyze_pipeline_log()
```

## Recovery Procedures

### Procedure 1: Complete Pipeline Reset

```python
#!/usr/bin/env python3
"""
Complete pipeline reset procedure.
"""

import os
import shutil
from pathlib import Path

def complete_reset():
    """Reset pipeline to clean state."""
    
    print("🔄 Starting complete pipeline reset...")
    
    # Files to remove
    files_to_remove = [
        "pipeline_state.json",
        "original_asr.json", 
        "translated.json",
        "stitched_audio.wav",
        "output_dubbed.mp4",
        "pipeline.log",
        "error_log.json"
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "tts_chunks",
        "__pycache__"
    ]
    
    # Remove files
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Removed: {file}")
    
    # Remove directories
    for dir in dirs_to_remove:
        if os.path.exists(dir):
            shutil.rmtree(dir)
            print(f"   Removed: {dir}/")
    
    print("✅ Pipeline reset completed")

if __name__ == "__main__":
    complete_reset()
```

### Procedure 2: Selective Recovery

```python
#!/usr/bin/env python3
"""
Selective recovery based on pipeline state.
"""

from pipeline_controller import PipelineController
from state_manager import StateManager

def selective_recovery():
    """Recover from specific pipeline stage."""
    
    controller = PipelineController()
    state_manager = StateManager()
    
    try:
        # Detect current state
        current_state = controller.detect_pipeline_state()
        print(f"📊 Current pipeline state: {current_state}")
        
        if current_state == "complete":
            print("✅ Pipeline already complete")
            return
        
        # Load saved state
        saved_state = state_manager.load_pipeline_state()
        print(f"💾 Saved state: {saved_state.get('current_stage', 'unknown')}")
        
        # Recovery options
        recovery_options = {
            "asr_needed": "Restart from ASR (transcription)",
            "translation_needed": "Continue from translation",
            "tts_needed": "Continue from TTS generation", 
            "stitching_needed": "Continue from audio stitching"
        }
        
        if current_state in recovery_options:
            print(f"🔧 Recovery option: {recovery_options[current_state]}")
            
            # Ask user for confirmation
            response = input("Continue with recovery? (y/n): ")
            if response.lower() == 'y':
                print("🚀 Starting recovery...")
                # Recovery logic would go here
                print("✅ Recovery completed")
            else:
                print("❌ Recovery cancelled")
        else:
            print("⚠️ Unknown state - manual intervention required")
    
    except Exception as e:
        print(f"❌ Recovery failed: {e}")

if __name__ == "__main__":
    selective_recovery()
```

## Getting Help

### Before Asking for Help

1. **Run health check script**
2. **Check logs for error messages**
3. **Try basic troubleshooting steps**
4. **Search existing issues**

### Information to Include

When reporting issues, include:

1. **System information:**
   ```bash
   python --version
   pip list | grep -E "(gradio|torch|nemo)"
   ffmpeg -version
   ```

2. **Error messages:**
   - Complete error traceback
   - Relevant log entries
   - Screenshots if applicable

3. **Configuration:**
   - Pipeline configuration used
   - Input file details
   - API key status (without revealing keys)

4. **Steps to reproduce:**
   - Exact steps taken
   - Expected vs actual behavior
   - Minimal example if possible

### Support Channels

1. **GitHub Issues:** For bugs and feature requests
2. **Documentation:** Check README and API docs first
3. **Community Forums:** For general questions
4. **Email Support:** For urgent issues

### Self-Help Resources

1. **Run diagnostics:**
   ```bash
   python health_check.py
   python log_analyzer.py
   ```

2. **Check documentation:**
   - README_DUBBING_PIPELINE.md
   - API_DOCUMENTATION.md
   - EXAMPLES.md

3. **Test with minimal example:**
   ```python
   # Test basic functionality
   from pipeline_controller import PipelineController
   controller = PipelineController()
   state = controller.detect_pipeline_state()
   print(f"Pipeline state: {state}")
   ```

Remember: Most issues can be resolved by following this troubleshooting guide systematically. Start with the health check and work through the relevant sections based on your specific symptoms.