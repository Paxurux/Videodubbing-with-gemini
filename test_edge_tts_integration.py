#!/usr/bin/env python3
"""
Edge TTS Integration Test
Tests the complete Edge TTS pipeline with voice parsing, stitching, and single-request fallback.
"""

import os
import json
import tempfile
from typing import List, Dict

# Import our enhanced components
from edge_tts_voice_parser import EdgeTTSVoiceParser
from enhanced_edge_tts_service import EnhancedEdgeTTSService, EdgeTTSConfig

def test_voice_database_integration():
    """Test complete voice database integration."""
    print("🧪 Testing Voice Database Integration")
    print("=" * 50)
    
    try:
        # Initialize parser
        parser = EdgeTTSVoiceParser()
        
        # Parse voices from markdown
        if not parser.parse_voices():
            print("❌ Failed to parse voices from edgettsvoices.md")
            return False
        
        # Test language mapping
        language_mapping = parser.get_language_voice_mapping()
        
        print(f"✅ Parsed {len(parser.voices)} voices")
        print(f"✅ Found {len(language_mapping)} languages")
        
        # Test specific languages
        test_languages = ['hi', 'en', 'es', 'fr', 'de']
        
        for lang in test_languages:
            voices = language_mapping.get(lang, [])
            if voices:
                print(f"  • {lang}: {len(voices)} voices - {voices[0]}")
            else:
                print(f"  • {lang}: No voices found")
        
        # Test voice lookup
        test_voice = "hi-IN-MadhurNeural"
        voice_info = parser.find_voice_by_short_name(test_voice)
        
        if voice_info:
            print(f"✅ Voice lookup successful: {voice_info['name']} ({voice_info['gender']})")
        else:
            print(f"❌ Voice lookup failed for: {test_voice}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Voice database integration test failed: {str(e)}")
        return False

def test_enhanced_stitching():
    """Test enhanced audio stitching with fade transitions."""
    print("\\n🧪 Testing Enhanced Audio Stitching")
    print("=" * 50)
    
    try:
        # Test segments with various durations
        test_segments = [
            {
                "start": 0.0,
                "end": 3.5,
                "text_translated": "नमस्ते, मैं Enhanced Edge TTS का परीक्षण कर रहा हूँ।"
            },
            {
                "start": 3.5,
                "end": 7.2,
                "text_translated": "यह timestamp synchronization के साथ काम करता है।"
            },
            {
                "start": 7.2,
                "end": 10.8,
                "text_translated": "Audio stitching में fade transitions भी हैं।"
            },
            {
                "start": 10.8,
                "end": 13.5,
                "text_translated": "यह professional quality audio बनाता है।"
            }
        ]
        
        # Initialize service
        config = EdgeTTSConfig(
            voice_name="hi-IN-MadhurNeural",
            language="hi"
        )
        
        service = EnhancedEdgeTTSService(config)
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"[{progress*100:5.1f}%] {message}")
        
        # Test TTS generation
        chunks_dir = service.generate_tts_chunks(test_segments, progress_callback)
        
        if not chunks_dir or not os.path.exists(chunks_dir):
            print("❌ TTS chunk generation failed")
            return False
        
        # Verify generated files
        chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
        
        if len(chunk_files) != len(test_segments):
            print(f"❌ Expected {len(test_segments)} chunks, got {len(chunk_files)}")
            return False
        
        # Analyze chunk quality
        total_size = 0
        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunks_dir, chunk_file)
            chunk_size = os.path.getsize(chunk_path)
            total_size += chunk_size
            
            if chunk_size < 1000:  # Less than 1KB indicates potential issue
                print(f"⚠️ Small chunk detected: {chunk_file} ({chunk_size} bytes)")
        
        print(f"✅ Generated {len(chunk_files)} audio chunks")
        print(f"✅ Total size: {total_size:,} bytes")
        print(f"✅ Average chunk size: {total_size // len(chunk_files):,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced stitching test failed: {str(e)}")
        return False

def test_single_request_fallback():
    """Test single-request fallback mode."""
    print("\\n🧪 Testing Single-Request Fallback")
    print("=" * 50)
    
    try:
        # Test segments for single request
        test_segments = [
            {
                "start": 0.0,
                "end": 2.5,
                "text_translated": "यह single request mode का test है।"
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text_translated": "सभी segments एक साथ process होते हैं।"
            },
            {
                "start": 5.0,
                "end": 7.5,
                "text_translated": "यह better consistency देता है।"
            }
        ]
        
        # Initialize service
        config = EdgeTTSConfig(
            voice_name="hi-IN-SwaraNeural",
            language="hi"
        )
        
        service = EnhancedEdgeTTSService(config)
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"[{progress*100:5.1f}%] {message}")
        
        # Test single request mode
        single_audio = service.generate_single_request_tts(test_segments, progress_callback)
        
        if not single_audio or not os.path.exists(single_audio):
            print("❌ Single request TTS generation failed")
            return False
        
        # Verify output
        file_size = os.path.getsize(single_audio)
        
        if file_size < 5000:  # Less than 5KB indicates potential issue
            print(f"⚠️ Small single request file: {file_size} bytes")
            return False
        
        print(f"✅ Single request TTS completed")
        print(f"✅ Output file: {single_audio}")
        print(f"✅ File size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Single request fallback test failed: {str(e)}")
        return False

