#!/usr/bin/env python3
"""
Kokoro TTS Voice Parser
Parses Kokoro TTS voice metadata and provides language/voice selection functionality.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class KokoroVoice:
    """Data class for Kokoro TTS voice information."""
    name: str
    language: str
    lang_code: str
    gender: str
    traits: str
    grade: str
    display_name: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'language': self.language,
            'lang_code': self.lang_code,
            'gender': self.gender,
            'traits': self.traits,
            'grade': self.grade,
            'display_name': self.display_name
        }

class KokoroVoiceParser:
    """Parser for Kokoro TTS voices."""
    
    def __init__(self):
        """Initialize parser with voice data."""
        self.voices: List[KokoroVoice] = []
        self.voices_by_language: Dict[str, List[KokoroVoice]] = {}
        self.language_names: Dict[str, str] = {}
        
        # Language mapping
        self.language_mapping = {
            'a': 'American English',
            'b': 'British English', 
            'j': 'Japanese',
            'z': 'Mandarin Chinese',
            'e': 'Spanish',
            'f': 'French',
            'h': 'Hindi',
            'i': 'Italian',
            'p': 'Brazilian Portuguese'
        }
        
        # Initialize voice data
        self._initialize_voices()
    
    def _initialize_voices(self):
        """Initialize voice data from hardcoded information."""
        voice_data = [
            # American English
            ('af_heart', 'a', 'American English', '🚺❤️', 'A'),
            ('af_alloy', 'a', 'American English', '🚺', 'C'),
            ('af_aoede', 'a', 'American English', '🚺', 'C+'),
            ('af_bella', 'a', 'American English', '🚺🔥', 'A-'),
            ('af_jessica', 'a', 'American English', '🚺', 'D'),
            ('af_kore', 'a', 'American English', '🚺', 'C+'),
            ('af_nicole', 'a', 'American English', '🚺🎧', 'B-'),
            ('af_nova', 'a', 'American English', '🚺', 'C'),
            ('af_river', 'a', 'American English', '🚺', 'D'),
            ('af_sarah', 'a', 'American English', '🚺', 'C+'),
            ('af_sky', 'a', 'American English', '🚺', 'C-'),
            ('am_adam', 'a', 'American English', '🚹', 'F+'),
            ('am_echo', 'a', 'American English', '🚹', 'D'),
            ('am_eric', 'a', 'American English', '🚹', 'D'),
            ('am_fenrir', 'a', 'American English', '🚹', 'C+'),
            ('am_liam', 'a', 'American English', '🚹', 'D'),
            ('am_michael', 'a', 'American English', '🚹', 'C+'),
            ('am_onyx', 'a', 'American English', '🚹', 'D'),
            ('am_puck', 'a', 'American English', '🚹', 'C+'),
            ('am_santa', 'a', 'American English', '🚹', 'D-'),
            
            # British English
            ('bf_alice', 'b', 'British English', '🚺', 'D'),
            ('bf_emma', 'b', 'British English', '🚺', 'B-'),
            ('bf_isabella', 'b', 'British English', '🚺', 'C'),
            ('bf_lily', 'b', 'British English', '🚺', 'D'),
            ('bm_daniel', 'b', 'British English', '🚹', 'D'),
            ('bm_fable', 'b', 'British English', '🚹', 'C'),
            ('bm_george', 'b', 'British English', '🚹', 'C'),
            ('bm_lewis', 'b', 'British English', '🚹', 'D+'),
            
            # Japanese
            ('jf_alpha', 'j', 'Japanese', '🚺', 'C+'),
            ('jf_gongitsune', 'j', 'Japanese', '🚺', 'C'),
            ('jf_nezumi', 'j', 'Japanese', '🚺', 'C-'),
            ('jf_tebukuro', 'j', 'Japanese', '🚺', 'C'),
            ('jm_kumo', 'j', 'Japanese', '🚹', 'C-'),
            
            # Mandarin Chinese
            ('zf_xiaobei', 'z', 'Mandarin Chinese', '🚺', 'D'),
            ('zf_xiaoni', 'z', 'Mandarin Chinese', '🚺', 'D'),
            ('zf_xiaoxiao', 'z', 'Mandarin Chinese', '🚺', 'D'),
            ('zf_xiaoyi', 'z', 'Mandarin Chinese', '🚺', 'D'),
            ('zm_yunjian', 'z', 'Mandarin Chinese', '🚹', 'D'),
            ('zm_yunxi', 'z', 'Mandarin Chinese', '🚹', 'D'),
            ('zm_yunxia', 'z', 'Mandarin Chinese', '🚹', 'D'),
            ('zm_yunyang', 'z', 'Mandarin Chinese', '🚹', 'D'),
            
            # Spanish
            ('ef_dora', 'e', 'Spanish', '🚺', 'C'),
            ('em_alex', 'e', 'Spanish', '🚹', 'C'),
            ('em_santa', 'e', 'Spanish', '🚹', 'C'),
            
            # French
            ('ff_siwis', 'f', 'French', '🚺', 'B-'),
            
            # Hindi
            ('hf_alpha', 'h', 'Hindi', '🚺', 'C'),
            ('hf_beta', 'h', 'Hindi', '🚺', 'C'),
            ('hm_omega', 'h', 'Hindi', '🚹', 'C'),
            ('hm_psi', 'h', 'Hindi', '🚹', 'C'),
            
            # Italian
            ('if_sara', 'i', 'Italian', '🚺', 'C'),
            ('im_nicola', 'i', 'Italian', '🚹', 'C'),
            
            # Brazilian Portuguese
            ('pf_dora', 'p', 'Brazilian Portuguese', '🚺', 'C'),
            ('pm_alex', 'p', 'Brazilian Portuguese', '🚹', 'C'),
            ('pm_santa', 'p', 'Brazilian Portuguese', '🚹', 'C'),
        ]
        
        # Create voice objects
        for name, lang_code, language, traits, grade in voice_data:
            gender = 'Female' if '🚺' in traits else 'Male'
            display_name = f"{name} ({gender}) - Grade {grade}"
            
            voice = KokoroVoice(
                name=name,
                language=language,
                lang_code=lang_code,
                gender=gender,
                traits=traits,
                grade=grade,
                display_name=display_name
            )
            
            self.voices.append(voice)
        
        # Organize by language
        self._organize_by_language()
    
    def _organize_by_language(self):
        """Organize voices by language."""
        self.voices_by_language = {}
        self.language_names = {}
        
        for voice in self.voices:
            lang_key = voice.lang_code
            
            if lang_key not in self.voices_by_language:
                self.voices_by_language[lang_key] = []
                self.language_names[lang_key] = voice.language
            
            self.voices_by_language[lang_key].append(voice)
        
        # Sort voices within each language by grade (best first)
        grade_order = {'A': 1, 'A-': 2, 'B': 3, 'B-': 4, 'C+': 5, 'C': 6, 'C-': 7, 'D+': 8, 'D': 9, 'D-': 10, 'F+': 11}
        
        for lang_key in self.voices_by_language:
            self.voices_by_language[lang_key].sort(
                key=lambda v: (grade_order.get(v.grade, 99), v.gender, v.name)
            )
    
    def get_languages(self) -> List[Dict[str, str]]:
        """Get list of available languages."""
        languages = []
        for lang_code, lang_name in self.language_names.items():
            languages.append({
                'code': lang_code,
                'name': lang_name,
                'voice_count': len(self.voices_by_language[lang_code])
            })
        
        # Sort by language name
        languages.sort(key=lambda x: x['name'])
        return languages
    
    def get_voices_for_language(self, language_code: str) -> List[Dict]:
        """Get voices for a specific language."""
        voices = self.voices_by_language.get(language_code, [])
        return [voice.to_dict() for voice in voices]
    
    def get_voice_choices_for_language(self, language_code: str) -> List[str]:
        """Get voice choices for Gradio dropdown."""
        voices = self.get_voices_for_language(language_code)
        choices = []
        
        for voice in voices:
            choices.append(voice['display_name'])
        
        return choices
    
    def get_voice_name_from_display(self, display_name: str, language_code: str) -> str:
        """Get voice name from display name."""
        voices = self.get_voices_for_language(language_code)
        
        for voice in voices:
            if voice['display_name'] == display_name:
                return voice['name']
        
        return display_name.split(' ')[0]  # Fallback
    
    def find_voice_by_name(self, voice_name: str) -> Optional[Dict]:
        """Find voice by name."""
        for voice in self.voices:
            if voice.name == voice_name:
                return voice.to_dict()
        return None
    
    def get_best_voices_by_language(self) -> Dict[str, str]:
        """Get the best voice for each language."""
        best_voices = {}
        
        for lang_code, voices in self.voices_by_language.items():
            if voices:
                # First voice is the best (sorted by grade)
                best_voices[lang_code] = voices[0].name
        
        return best_voices
    
    def get_language_from_voice(self, voice_name: str) -> Optional[str]:
        """Get language code from voice name."""
        for voice in self.voices:
            if voice.name == voice_name:
                return voice.lang_code
        return None
    
    def get_all_voices(self) -> List[Dict]:
        """Get all voices in a simple format for dropdown."""
        all_voices = []
        for voice in self.voices:
            all_voices.append({
                'name': voice.name,
                'language': voice.language,
                'lang_code': voice.lang_code,
                'gender': voice.gender,
                'grade': voice.grade
            })
        return all_voices

def test_kokoro_voice_parser():
    """Test the Kokoro voice parser."""
    print("🧪 Testing Kokoro Voice Parser")
    print("=" * 50)
    
    try:
        parser = KokoroVoiceParser()
        
        # Test language listing
        languages = parser.get_languages()
        print(f"✅ Found {len(languages)} languages")
        
        for lang in languages[:5]:  # Show first 5
            print(f"  • {lang['name']} ({lang['code']}): {lang['voice_count']} voices")
        
        # Test voice listing for specific languages
        test_languages = ['a', 'h', 'j']  # American English, Hindi, Japanese
        
        for lang_code in test_languages:
            lang_name = parser.language_names.get(lang_code, lang_code)
            voices = parser.get_voice_choices_for_language(lang_code)
            print(f"\n🎤 {lang_name} voices:")
            for voice in voices[:3]:  # Show first 3
                print(f"  • {voice}")
        
        # Test best voices
        best_voices = parser.get_best_voices_by_language()
        print(f"\n⭐ Best voices by language:")
        for lang_code, voice_name in list(best_voices.items())[:5]:
            lang_name = parser.language_names.get(lang_code, lang_code)
            print(f"  • {lang_name}: {voice_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_kokoro_voice_parser()
    print(f"\n{'✅ Kokoro Voice Parser test passed!' if success else '❌ Test failed!'}")