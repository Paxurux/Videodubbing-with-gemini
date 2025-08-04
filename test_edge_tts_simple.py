#!/usr/bin/env python3
"""
Simple Edge TTS Test
Tests the core functionality without requiring FFmpeg.
"""

import os
import json
from edge_tts_voice_parser import EdgeTTSVoiceParser
from enhanced_edge_tts_service import EnhancedEdgeTTSService, EdgeTTSConfig

def test_voice_parser_only():
    """Test just the voice parser functionality."""
    print("🧪 Testing Voice Parser Only")
    print("=" * 40)
    
    try:
        parser = EdgeTTSVoiceParser()
        
        if not parser.parse_voices():
            print("❌ Failed to parse voices")
            return False
        
        print(f"✅ Parsed {len(parser.voices)} voices")
        print(f"✅ Found {len(parser.voices_by_language)} languages")
        
        # Test Hindi voices
        hindi_voices = parser.get_voice_choices_for_language('hi')
        print(f"✅ Hindi voices: {len(hindi_voices)}")
        for voice in hindi_voices:
            print(f"  • {voice}")
        
        # Test English voices (first 3)
        english_voices = parser.get_voice_choices_for_language('en')
        print(f"✅ English voices: {len(english_voices)} (showing first 3)")
        for voice in english_voices[:3]:
            print(f"  • {voice}")
        
        # Test voice lookup
        test_voice = "hi-IN-MadhurNeural"
        voice_info = parser.find_voice_by_short_name(test_voice)
        
        if voice_info:
            print(f"✅ Voice lookup: {voice_info['name']} ({voice_info['gender']})")
        else:
            print(f"❌ Voice lookup failed for: {test_voice}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Voice parser test failed: {str(e)}")
        return False

def test_edge_tts_initialization():
    """Test Edge TTS service initialization."""
    print("\\n🧪 Testing Edge TTS Initialization")
    print("=" * 40)
    
    try:
        config = EdgeTTSConfig(
            voice_name="hi-IN-MadhurNeural",
            language="hi"
        )
        
        service = EnhancedEdgeTTSService(config)
        
        print(f"✅ Service initialized")
        print(f"✅ Voice: {service.config.voice_name}")
        print(f"✅ Language: {service.config.language}")
        
        # Test voice info
        voice_info = service.get_voice_info()
        print(f"✅ Voice info: {voice_info['name']} ({voice_info['gender']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge TTS initialization failed: {str(e)}")
        return False

def test_gradio_compatibility():
    """Test Gradio dropdown compatibility."""
    print("\\n🧪 Testing Gradio Compatibility")
    print("=" * 40)
    
    try:
        parser = EdgeTTSVoiceParser()
        parser.parse_voices()
        
        # Test language mapping
        language_mapping = parser.get_language_voice_mapping()
        
        print(f"✅ Language mapping: {len(language_mapping)} languages")
        
        # Test specific languages for dropdowns
        test_languages = ['hi', 'en', 'es', 'fr']
        
        for lang in test_languages:
            voices = language_mapping.get(lang, [])
            if voices:
                print(f"✅ {lang}: {len(voices)} voices")
                print(f"   First voice: {voices[0]}")
                
                # Test voice name conversion
                short_name = parser.get_voice_short_name(voices[0], lang)
                print(f"   Short name: {short_name}")
            else:
                print(f"❌ {lang}: No voices found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gradio compatibility test failed: {str(e)}")
        return False

def test_segment_validation():
    """Test segment validation without audio generation."""
    print("\\n🧪 Testing Segment Validation")
    print("=" * 40)
    
    try:
        config = EdgeTTSConfig(
            voice_name="hi-IN-SwaraNeural",
            language="hi"
        )
        
        service = EnhancedEdgeTTSService(config)
        
        # Test valid segments
        valid_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text_translated": "यह एक valid segment है।"
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text_translated": "दूसरा segment भी valid है।"
            }
        ]
        
        if service._validate_translated_segments(valid_segments):
            print("✅ Valid segments passed validation")
        else:
            print("❌ Valid segments failed validation")
            return False
        
        # Test invalid segments
        invalid_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                # Missing text_translated
            },
            {
                "start": 6.0,  # Invalid timing
                "end": 3.0,
                "text_translated": "Invalid timing"
            }
        ]
        
        if not service._validate_translated_segments(invalid_segments):
            print("✅ Invalid segments correctly rejected")
        else:
            print("❌ Invalid segments incorrectly accepted")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Segment validation test failed: {str(e)}")
        return False

def test_time_parsing():
    """Test time parsing functionality."""
    print("\\n🧪 Testing Time Parsing")
    print("=" * 40)
    
    try:
        config = EdgeTTSConfig(
            voice_name="en-US-AriaNeural",
            language="en"
        )
        
        service = EnhancedEdgeTTSService(config)
        
        # Test various time formats
        test_cases = [
            (0.0, 0.0),
            (5.5, 5.5),
            ("10.25", 10.25),
            ("1:30", 90.0),  # 1 minute 30 seconds
            ("0:05.5", 5.5),  # 5.5 seconds
        ]
        
        for input_time, expected in test_cases:
            result = service._parse_time(input_time)
            if abs(result - expected) < 0.01:  # Allow small floating point differences
                print(f"✅ {input_time} -> {result}s (expected {expected}s)")
            else:
                print(f"❌ {input_time} -> {result}s (expected {expected}s)")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Time parsing test failed: {str(e)}")
        return False

def run_simple_tests():
    """Run simple tests that don't require audio generation."""
    print("🚀 Edge TTS Simple Test Suite")
    print("=" * 50)
    
    tests = [
        ("Voice Parser", test_voice_parser_only),
        ("Edge TTS Initialization", test_edge_tts_initialization),
        ("Gradio Compatibility", test_gradio_compatibility),
        ("Segment Validation", test_segment_validation),
        ("Time Parsing", test_time_parsing)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 Simple Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All simple tests PASSED! Core functionality is working.")
        return True
    else:
        print("⚠️ Some tests FAILED. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    
    if success:
        print("\\n✅ Edge TTS Simple Test Suite PASSED!")
        print("💡 Note: Audio generation tests require FFmpeg installation")
        exit(0)
    else:
        print("\\n❌ Edge TTS Simple Test Suite FAILED!")
        exit(1)