def test_comprehensive_logging():
    """Test comprehensive logging and analytics."""
    print("\\n🧪 Testing Comprehensive Logging")
    print("=" * 50)
    
    try:
        # Test segments with various characteristics
        test_segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "text_translated": "छोटा segment।"  # Short segment
            },
            {
                "start": 2.0,
                "end": 8.0,
                "text_translated": "यह एक लंबा segment है जो अधिक समय तक चलता है और अधिक text content रखता है।"  # Long segment
            },
            {
                "start": 8.0,
                "end": 9.5,
                "text_translated": "मध्यम segment।"  # Medium segment
            }
        ]
        
        # Initialize service
        config = EdgeTTSConfig(
            voice_name="hi-IN-MadhurNeural",
            language="hi"
        )
        
        service = EnhancedEdgeTTSService(config)
        
        # Capture logging output
        import io
        import sys
        from contextlib import redirect_stdout
        
        log_capture = io.StringIO()
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            log_capture.write(f"[{progress*100:5.1f}%] {message}\\n")
        
        # Test with logging capture
        with redirect_stdout(log_capture):
            chunks_dir = service.generate_tts_chunks(test_segments, progress_callback)
        
        log_output = log_capture.getvalue()
        
        # Verify logging contains expected elements
        expected_log_elements = [
            "Segment timing:",
            "drift:",
            "speed:",
            "Final duration:",
            "Edge TTS Stitching Summary",
            "Average drift:",
            "Max drift:"
        ]
        
        missing_elements = []
        for element in expected_log_elements:
            if element not in log_output:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing log elements: {missing_elements}")
            return False
        
        print("✅ Comprehensive logging verified")
        print("✅ All expected log elements present")
        print(f"✅ Log output length: {len(log_output)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive logging test failed: {str(e)}")
        return False

def test_gradio_ui_compatibility():
    """Test compatibility with Gradio UI dropdowns."""
    print("\\n🧪 Testing Gradio UI Compatibility")
    print("=" * 50)
    
    try:
        parser = EdgeTTSVoiceParser()
        
        if not parser.parse_voices():
            print("❌ Failed to parse voices")
            return False
        
        # Test language dropdown data
        languages = parser.get_languages()
        
        if not languages:
            print("❌ No languages found for dropdown")
            return False
        
        # Verify language structure
        for lang in languages[:3]:  # Test first 3
            required_keys = ['code', 'name', 'voice_count']
            for key in required_keys:
                if key not in lang:
                    print(f"❌ Language missing key: {key}")
                    return False
        
        # Test voice dropdown data for specific languages
        test_languages = ['hi', 'en', 'es']
        
        for lang_code in test_languages:
            voice_choices = parser.get_voice_choices_for_language(lang_code)
            
            if not voice_choices:
                print(f"❌ No voice choices for language: {lang_code}")
                return False
            
            # Test voice name conversion
            first_voice = voice_choices[0]
            short_name = parser.get_voice_short_name(first_voice, lang_code)
            
            if not short_name:
                print(f"❌ Failed to get short name for: {first_voice}")
                return False
            
            print(f"✅ {lang_code}: {len(voice_choices)} voices, first: {first_voice} -> {short_name}")
        
        print("✅ Gradio UI compatibility verified")
        return True
        
    except Exception as e:
        print(f"❌ Gradio UI compatibility test failed: {str(e)}")
        return False

def run_complete_integration_test():
    """Run complete integration test suite."""
    print("🚀 Edge TTS Complete Integration Test")
    print("=" * 60)
    
    tests = [
        ("Voice Database Integration", test_voice_database_integration),
        ("Enhanced Audio Stitching", test_enhanced_stitching),
        ("Single-Request Fallback", test_single_request_fallback),
        ("Comprehensive Logging", test_comprehensive_logging),
        ("Gradio UI Compatibility", test_gradio_ui_compatibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 Integration Test Results")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests PASSED! Edge TTS is ready for production.")
        return True
    else:
        print("⚠️ Some tests FAILED. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_complete_integration_test()
    
    if success:
        print("\\n✅ Edge TTS Integration Test Suite PASSED!")
        exit(0)
    else:
        print("\\n❌ Edge TTS Integration Test Suite FAILED!")
        exit(1)