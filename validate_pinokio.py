#!/usr/bin/env python3
"""
Validation script to ensure all Pinokio components are properly configured
and the dubbing pipeline is ready for use.
"""

import os
import sys
import importlib
import subprocess
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
        ('gradio', 'Gradio web interface'),
        ('torch', 'PyTorch deep learning framework'),
        ('nemo_toolkit', 'NVIDIA NeMo ASR toolkit'),
        ('google.generativeai', 'Google Gemini API'),
        ('tiktoken', 'Token counting for API limits'),
        ('pandas', 'Data processing'),
        ('soundfile', 'Audio file I/O'),
        ('scipy', 'Signal processing'),
        ('requests', 'HTTP requests')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - MISSING - {description}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_dubbing_pipeline_components():
    """Check dubbing pipeline components."""
    components = [
        ('pipeline_controller', 'Pipeline orchestration'),
        ('translation', 'Translation service'),
        ('tts', 'Text-to-speech service'),
        ('audio_utils', 'Audio processing utilities'),
        ('state_manager', 'State management'),
        ('manual_mode_utils', 'Manual mode functionality'),
        ('error_handler', 'Error handling and recovery'),
        ('config', 'Configuration management')
    ]
    
    missing_components = []
    
    for component, description in components:
        try:
            importlib.import_module(component)
            print(f"✅ {component}.py - {description}")
        except ImportError:
            print(f"❌ {component}.py - MISSING - {description}")
            missing_components.append(component)
    
    return len(missing_components) == 0, missing_components

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

def check_pinokio_files():
    """Check Pinokio configuration files."""
    pinokio_files = [
        ('pinokio.js', 'Pinokio launcher configuration'),
        ('install.js', 'Installation script'),
        ('start.js', 'Startup script'),
        ('update.js', 'Update script'),
        ('requirements.txt', 'Python dependencies'),
        ('app.py', 'Main application'),
        ('README.md', 'Documentation')
    ]
    
    missing_files = []
    
    for file, description in pinokio_files:
        if os.path.exists(file):
            print(f"✅ {file} - {description}")
        else:
            print(f"❌ {file} - MISSING - {description}")
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files

def check_documentation():
    """Check documentation files."""
    doc_files = [
        ('USER_MANUAL.md', 'Complete user guide'),
        ('TROUBLESHOOTING_GUIDE.md', 'Troubleshooting guide'),
        ('EXAMPLES.md', 'Usage examples'),
        ('API_DOCUMENTATION.md', 'Technical API reference'),
        ('INTEGRATION_TEST_SUMMARY.md', 'Test results summary')
    ]
    
    missing_docs = []
    
    for file, description in doc_files:
        if os.path.exists(file):
            print(f"✅ {file} - {description}")
        else:
            print(f"❌ {file} - MISSING - {description}")
            missing_docs.append(file)
    
    return len(missing_docs) == 0, missing_docs

def check_test_files():
    """Check test files."""
    test_files = [
        'test_integration_final.py',
        'test_comprehensive_error_handling.py',
        'test_manual_mode.py',
        'test_state_manager.py',
        'test_audio_utils.py',
        'test_pipeline_controller.py'
    ]
    
    existing_tests = []
    
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
            print(f"✅ {test_file}")
    
    print(f"📊 Test coverage: {len(existing_tests)}/{len(test_files)} test files available")
    return len(existing_tests) > 0

def validate_app_functionality():
    """Validate core app functionality."""
    try:
        # Test imports
        from pipeline_controller import PipelineController
        from manual_mode_utils import ManualModeWorkflow
        from error_handler import ErrorHandler
        
        print("✅ Core dubbing pipeline components imported successfully")
        
        # Test basic functionality
        workflow = ManualModeWorkflow()
        error_handler = ErrorHandler()
        
        print("✅ Core components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ App functionality validation failed: {str(e)}")
        return False

def main():
    """Run complete validation."""
    print("🔍 Validating Pinokio Dubbing Pipeline Setup...")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Python Dependencies", lambda: check_dependencies()[0]),
        ("Dubbing Pipeline Components", lambda: check_dubbing_pipeline_components()[0]),
        ("FFmpeg Installation", check_ffmpeg),
        ("Pinokio Files", lambda: check_pinokio_files()[0]),
        ("Documentation", lambda: check_documentation()[0]),
        ("Test Files", check_test_files),
        ("App Functionality", validate_app_functionality)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"❌ {check_name} check failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"PINOKIO VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 ALL CHECKS PASSED!")
        print(f"✅ Your Pinokio Dubbing Pipeline is ready for use!")
        print(f"\n📋 What you can do now:")
        print(f"   1. Run 'python app.py' to start the application")
        print(f"   2. Visit the Gradio interface in your browser")
        print(f"   3. Use the Transcription tab for audio transcription")
        print(f"   4. Use the Dubbing Pipeline tab for video dubbing")
        print(f"   5. Check the Help tab for detailed usage instructions")
        
        print(f"\n🔑 Don't forget to:")
        print(f"   • Get your Gemini API keys from https://makersuite.google.com/app/apikey")
        print(f"   • Use multiple API keys for better reliability")
        print(f"   • Check the documentation files for detailed guides")
        
        return True
    else:
        print(f"\n❌ {total - passed} checks failed.")
        print(f"Please resolve the issues above before using the application.")
        
        print(f"\n💡 Common solutions:")
        print(f"   • Install missing dependencies: pip install -r requirements.txt")
        print(f"   • Install FFmpeg and add to PATH")
        print(f"   • Ensure Python 3.8+ is installed")
        print(f"   • Check that all files are present in the project directory")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)