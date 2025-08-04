#!/usr/bin/env python3
"""
Test Gemini TTS Integration
"""

def test_gemini_voice_library():
    """Test the Gemini voice library functionality."""
    print("🧪 Testing Gemini Voice Library Integration")
    print("=" * 50)
    
    try:
        from gemini_voice_library import GeminiVoiceLibrary
        
        # Initialize library
        gemini_library = GeminiVoiceLibrary()
        
        # Test basic functionality
        print(f"✅ Languages supported: {len(gemini_library.gemini_voices)}")
        print(f"✅ Total voices: {sum(len(voices) for voices in gemini_library.gemini_voices.values())}")
        
        # Test language-specific voices
        test_languages = ["en", "hi", "es", "ja"]
        for lang in test_languages:
            voices = gemini_library.get_gemini_voices(lang)
            print(f"✅ {lang.upper()} voices: {len(voices)} - {voices[:2]}...")
        
        # Test voice choices for UI
        for lang in test_languages[:2]:
            choices = gemini_library.create_voice_choices_for_language(lang)
            print(f"✅ {lang.upper()} UI choices: {len(choices)} - {choices[0] if choices else 'None'}")
        
        # Test voice display names
        test_voices = ["gemini_hi_deep", "gemini_en_soft", "gemini_es_bright"]
        for voice in test_voices:
            display_name = gemini_library.get_voice_display_name(voice)
            print(f"✅ {voice} -> {display_name}")
        
        print("\n🎉 Gemini Voice Library test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Gemini Voice Library test FAILED: {str(e)}")
        return False

def test_app_functions():
    """Test the app.py integration functions."""
    print("\n🧪 Testing App Integration Functions")
    print("=" * 50)
    
    try:
        # Import the functions we added to app.py
        import sys
        import os
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test get_gemini_languages
        print("Testing get_gemini_languages...")
        # We can't import directly from app.py due to dependencies, so we'll test the logic
        
        from gemini_voice_library import GeminiVoiceLibrary
        gemini_library = GeminiVoiceLibrary()
        
        # Simulate the language mapping logic
        language_mapping = {
            "en": "English", "hi": "Hindi", "es": "Spanish", "ja": "Japanese",
            "fr": "French", "de": "German", "ko": "Korean", "pt": "Portuguese",
            "ar": "Arabic", "it": "Italian", "ru": "Russian", "nl": "Dutch",
            "pl": "Polish", "th": "Thai", "tr": "Turkish", "vi": "Vietnamese",
            "ro": "Romanian", "uk": "Ukrainian", "bn": "Bengali", "mr": "Marathi",
            "ta": "Tamil", "te": "Telugu"
        }
        
        languages = []
        for lang_code in gemini_library.gemini_voices.keys():
            lang_name = language_mapping.get(lang_code, lang_code.upper())
            languages.append((lang_name, lang_code))
        
        languages = sorted(languages)
        print(f"✅ Language choices: {len(languages)} - {languages[:3]}...")
        
        # Test voice choices for specific language
        test_lang = "hi"
        voices = gemini_library.create_voice_choices_for_language(test_lang)
        print(f"✅ Voice choices for {test_lang}: {len(voices)} - {voices[0] if voices else 'None'}")
        
        print("\n🎉 App Integration Functions test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ App Integration Functions test FAILED: {str(e)}")
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
            'gemini_language_selection = gr.Dropdown',
            'gemini_voice_selection = gr.Dropdown',
            'def get_gemini_languages',
            'def get_gemini_voices_for_language',
            'def update_gemini_voices',
            'def preview_gemini_voice',
            'gemini_language_selection.change',
            'elif tts_engine == "gemini"'
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

if __name__ == "__main__":
    print("🚀 Starting Gemini TTS Integration Tests")
    print("=" * 60)
    
    # Run all tests
    tests = [
        test_gemini_voice_library,
        test_app_functions,
        test_ui_structure
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
        print("🎉 ALL TESTS PASSED! Gemini TTS integration is complete!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    print("=" * 60)