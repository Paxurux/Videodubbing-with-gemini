#!/usr/bin/env python3
"""
Quick test to verify Kokoro TTS method call fix
"""

def test_kokoro_voice_parsing():
    """Test the fixed Kokoro voice parsing"""
    try:
        from kokoro_voice_parser import KokoroVoiceParser
        
        parser = KokoroVoiceParser()
        
        # Test American English voices
        voices = parser.get_voice_choices_for_language("a")
        print(f"✅ Found {len(voices)} American English voices")
        
        if voices:
            # Test the fixed method call
            display_name = voices[0]
            voice_name = parser.get_voice_name_from_display(display_name, "a")
            print(f"✅ Voice parsing works: '{display_name}' -> '{voice_name}'")
            
            # Test with different language
            jp_voices = parser.get_voice_choices_for_language("j")
            if jp_voices:
                jp_display = jp_voices[0]
                jp_voice_name = parser.get_voice_name_from_display(jp_display, "j")
                print(f"✅ Japanese voice parsing: '{jp_display}' -> '{jp_voice_name}'")
            
            return True
        else:
            print("❌ No voices found")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_kokoro_service_init():
    """Test Kokoro service initialization"""
    try:
        from kokoro_tts_service import KokoroTTSService
        
        # Test with a known voice
        service = KokoroTTSService(voice_name="af_bella")
        print(f"✅ Kokoro service initialized: {service.voice_name}")
        print(f"   Model available: {service.model_available}")
        
        return True
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Kokoro TTS Fix")
    print("=" * 30)
    
    success = True
    
    print("\n1. Testing voice parsing:")
    if not test_kokoro_voice_parsing():
        success = False
    
    print("\n2. Testing service initialization:")
    if not test_kokoro_service_init():
        success = False
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 All tests passed! Kokoro TTS fix is working.")
    else:
        print("❌ Some tests failed.")