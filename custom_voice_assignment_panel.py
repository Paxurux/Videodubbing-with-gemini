#!/usr/bin/env python3
"""
Custom Voice Assignment Panel
Dynamic panel for assigning voices to translated languages with custom voice support.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import traceback

class CustomVoiceAssignmentPanel:
    """Manages custom voice assignments with dynamic UI support."""
    
    def __init__(self):
        """Initialize the voice assignment panel."""
        self.custom_voices_dir = Path("custom_voices")
        self.custom_voices_dir.mkdir(exist_ok=True)
        
        self.voice_assignments_file = "voice_assignments.json"
        self.translations_dir = Path("translations")
        
        # Initialize available voices database
        self.available_voices = self._load_available_voices()
        
    def _load_available_voices(self) -> Dict[str, Dict[str, List[str]]]:
        """Load comprehensive available voices database."""
        # Load Gemini voices from library
        try:
            from gemini_voice_library import GeminiVoiceLibrary
            gemini_library = GeminiVoiceLibrary()
            gemini_voices_dict = gemini_library.gemini_voices
        except Exception as e:
            print(f"⚠️ Error loading Gemini voice library: {str(e)}")
            # Fallback to basic Gemini voices
            gemini_voices_dict = {
                "en": ["gemini_en_soft", "gemini_en_deep", "gemini_en_natural"],
                "hi": ["gemini_hi_deep", "gemini_hi_soft", "gemini_hi_natural"],
                "es": ["gemini_es_soft", "gemini_es_deep", "gemini_es_natural"]
            }
        
        return {
            "gemini": gemini_voices_dict,
            "edge": {
                # Edge TTS voices (comprehensive list)
                "en": ["en-US-AriaNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-US-JennyNeural"],
                "hi": ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
                "es": ["es-US-AlonsoNeural", "es-US-PalomaNeural", "es-ES-AlvaroNeural", "es-ES-ElviraNeural"],
                "ja": ["ja-JP-KeitaNeural", "ja-JP-NanamiNeural"],
                "fr": ["fr-FR-DeniseNeural", "fr-FR-EloiseNeural", "fr-FR-HenriNeural", "fr-FR-YvesNeural"],
                "de": ["de-DE-AmalaNeural", "de-DE-ConradNeural", "de-DE-KatjaNeural", "de-DE-KillianNeural"],
                "ko": ["ko-KR-InJoonNeural", "ko-KR-SunHiNeural"],
                "pt": ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural"],
                "ar": ["ar-EG-SalmaNeural", "ar-EG-ShakirNeural"],
                "it": ["it-IT-DiegoNeural", "it-IT-ElsaNeural", "it-IT-IsabellaNeural"],
                "ru": ["ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"],
                "nl": ["nl-NL-ColetteNeural", "nl-NL-FennaNeural", "nl-NL-MaartenNeural"],
                "pl": ["pl-PL-MarekNeural", "pl-PL-ZofiaNeural"],
                "th": ["th-TH-NiwatNeural", "th-TH-PremwadeeNeural"],
                "tr": ["tr-TR-AhmetNeural", "tr-TR-EmelNeural"],
                "vi": ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"],
                "ro": ["ro-RO-AlinaNeural", "ro-RO-EmilNeural"],
                "uk": ["uk-UA-OstapNeural", "uk-UA-PolinaNeural"],
                "bn": ["bn-BD-NabanitaNeural", "bn-BD-PradeepNeural"],
                "mr": ["mr-IN-AarohiNeural", "mr-IN-ManoharNeural"],
                "ta": ["ta-IN-PallaviNeural", "ta-IN-ValluvarNeural"],
                "te": ["te-IN-MohanNeural", "te-IN-ShrutiNeural"]
            },
            "kokoro": {
                # Kokoro TTS voices
                "en": ["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael"],
                "ja": ["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael", "jf_alpha", "jm_beta"],
                "ko": ["af_heart", "af_bella"],
                "zh": ["af_heart", "af_bella"]
            },
            "custom": {}  # Will be populated with uploaded voices
        }
    
    def get_detected_languages(self) -> Dict[str, str]:
        """Get detected translated languages from translation files."""
        detected_languages = {}
        
        if not self.translations_dir.exists():
            return detected_languages
        
        try:
            # Language code to name mapping
            language_names = {
                "ar-EG": "Arabic (Egyptian)",
                "de-DE": "German (Germany)",
                "es-US": "Spanish (US)",
                "fr-FR": "French (France)",
                "hi-IN": "Hindi (India)",
                "id-ID": "Indonesian (Indonesia)",
                "it-IT": "Italian (Italy)",
                "ja-JP": "Japanese (Japan)",
                "ko-KR": "Korean (Korea)",
                "pt-BR": "Portuguese (Brazil)",
                "ru-RU": "Russian (Russia)",
                "nl-NL": "Dutch (Netherlands)",
                "pl-PL": "Polish (Poland)",
                "th-TH": "Thai (Thailand)",
                "tr-TR": "Turkish (Turkey)",
                "vi-VN": "Vietnamese (Vietnam)",
                "ro-RO": "Romanian (Romania)",
                "uk-UA": "Ukrainian (Ukraine)",
                "bn-BD": "Bengali (Bangladesh)",
                "en-US": "English (US)",
                "en-IN": "English (India)",
                "mr-IN": "Marathi (India)",
                "ta-IN": "Tamil (India)",
                "te-IN": "Telugu (India)"
            }
            
            # Scan translation files
            for json_file in self.translations_dir.glob("transcript_*.json"):
                lang_code = json_file.stem.replace("transcript_", "")
                if lang_code != "original":
                    # Convert full language codes to simple codes for voice matching
                    simple_code = self._get_simple_language_code(lang_code)
                    language_name = language_names.get(lang_code, lang_code.upper())
                    detected_languages[simple_code] = language_name
            
            return detected_languages
            
        except Exception as e:
            print(f"❌ Error detecting languages: {str(e)}")
            return {}
    
    def _get_simple_language_code(self, full_code: str) -> str:
        """Convert full language code to simple code for voice matching."""
        # Map full codes to simple codes
        code_mapping = {
            "ar-EG": "ar", "de-DE": "de", "es-US": "es", "fr-FR": "fr",
            "hi-IN": "hi", "id-ID": "id", "it-IT": "it", "ja-JP": "ja",
            "ko-KR": "ko", "pt-BR": "pt", "ru-RU": "ru", "nl-NL": "nl",
            "pl-PL": "pl", "th-TH": "th", "tr-TR": "tr", "vi-VN": "vi",
            "ro-RO": "ro", "uk-UA": "uk", "bn-BD": "bn", "en-US": "en",
            "en-IN": "en", "mr-IN": "mr", "ta-IN": "ta", "te-IN": "te"
        }
        return code_mapping.get(full_code, full_code.split("-")[0])
    
    def get_available_voices_for_language(self, lang_code: str) -> Dict[str, List[str]]:
        """Get all available voices for a specific language."""
        available = {}
        
        # Check each TTS engine
        for engine, voices in self.available_voices.items():
            if lang_code in voices and voices[lang_code]:
                available[engine] = voices[lang_code]
        
        # Add custom voices for this language
        custom_voices = self._get_custom_voices_for_language(lang_code)
        if custom_voices:
            available["custom"] = custom_voices
        
        return available
    
    def _get_custom_voices_for_language(self, lang_code: str) -> List[str]:
        """Get custom voices for a specific language."""
        custom_voices = []
        
        if not self.custom_voices_dir.exists():
            return custom_voices
        
        try:
            # Look for custom voice files for this language
            pattern = f"*{lang_code}*.wav"
            for voice_file in self.custom_voices_dir.glob(pattern):
                voice_name = voice_file.stem
                custom_voices.append(voice_name)
            
            # Also look for generic custom voices
            for voice_file in self.custom_voices_dir.glob("*.wav"):
                voice_name = voice_file.stem
                if voice_name not in custom_voices:
                    custom_voices.append(voice_name)
            
            return custom_voices
            
        except Exception as e:
            print(f"❌ Error getting custom voices for {lang_code}: {str(e)}")
            return []
    
    def create_voice_assignment_table_data(self) -> List[Dict[str, Any]]:
        """Create data for the voice assignment table."""
        detected_languages = self.get_detected_languages()
        table_data = []
        
        for lang_code, lang_name in detected_languages.items():
            # Get available voices for this language
            available_voices = self.get_available_voices_for_language(lang_code)
            
            # Create voice options list
            voice_options = []
            for engine, voices in available_voices.items():
                for voice in voices:
                    voice_options.append(f"{engine}:{voice}")
            
            # Get current assignment if exists
            current_assignments = self.load_voice_assignments()
            current_assignment = current_assignments.get(lang_code, {})
            current_voice = f"{current_assignment.get('engine', 'auto')}:{current_assignment.get('voice', 'auto')}"
            
            table_data.append({
                "language_code": lang_code,
                "language_name": lang_name,
                "voice_options": voice_options,
                "current_voice": current_voice if current_voice in voice_options else (voice_options[0] if voice_options else "none:none"),
                "available_engines": list(available_voices.keys())
            })
        
        return table_data
    
    def load_voice_assignments(self) -> Dict[str, Dict[str, str]]:
        """Load current voice assignments."""
        try:
            if os.path.exists(self.voice_assignments_file):
                with open(self.voice_assignments_file, "r", encoding="utf-8") as f:
                    assignments = json.load(f)
                    
                # Convert to simple language codes if needed
                simple_assignments = {}
                for lang_code, assignment in assignments.items():
                    simple_code = self._get_simple_language_code(lang_code)
                    simple_assignments[simple_code] = assignment
                
                return simple_assignments
            return {}
        except Exception as e:
            print(f"❌ Error loading voice assignments: {str(e)}")
            return {}
    
    def save_voice_assignments(self, assignments: Dict[str, Dict[str, str]]) -> bool:
        """Save voice assignments to file."""
        try:
            with open(self.voice_assignments_file, "w", encoding="utf-8") as f:
                json.dump(assignments, f, indent=2, ensure_ascii=False)
            print(f"✅ Voice assignments saved to {self.voice_assignments_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving voice assignments: {str(e)}")
            return False
    
    def upload_custom_voice(self, voice_file_path: str, language_code: str, voice_name: str) -> Tuple[bool, str]:
        """Upload a custom voice file."""
        try:
            if not voice_file_path:
                return False, "❌ No voice file provided"
            
            if not language_code.strip():
                return False, "❌ Language code is required"
            
            if not voice_name.strip():
                return False, "❌ Voice name is required"
            
            # Clean voice name (remove special characters)
            clean_voice_name = "".join(c for c in voice_name if c.isalnum() or c in "_-").strip()
            if not clean_voice_name:
                return False, "❌ Invalid voice name"
            
            # Create filename with language code
            filename = f"{clean_voice_name}_{language_code}.wav"
            destination = self.custom_voices_dir / filename
            
            # Copy the uploaded file
            shutil.copy2(voice_file_path, destination)
            
            # Update custom voices in available voices
            if language_code not in self.available_voices["custom"]:
                self.available_voices["custom"][language_code] = []
            
            voice_id = f"{clean_voice_name}_{language_code}"
            if voice_id not in self.available_voices["custom"][language_code]:
                self.available_voices["custom"][language_code].append(voice_id)
            
            return True, f"✅ Custom voice uploaded: {filename} ({destination.stat().st_size:,} bytes)"
            
        except Exception as e:
            error_msg = f"❌ Error uploading custom voice: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return False, error_msg
    
    def auto_assign_best_voices(self) -> Dict[str, Dict[str, str]]:
        """Automatically assign best available voices for each language."""
        detected_languages = self.get_detected_languages()
        auto_assignments = {}
        
        # Priority order: custom > gemini > edge > kokoro
        engine_priority = ["custom", "gemini", "edge", "kokoro"]
        
        for lang_code, lang_name in detected_languages.items():
            available_voices = self.get_available_voices_for_language(lang_code)
            
            # Find best engine and voice
            assigned = False
            for engine in engine_priority:
                if engine in available_voices and available_voices[engine]:
                    # Use first voice from highest priority engine
                    voice = available_voices[engine][0]
                    auto_assignments[lang_code] = {
                        "engine": engine,
                        "voice": voice,
                        "source": "auto_assigned"
                    }
                    assigned = True
                    break
            
            if not assigned:
                auto_assignments[lang_code] = {
                    "engine": "none",
                    "voice": "Voice Not Found",
                    "source": "auto_assigned"
                }
        
        return auto_assignments
    
    def generate_voice_preview_text(self, lang_code: str) -> str:
        """Generate preview text for a language."""
        preview_texts = {
            "en": "Hello world, this is a voice preview test.",
            "hi": "नमस्ते दुनिया, यह एक आवाज़ पूर्वावलोकन परीक्षण है।",
            "es": "Hola mundo, esta es una prueba de vista previa de voz.",
            "ja": "こんにちは世界、これは音声プレビューテストです。",
            "fr": "Bonjour le monde, ceci est un test d'aperçu vocal.",
            "de": "Hallo Welt, das ist ein Sprachvorschau-Test.",
            "ko": "안녕하세요 세계, 이것은 음성 미리보기 테스트입니다.",
            "pt": "Olá mundo, este é um teste de visualização de voz.",
            "ar": "مرحبا بالعالم، هذا اختبار معاينة صوتية.",
            "it": "Ciao mondo, questo è un test di anteprima vocale.",
            "ru": "Привет мир, это тест предварительного просмотра голоса.",
            "nl": "Hallo wereld, dit is een spraakvoorbeeld test.",
            "pl": "Witaj świecie, to jest test podglądu głosu.",
            "th": "สวัสดีชาวโลก นี่คือการทดสอบตัวอย่างเสียง",
            "tr": "Merhaba dünya, bu bir ses önizleme testidir.",
            "vi": "Xin chào thế giới, đây là bài kiểm tra xem trước giọng nói.",
            "ro": "Salut lume, acesta este un test de previzualizare vocală.",
            "uk": "Привіт світ, це тест попереднього перегляду голосу.",
            "bn": "হ্যালো বিশ্ব, এটি একটি ভয়েস প্রিভিউ টেস্ট।",
            "mr": "हॅलो जग, ही एक आवाज पूर्वावलोकन चाचणी आहे.",
            "ta": "வணக்கம் உலகம், இது ஒரு குரல் முன்னோட்ட சோதனை.",
            "te": "హలో వరల్డ్, ఇది వాయిస్ ప్రివ్యూ టెస్ట్."
        }
        
        return preview_texts.get(lang_code, f"Hello world in {lang_code}, this is a voice preview test.")
    
    def create_voice_assignment_summary(self, assignments: Dict[str, Dict[str, str]]) -> str:
        """Create a summary of voice assignments."""
        if not assignments:
            return "No voice assignments configured."
        
        summary_lines = [
            f"🎤 Voice Assignment Summary ({len(assignments)} languages):",
            "=" * 50
        ]
        
        detected_languages = self.get_detected_languages()
        
        for lang_code, assignment in assignments.items():
            lang_name = detected_languages.get(lang_code, lang_code.upper())
            engine = assignment.get("engine", "unknown")
            voice = assignment.get("voice", "unknown")
            source = assignment.get("source", "manual")
            
            if engine == "none":
                status = "❌ No Voice Available"
            elif source == "auto_assigned":
                status = f"🤖 Auto: {engine}:{voice}"
            elif engine == "custom":
                status = f"📁 Custom: {voice}"
            else:
                status = f"✅ {engine.title()}: {voice}"
            
            summary_lines.append(f"  {lang_name} ({lang_code}): {status}")
        
        return "\\n".join(summary_lines)

def test_custom_voice_assignment_panel():
    """Test the custom voice assignment panel."""
    print("🧪 Testing Custom Voice Assignment Panel")
    print("=" * 60)
    
    try:
        # Initialize panel
        panel = CustomVoiceAssignmentPanel()
        
        # Test detecting languages
        detected_languages = panel.get_detected_languages()
        print(f"✅ Detected {len(detected_languages)} languages: {list(detected_languages.keys())}")
        
        # Test getting available voices
        if detected_languages:
            test_lang = list(detected_languages.keys())[0]
            available_voices = panel.get_available_voices_for_language(test_lang)
            print(f"✅ Available voices for {test_lang}: {list(available_voices.keys())}")
        
        # Test creating table data
        table_data = panel.create_voice_assignment_table_data()
        print(f"✅ Created table data for {len(table_data)} languages")
        
        # Test auto assignment
        auto_assignments = panel.auto_assign_best_voices()
        print(f"✅ Auto-assigned voices for {len(auto_assignments)} languages")
        
        if auto_assignments:
            summary = panel.create_voice_assignment_summary(auto_assignments)
            print("\\n" + summary)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_custom_voice_assignment_panel()
    
    if success:
        print("\\n🎉 Custom Voice Assignment Panel test PASSED!")
    else:
        print("\\n❌ Custom Voice Assignment Panel test FAILED!")
    
    exit(0 if success else 1)