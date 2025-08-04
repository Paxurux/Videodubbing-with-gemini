#!/usr/bin/env python3
"""
Edge TTS Voice Parser
Parses the edgettsvoices.md file to extract voice information and organize by language.
"""

import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class EdgeVoice:
    """Data class for Edge TTS voice information."""
    name: str
    short_name: str
    gender: str
    locale: str
    language: str
    country: str
    voice_tag: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'short_name': self.short_name,
            'gender': self.gender,
            'locale': self.locale,
            'language': self.language,
            'country': self.country,
            'voice_tag': self.voice_tag
        }

class EdgeTTSVoiceParser:
    """Parser for Edge TTS voices from markdown file."""
    
    def __init__(self, voices_file: str = "edgettsvoices.md"):
        """Initialize parser with voices file."""
        self.voices_file = voices_file
        self.voices: List[EdgeVoice] = []
        self.voices_by_language: Dict[str, List[EdgeVoice]] = {}
        self.language_names: Dict[str, str] = {}
        
        # Language code to display name mapping
        self.language_display_names = {
            'af': 'Afrikaans',
            'sq': 'Albanian', 
            'am': 'Amharic',
            'ar': 'Arabic',
            'az': 'Azerbaijani',
            'bn': 'Bengali',
            'bs': 'Bosnian',
            'bg': 'Bulgarian',
            'my': 'Burmese',
            'ca': 'Catalan',
            'zh': 'Chinese',
            'hr': 'Croatian',
            'cs': 'Czech',
            'da': 'Danish',
            'nl': 'Dutch',
            'en': 'English',
            'et': 'Estonian',
            'fil': 'Filipino',
            'fi': 'Finnish',
            'fr': 'French',
            'de': 'German',
            'el': 'Greek',
            'gu': 'Gujarati',
            'he': 'Hebrew',
            'hi': 'Hindi',
            'hu': 'Hungarian',
            'is': 'Icelandic',
            'id': 'Indonesian',
            'ga': 'Irish',
            'it': 'Italian',
            'ja': 'Japanese',
            'jv': 'Javanese',
            'kn': 'Kannada',
            'kk': 'Kazakh',
            'km': 'Khmer',
            'ko': 'Korean',
            'lo': 'Lao',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'mk': 'Macedonian',
            'ms': 'Malay',
            'ml': 'Malayalam',
            'mt': 'Maltese',
            'mr': 'Marathi',
            'mn': 'Mongolian',
            'ne': 'Nepali',
            'nb': 'Norwegian',
            'ps': 'Pashto',
            'fa': 'Persian',
            'pl': 'Polish',
            'pt': 'Portuguese',
            'pa': 'Punjabi',
            'ro': 'Romanian',
            'ru': 'Russian',
            'sr': 'Serbian',
            'si': 'Sinhala',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'so': 'Somali',
            'es': 'Spanish',
            'su': 'Sundanese',
            'sw': 'Swahili',
            'sv': 'Swedish',
            'ta': 'Tamil',
            'te': 'Telugu',
            'th': 'Thai',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'ur': 'Urdu',
            'uz': 'Uzbek',
            'vi': 'Vietnamese',
            'cy': 'Welsh',
            'zu': 'Zulu'
        }
        
        # Country code to name mapping
        self.country_names = {
            'ZA': 'South Africa', 'AL': 'Albania', 'ET': 'Ethiopia', 'DZ': 'Algeria',
            'BH': 'Bahrain', 'EG': 'Egypt', 'IQ': 'Iraq', 'JO': 'Jordan',
            'KW': 'Kuwait', 'LB': 'Lebanon', 'LY': 'Libya', 'MA': 'Morocco',
            'OM': 'Oman', 'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SY': 'Syria',
            'TN': 'Tunisia', 'AE': 'UAE', 'YE': 'Yemen', 'AZ': 'Azerbaijan',
            'BD': 'Bangladesh', 'IN': 'India', 'BA': 'Bosnia', 'BG': 'Bulgaria',
            'MM': 'Myanmar', 'ES': 'Spain', 'HK': 'Hong Kong', 'CN': 'China',
            'TW': 'Taiwan', 'HR': 'Croatia', 'CZ': 'Czech Republic', 'DK': 'Denmark',
            'BE': 'Belgium', 'NL': 'Netherlands', 'AU': 'Australia', 'CA': 'Canada',
            'IE': 'Ireland', 'KE': 'Kenya', 'NZ': 'New Zealand', 'NG': 'Nigeria',
            'PH': 'Philippines', 'SG': 'Singapore', 'TZ': 'Tanzania', 'GB': 'United Kingdom',
            'US': 'United States', 'EE': 'Estonia', 'FI': 'Finland', 'FR': 'France',
            'CH': 'Switzerland', 'DE': 'Germany', 'GR': 'Greece', 'IL': 'Israel',
            'HU': 'Hungary', 'IS': 'Iceland', 'ID': 'Indonesia', 'IT': 'Italy',
            'JP': 'Japan', 'KZ': 'Kazakhstan', 'KH': 'Cambodia', 'KR': 'Korea',
            'LA': 'Laos', 'LV': 'Latvia', 'LT': 'Lithuania', 'MK': 'Macedonia',
            'MY': 'Malaysia', 'MT': 'Malta', 'MN': 'Mongolia', 'NP': 'Nepal',
            'NO': 'Norway', 'AF': 'Afghanistan', 'IR': 'Iran', 'PL': 'Poland',
            'BR': 'Brazil', 'PT': 'Portugal', 'RO': 'Romania', 'RU': 'Russia',
            'RS': 'Serbia', 'LK': 'Sri Lanka', 'SK': 'Slovakia', 'SI': 'Slovenia',
            'SO': 'Somalia', 'SE': 'Sweden', 'TH': 'Thailand', 'TR': 'Turkey',
            'UA': 'Ukraine', 'PK': 'Pakistan', 'UZ': 'Uzbekistan', 'VN': 'Vietnam',
            'CY': 'Cyprus'
        }
    
    def parse_voices(self) -> bool:
        """Parse voices from the markdown file."""
        try:
            with open(self.voices_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clear existing data
            self.voices.clear()
            self.voices_by_language.clear()
            
            # Split into voice entries (each voice is separated by blank lines)
            voice_entries = content.split('\n\n')
            
            for entry in voice_entries:
                if not entry.strip():
                    continue
                
                voice = self._parse_voice_entry(entry)
                if voice:
                    self.voices.append(voice)
            
            # Organize by language
            self._organize_by_language()
            
            print(f"✅ Parsed {len(self.voices)} Edge TTS voices from {self.voices_file}")
            print(f"📊 Found {len(self.voices_by_language)} languages")
            
            # Log some statistics
            for lang_code, voices in sorted(self.voices_by_language.items()):
                lang_name = self.language_display_names.get(lang_code, lang_code)
                print(f"   {lang_name} ({lang_code}): {len(voices)} voices")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to parse voices from {self.voices_file}: {str(e)}")
            return False
    
    def _parse_voice_entry(self, entry: str) -> Optional[EdgeVoice]:
        """Parse a single voice entry from markdown format."""
        try:
            lines = entry.strip().split('\n')
            
            voice_data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'VoiceTag':
                        # Parse the dictionary-like string safely
                        try:
                            # Replace single quotes with double quotes for JSON parsing
                            json_str = value.replace("'", '"')
                            voice_data[key] = json.loads(json_str)
                        except:
                            voice_data[key] = {}
                    else:
                        voice_data[key] = value
            
            # Extract required fields
            name = voice_data.get('Name', '')
            short_name = voice_data.get('ShortName', '')
            gender = voice_data.get('Gender', 'Unknown')
            locale = voice_data.get('Locale', '')
            voice_tag = voice_data.get('VoiceTag', {})
            
            if not short_name or not locale:
                return None
            
            # Extract language and country from locale (e.g., "en-US" -> "en", "US")
            if '-' in locale:
                language, country = locale.split('-', 1)
            else:
                language = locale
                country = ''
            
            return EdgeVoice(
                name=name,
                short_name=short_name,
                gender=gender,
                locale=locale,
                language=language.lower(),
                country=country.upper(),
                voice_tag=voice_tag
            )
            
        except Exception as e:
            print(f"⚠️ Failed to parse voice entry: {str(e)}")
            return None
    
    def _organize_by_language(self):
        """Organize voices by language."""
        self.voices_by_language = {}
        self.language_names = {}
        
        for voice in self.voices:
            lang_key = voice.language
            
            if lang_key not in self.voices_by_language:
                self.voices_by_language[lang_key] = []
                
                # Create display name
                lang_display = self.language_display_names.get(lang_key, lang_key.upper())
                if voice.country:
                    country_display = self.country_names.get(voice.country, voice.country)
                    lang_display = f"{lang_display} ({country_display})"
                
                self.language_names[lang_key] = lang_display
            
            self.voices_by_language[lang_key].append(voice)
        
        # Sort voices within each language by gender and name
        for lang_key in self.voices_by_language:
            self.voices_by_language[lang_key].sort(
                key=lambda v: (v.gender, v.short_name)
            )
    
    def get_languages(self) -> List[Dict[str, str]]:
        """Get list of available languages."""
        languages = []
        for lang_key, lang_name in sorted(self.language_names.items()):
            languages.append({
                'code': lang_key,
                'name': lang_name,
                'voice_count': len(self.voices_by_language[lang_key])
            })
        return languages
    
    def get_voice_choices_for_language(self, language_code: str) -> List[str]:
        """Get voice choices for Gradio dropdown for a specific language."""
        if not self.voices:
            self.parse_voices()
        
        voices = self.voices_by_language.get(language_code, [])
        choices = []
        
        for voice in voices:
            # Create display name: "VoiceName (Gender)"
            display_name = f"{voice.short_name.split('-')[-1]} ({voice.gender})"
            choices.append(display_name)
        
        return choices
    
    def get_voice_short_name(self, display_name: str, language_code: str) -> str:
        """Get the short name from display name for a specific language."""
        voices = self.voices_by_language.get(language_code, [])
        
        for voice in voices:
            voice_display = f"{voice.short_name.split('-')[-1]} ({voice.gender})"
            if voice_display == display_name:
                return voice.short_name
        
        # Fallback: return the first part of display name
        return display_name.split(' ')[0]
    
    def get_all_voices(self) -> List[Dict]:
        """Get all voices in a simple format for dropdown."""
        if not self.voices:
            self.parse_voices()
        
        all_voices = []
        for voice in self.voices:
            all_voices.append({
                'display_name': f"{voice.short_name} ({voice.gender})",
                'short_name': voice.short_name,
                'language': voice.language,
                'locale': voice.locale,
                'gender': voice.gender
            })
        
        return all_voices
    
    def get_language_voice_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of language codes to voice lists for dropdowns."""
        if not self.voices:
            self.parse_voices()
        
        mapping = {}
        for lang_code, voices in self.voices_by_language.items():
            voice_names = []
            for voice in voices:
                display_name = f"{voice.short_name.split('-')[-1]} ({voice.gender})"
                voice_names.append(display_name)
            mapping[lang_code] = voice_names
        
        return mapping
        
        # Sort by language name
        languages.sort(key=lambda x: x['name'])
        return languages
    
    def get_voices_for_language(self, language_code: str) -> List[Dict]:
        """Get voices for a specific language."""
        voices = self.voices_by_language.get(language_code.lower(), [])
        return [voice.to_dict() for voice in voices]
    
    def get_voice_choices_for_language(self, language_code: str) -> List[str]:
        """Get voice choices for Gradio dropdown."""
        voices = self.get_voices_for_language(language_code)
        choices = []
        
        for voice in voices:
            # Format: "Voice Name (Gender) - Short Name"
            display_name = f"{voice['short_name']} ({voice['gender']})"
            choices.append(display_name)
        
        return choices
    
    def get_voice_short_name(self, display_name: str, language_code: str) -> str:
        """Get short name from display name."""
        voices = self.get_voices_for_language(language_code)
        
        for voice in voices:
            expected_display = f"{voice['short_name']} ({voice['gender']})"
            if expected_display == display_name:
                return voice['short_name']
        
        return display_name  # Fallback
    
    def find_voice_by_short_name(self, short_name: str) -> Optional[Dict]:
        """Find voice by short name."""
        for voice in self.voices:
            if voice.short_name == short_name:
                return voice.to_dict()
        return None
    
    def get_all_voices(self) -> List[Dict]:
        """Get all voices in a simple format for dropdown."""
        all_voices = []
        for voice in self.voices:
            all_voices.append({
                'short_name': voice.short_name,
                'locale': voice.locale,
                'gender': voice.gender,
                'language': voice.language,
                'country': voice.country
            })
        return all_voices
    
    def get_popular_voices(self) -> Dict[str, str]:
        """Get popular voices for major languages."""
        popular = {}
        
        # Define popular voice preferences
        preferences = {
            'hi': ('Female', 'hi-IN-SwaraNeural'),  # Hindi
            'en': ('Female', 'en-US-AriaNeural'),   # English
            'es': ('Female', 'es-ES-ElviraNeural'), # Spanish
            'fr': ('Female', 'fr-FR-DeniseNeural'), # French
            'de': ('Female', 'de-DE-KatjaNeural'),  # German
            'ja': ('Female', 'ja-JP-NanamiNeural'), # Japanese
            'ko': ('Female', 'ko-KR-SunHiNeural'),  # Korean
            'zh': ('Female', 'zh-CN-XiaoxiaoNeural'), # Chinese
            'ar': ('Female', 'ar-SA-ZariyahNeural'), # Arabic
            'ta': ('Female', 'ta-IN-PallaviNeural'), # Tamil
            'te': ('Female', 'te-IN-ShrutiNeural'),  # Telugu
            'mr': ('Female', 'mr-IN-AarohiNeural'),  # Marathi
            'bn': ('Female', 'bn-IN-TanishaaNeural'), # Bengali
            'pt': ('Female', 'pt-BR-FranciscaNeural'), # Portuguese
            'ru': ('Female', 'ru-RU-SvetlanaNeural'), # Russian
            'it': ('Female', 'it-IT-ElsaNeural'),    # Italian
            'tr': ('Female', 'tr-TR-EmelNeural'),    # Turkish
            'th': ('Female', 'th-TH-PremwadeeNeural'), # Thai
            'vi': ('Female', 'vi-VN-HoaiMyNeural'),  # Vietnamese
            'nl': ('Female', 'nl-NL-ColetteNeural'), # Dutch
            'pl': ('Female', 'pl-PL-ZofiaNeural'),   # Polish
        }
        
        for lang_code, (preferred_gender, fallback_voice) in preferences.items():
            voices = self.voices_by_language.get(lang_code, [])
            
            if voices:
                # Try to find preferred gender first
                preferred_voice = None
                for voice in voices:
                    if voice.gender == preferred_gender:
                        preferred_voice = voice.short_name
                        break
                
                # Use preferred voice or fallback to first available
                popular[lang_code] = preferred_voice or voices[0].short_name
            else:
                # Use fallback if language not found
                popular[lang_code] = fallback_voice
        
        return popular
    
    def save_parsed_data(self, output_file: str = "edge_tts_voices.json"):
        """Save parsed voice data to JSON file."""
        try:
            data = {
                'languages': self.get_languages(),
                'voices_by_language': {
                    lang: [voice.to_dict() for voice in voices]
                    for lang, voices in self.voices_by_language.items()
                },
                'popular_voices': self.get_popular_voices(),
                'total_voices': len(self.voices),
                'total_languages': len(self.voices_by_language)
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved parsed data to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save data: {str(e)}")
            return False

# Test function
def test_voice_parser():
    """Test the voice parser."""
    print("🧪 Testing Edge TTS Voice Parser")
    print("=" * 60)
    
    try:
        parser = EdgeTTSVoiceParser()
        
        if not parser.parse_voices():
            print("❌ Failed to parse voices")
            return False
        
        # Test language listing
        languages = parser.get_languages()
        print(f"\n📋 Available Languages ({len(languages)}):")
        for lang in languages[:10]:  # Show first 10
            print(f"  • {lang['name']} ({lang['code']}) - {lang['voice_count']} voices")
        if len(languages) > 10:
            print(f"  ... and {len(languages) - 10} more")
        
        # Test Hindi voices
        print(f"\n🇮🇳 Hindi Voices:")
        hindi_voices = parser.get_voice_choices_for_language('hi')
        for voice in hindi_voices[:5]:  # Show first 5
            print(f"  • {voice}")
        
        # Test English voices
        print(f"\n🇺🇸 English Voices:")
        english_voices = parser.get_voice_choices_for_language('en')
        for voice in english_voices[:5]:  # Show first 5
            print(f"  • {voice}")
        
        # Test popular voices
        print(f"\n⭐ Popular Voices:")
        popular = parser.get_popular_voices()
        for lang, voice in list(popular.items())[:10]:
            lang_name = parser.language_names.get(lang, lang)
            print(f"  • {lang_name}: {voice}")
        
        # Save data
        parser.save_parsed_data()
        
        print(f"\n🎉 Voice parser test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_voice_parser()
    
    if success:
        print("\n✅ Edge TTS Voice Parser is working!")
    else:
        print("\n❌ Edge TTS Voice Parser test failed.")