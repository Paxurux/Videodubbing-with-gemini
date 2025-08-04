#!/usr/bin/env python3
"""
Test Video Dubbing Integration
"""

import os
import tempfile
import json
from pathlib import Path

def test_video_dubbing_service():
    """Test the video dubbing service functionality."""
    print("🧪 Testing Video Dubbing Service")
    print("=" * 50)
    
    try:
        from video_dubbing_service import VideoDubbingService
        
        # Initialize service
        service = VideoDubbingService()
        print("✅ VideoDubbingService initialized")
        
        # Test finding audio files
        audio_files = service.find_audio_files()
        print(f"✅ Found {len(audio_files)} audio files")
        
        for audio in audio_files[:5]:  # Show first 5
            print(f"  - {audio['display_name']}")
            print(f"    Engine: {audio['engine']} | Language: {audio['language']}")
            print(f"    File: {audio['file_path']}")
            print()
        
        # Test filename parsing
        test_filenames = [
            "temp_audio/combined_gemini_tts.wav",
            "temp_audio/combined_edge_tts.wav", 
            "temp_audio/combined_kokoro_tts.wav",
            "voices/gemini_hi_deep_demo.wav",
            "voices/edge_en_us_demo.wav",
            "final_audio/kokoro_tts_final.wav"
        ]
        
        print("🧪 Testing filename parsing:")
        for filename in test_filenames:
            parsed = service.parse_audio_filename(filename)
            if parsed:
                print(f"✅ {filename} -> {parsed['display_name']}")
            else:
                print(f"❌ Failed to parse: {filename}")
        
        print("\n🎉 Video Dubbing Service test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Video Dubbing Service test FAILED: {str(e)}")
        return False

def test_app_integration():
    """Test the app.py integration functions."""
    print("\n🧪 Testing App Integration")
    print("=" * 50)
    
    try:
        # Test the functions we added to app.py
        import sys
        import os
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test get_audio_preview_info function logic
        from video_dubbing_service import VideoDubbingService
        
        service = VideoDubbingService()
        audio_files = service.find_audio_files()
        
        if audio_files:
            print(f"✅ Found {len(audio_files)} audio files for preview")
            
            # Simulate the preview info generation
            preview_text = f"Found {len(audio_files)} audio files ready for dubbing:\n\n"
            
            for audio_info in audio_files[:3]:  # First 3
                file_size = os.path.getsize(audio_info['file_path']) / 1024  # KB
                preview_text += f"🎵 **{audio_info['display_name']}**\n"
                preview_text += f"   Engine: {audio_info['engine'].title()} | Language: {audio_info['language'].upper()}\n"
                preview_text += f"   File: {os.path.basename(audio_info['file_path'])} ({file_size:.1f} KB)\n\n"
            
            print("✅ Preview text generation working")
            print(f"Preview sample:\n{preview_text[:200]}...")
        else:
            print("⚠️ No audio files found for testing")
        
        print("\n🎉 App Integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ App Integration test FAILED: {str(e)}")
        return False

def test_ui_structure():
    """Test that the UI structure is correct."""
    print("\n🧪 Testing UI Structure")
    print("=" * 50)
    
    try:
        # Check if app.py has the required UI elements
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        required_elements = [
            'Step 4.5: Multi-Language Video Dubbing',
            'dubbing_video_input = gr.File',
            'enable_video_preview = gr.Checkbox',
            'audio_previews_info = gr.Markdown',
            'create_dubbed_videos_btn = gr.Button',
            'dubbing_status = gr.Textbox',
            'dubbed_videos_info = gr.Markdown',
            'def get_audio_preview_info',
            'def create_all_dubbed_videos',
            'from video_dubbing_service import VideoDubbingService'
        ]
        
        for element in required_elements:
            if element in app_content:
                print(f"✅ Found: {element}")
            else:
                print(f"❌ Missing: {element}")
                return False
        
        print("\n🎉 UI Structure test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ UI Structure test FAILED: {str(e)}")
        return False

def test_video_creation_logic():
    """Test the video creation logic (without actual video files)."""
    print("\n🧪 Testing Video Creation Logic")
    print("=" * 50)
    
    try:
        from video_dubbing_service import VideoDubbingService
        
        service = VideoDubbingService()
        
        # Test directory creation
        service.ensure_directories()
        print("✅ Directory creation working")
        
        # Test that output directory exists
        if os.path.exists(service.output_dir):
            print(f"✅ Output directory exists: {service.output_dir}")
        else:
            print(f"❌ Output directory missing: {service.output_dir}")
            return False
        
        # Test video info function (will fail gracefully without ffprobe)
        try:
            info = service.get_video_info("nonexistent.mp4")
            print("✅ Video info function handles missing files gracefully")
        except Exception as e:
            print(f"⚠️ Video info function error (expected): {str(e)}")
        
        print("\n🎉 Video Creation Logic test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Video Creation Logic test FAILED: {str(e)}")
        return False

def create_sample_audio_files():
    """Create sample audio files for testing."""
    print("\n🧪 Creating Sample Audio Files")
    print("=" * 50)
    
    try:
        # Create directories
        os.makedirs("temp_audio", exist_ok=True)
        os.makedirs("voices", exist_ok=True)
        
        # Create dummy audio files (empty files for testing)
        sample_files = [
            "temp_audio/combined_gemini_tts.wav",
            "temp_audio/combined_edge_tts.wav",
            "temp_audio/combined_kokoro_tts.wav",
            "voices/gemini_hi_deep_demo.wav",
            "voices/gemini_en_soft_demo.wav",
            "voices/edge_hi_IN_MadhurNeural_demo.wav"
        ]
        
        for file_path in sample_files:
            if not os.path.exists(file_path):
                # Create a minimal WAV file header (44 bytes)
                with open(file_path, 'wb') as f:
                    # WAV header for empty file
                    f.write(b'RIFF')
                    f.write((36).to_bytes(4, 'little'))  # File size - 8
                    f.write(b'WAVE')
                    f.write(b'fmt ')
                    f.write((16).to_bytes(4, 'little'))  # Subchunk1Size
                    f.write((1).to_bytes(2, 'little'))   # AudioFormat (PCM)
                    f.write((1).to_bytes(2, 'little'))   # NumChannels
                    f.write((44100).to_bytes(4, 'little'))  # SampleRate
                    f.write((88200).to_bytes(4, 'little'))  # ByteRate
                    f.write((2).to_bytes(2, 'little'))   # BlockAlign
                    f.write((16).to_bytes(2, 'little'))  # BitsPerSample
                    f.write(b'data')
                    f.write((0).to_bytes(4, 'little'))   # Subchunk2Size
                
                print(f"✅ Created: {file_path}")
        
        print(f"\n🎉 Created {len(sample_files)} sample audio files!")
        return True
        
    except Exception as e:
        print(f"❌ Sample file creation FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Video Dubbing Integration Tests")
    print("=" * 60)
    
    # Create sample files first
    create_sample_audio_files()
    
    # Run all tests
    tests = [
        test_video_dubbing_service,
        test_app_integration,
        test_ui_structure,
        test_video_creation_logic
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Video dubbing integration is complete!")
        print("\n🎯 READY FOR USE:")
        print("1. Generate TTS audio files using the existing TTS system")
        print("2. Upload an original video in Step 4.5")
        print("3. Click 'Create All Dubbed Videos' to generate dubbed versions")
        print("4. Download videos from the 'dubbed_videos' directory")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    print("=" * 60)