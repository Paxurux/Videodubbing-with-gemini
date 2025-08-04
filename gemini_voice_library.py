#!/usr/bin/env python3
"""
Gemini Voice Library
Comprehensive voice library for Gemini TTS with language-specific voices and preview functionality.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class GeminiVoiceLibrary:
    """Manages Gemini TTS voices with language-specific organization."""
    
    def __init__(self):
        """Initialize the Gemini voice library."""
        self.gemini_voices = self._load_gemini_voices()
        self.preview_texts = self._load_preview_texts()
        
    def _load_gemini_voices(self) -> Dict[str, List[str]]:
        """Load comprehensive Gemini voice library."""
        return {
            "en": [
                "gemini_en_soft",
                "gemini_en_deep", 
                "gemini_en_natural",
                "gemini_en_fast",
                "gemini_en_warm",
                "gemini_en_professional"
            ],
            "hi": [
                "gemini_hi_deep",
                "gemini_hi_female",
                "gemini_hi_soft",
                "gemini_hi_natural",
                "gemini_hi_warm"
            ],
            "es": [
                "gemini_es_bright",
                "gemini_es_soft",
                "gemini_es_deep",
                "gemini_es_natural",
                "gemini_es_warm"
            ],
            "ja": [
                "gemini_ja_soft",
                "gemini_ja_deep",
                "gemini_ja_natural",
                "gemini_ja_anime",
                "gemini_ja_professional"
            ],
            "fr": [
                "gemini_fr_soft",
                "gemini_fr_deep",
                "gemini_fr_natural",
                "gemini_fr_elegant",
                "gemini_fr_warm"
            ],
            "de": [
                "gemini_de_soft",
                "gemini_de_deep",
                "gemini_de_natural",
                "gemini_de_professional",
                "gemini_de_warm"
            ],
            "ko": [
                "gemini_ko_soft",
                "gemini_ko_deep",
                "gemini_ko_natural",
                "gemini_ko_cute",
                "gemini_ko_professional"
            ],
            "pt": [
                "gemini_pt_soft",
                "gemini_pt_deep",
                "gemini_pt_natural",
                "gemini_pt_warm",
                "gemini_pt_brazilian"
            ],
            "ar": [
                "gemini_ar_soft",
                "gemini_ar_deep",
                "gemini_ar_natural",
                "gemini_ar_classical",
                "gemini_ar_modern"
            ],
            "it": [
                "gemini_it_soft",
                "gemini_it_deep",
                "gemini_it_natural",
                "gemini_it_elegant",
                "gemini_it_warm"
            ],
            "ru": [
                "gemini_ru_soft",
                "gemini_ru_deep",
                "gemini_ru_natural",
                "gemini_ru_professional",
                "gemini_ru_warm"
            ],
            "nl": [
                "gemini_nl_soft",
                "gemini_nl_deep",
                "gemini_nl_natural",
                "gemini_nl_warm"
            ],
            "pl": [
                "gemini_pl_soft",
                "gemini_pl_deep",
                "gemini_pl_natural",
                "gemini_pl_warm"
            ],
            "th": [
                "gemini_th_soft",
                "gemini_th_deep",
                "gemini_th_natural",
                "gemini_th_traditional"
            ],
            "tr": [
                "gemini_tr_soft",
                "gemini_tr_deep",
                "gemini_tr_natural",
                "gemini_tr_warm"
            ],
            "vi": [
                "gemini_vi_soft",
                "gemini_vi_deep",
                "gemini_vi_natural",
                "gemini_vi_southern"
            ],
            "ro": [
                "gemini_ro_soft",
                "gemini_ro_deep",
                "gemini_ro_natural"
            ],
            "uk": [
                "gemini_uk_soft",
                "gemini_uk_deep",
                "gemini_uk_natural"
            ],
            "bn": [
                "gemini_bn_soft",
                "gemini_bn_deep",
                "gemini_bn_natural"
            ],
            "mr": [
                "gemini_mr_soft",
                "gemini_mr_deep",
                "gemini_mr_natural"
            ],
            "ta": [
                "gemini_ta_soft",
                "gemini_ta_deep",
                "gemini_ta_natural"
            ],
            "te": [
                "gemini_te_soft",
                "gemini_te_deep",
                "gemini_te_natural"
            ]
        }
    
    def _load_preview_texts(self) -> Dict[str, str]:
        """Load preview texts for each language."""
        return {
            "en": "Hello world, this is a Gemini TTS voice preview test.",
            "hi": "नमस्ते दुनिया, यह जेमिनी टीटीएस आवाज़ का पूर्वावलोकन है।",
            "es": "Hola mundo, esta es una prueba de vista previa de voz Gemini TTS.",
            "ja": "こんにちは世界、これはGemini TTSの音声プレビューテストです。",
            "fr": "Bonjour le monde, ceci est un test d'aperçu vocal Gemini TTS.",
            "de": "Hallo Welt, das ist ein Gemini TTS Sprachvorschau-Test.",
            "ko": "안녕하세요 세계, 이것은 Gemini TTS 음성 미리보기 테스트입니다.",
            "pt": "Olá mundo, este é um teste de visualização de voz Gemini TTS.",
            "ar": "مرحبا بالعالم، هذا اختبار معاينة صوت Gemini TTS.",
            "it": "Ciao mondo, questo è un test di anteprima vocale Gemini TTS.",
            "ru": "Привет мир, это тест предварительного просмотра голоса Gemini TTS.",
            "nl": "Hallo wereld, dit is een Gemini TTS spraakvoorbeeld test.",
            "pl": "Witaj świecie, to jest test podglądu głosu Gemini TTS.",
            "th": "สวัสดีชาวโลก นี่คือการทดสอบตัวอย่างเสียง Gemini TTS",
            "tr": "Merhaba dünya, bu bir Gemini TTS ses önizleme testidir.",
            "vi": "Xin chào thế giới, đây là bài kiểm tra xem trước giọng nói Gemini TTS.",
            "ro": "Salut lume, acesta este un test de previzualizare vocală Gemini TTS.",
            "uk": "Привіт світ, це тест попереднього перегляду голосу Gemini TTS.",
            "bn": "হ্যালো বিশ্ব, এটি একটি Gemini TTS ভয়েস প্রিভিউ টেস্ট।",
            "mr": "हॅलो जग, ही एक Gemini TTS आवाज पूर्वावलोकन चाचणी आहे.",
            "ta": "வணக்கம் உலகம், இது ஒரு Gemini TTS குரல் முன்னோட்ட சோதனை.",
            "te": "హలో వరల్డ్, ఇది Gemini TTS వాయిస్ ప్రివ్యూ టెస్ట్."
        }
    
    def get_gemini_voices(self, lang_code: str) -> List[str]:
        """Get available Gemini voices for a language."""
        return self.gemini_voices.get(lang_code, [])
    
    def get_gemini_languages(self) -> List[str]:
        """Get all languages supported by Gemini TTS."""
        return list(self.gemini_voices.keys())
    
    def get_preview_text(self, lang_code: str) -> str:
        """Get preview text for a language."""
        return self.preview_texts.get(lang_code, f"Hello world in {lang_code}, this is a Gemini TTS voice preview test.")
    
    def is_gemini_voice(self, voice_name: str) -> bool:
        """Check if a voice name is a Gemini voice."""
        return voice_name.startswith("gemini_")
    
    def get_voice_language(self, voice_name: str) -> Optional[str]:
        """Get the language code for a Gemini voice."""
        if not self.is_gemini_voice(voice_name):
            return None
        
        # Extract language from voice name (e.g., "gemini_hi_deep" -> "hi")
        parts = voice_name.split("_")
        if len(parts) >= 3:
            return parts[1]
        return None
    
    def get_voice_display_name(self, voice_name: str) -> str:
        """Get a user-friendly display name for a voice."""
        if not self.is_gemini_voice(voice_name):
            return voice_name
        
        # Convert "gemini_hi_deep" to "Hindi Deep (Gemini)"
        parts = voice_name.split("_")
        if len(parts) >= 3:
            lang_code = parts[1]
            voice_type = parts[2].title()
            
            # Language code to name mapping
            lang_names = {
                "en": "English", "hi": "Hindi", "es": "Spanish", "ja": "Japanese",
                "fr": "French", "de": "German", "ko": "Korean", "pt": "Portuguese",
                "ar": "Arabic", "it": "Italian", "ru": "Russian", "nl": "Dutch",
                "pl": "Polish", "th": "Thai", "tr": "Turkish", "vi": "Vietnamese",
                "ro": "Romanian", "uk": "Ukrainian", "bn": "Bengali", "mr": "Marathi",
                "ta": "Tamil", "te": "Telugu"
            }
            
            lang_name = lang_names.get(lang_code, lang_code.upper())
            return f"{lang_name} {voice_type} (Gemini)"
        
        return voice_name
    
    def create_voice_choices_for_language(self, lang_code: str) -> List[Tuple[str, str]]:
        """Create voice choices for Gradio dropdown for a specific language."""
        voices = self.get_gemini_voices(lang_code)
        choices = []
        
        for voice in voices:
            display_name = self.get_voice_display_name(voice)
            choices.append((display_name, voice))
        
        return choices
    
    def get_all_voice_choices(self) -> List[Tuple[str, str]]:
        """Get all Gemini voice choices for Gradio dropdown."""
        all_choices = []
        
        for lang_code in self.get_gemini_languages():
            lang_choices = self.create_voice_choices_for_language(lang_code)
            all_choices.extend(lang_choices)
        
        return all_choices
    
    def generate_gemini_tts_preview(self, voice_name: str, lang_code: str = None) -> Optional[str]:
        """Generate a TTS preview for a Gemini voice."""
        try:
            # Get language code if not provided
            if not lang_code:
                lang_code = self.get_voice_language(voice_name)
            
            if not lang_code:
                print(f"❌ Could not determine language for voice: {voice_name}")
                return None
            
            # Get preview text
            preview_text = self.get_preview_text(lang_code)
            
            # Generate TTS using Gemini service
            from api_key_manager import APIKeyManager
            from real_gemini_service import RealGeminiService
            
            # Check if API keys are available
            api_manager = APIKeyManager()
            if not api_manager.has_keys():
                print("❌ No Gemini API keys available for preview")
                return None
            
            # Initialize Gemini service
            api_keys = api_manager.get_keys()
            gemini_service = RealGeminiService(api_keys)
            
            # Create a temporary segment for TTS generation
            temp_segments = [{
                "start": 0.0,
                "end": 5.0,
                "text_translated": preview_text
            }]
            
            # Generate TTS
            def progress_callback(progress, message):
                print(f"[Gemini Preview {progress:.1%}] {message}")
            
            chunks_dir = gemini_service.generate_tts_chunks(
                temp_segments, voice_name, progress_callback
            )
            
            if chunks_dir and os.path.exists(chunks_dir):
                # Find the generated audio file
                chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
                if chunk_files:
                    preview_file = os.path.join(chunks_dir, chunk_files[0])
                    
                    # Create preview directory
                    preview_dir = Path("gemini_voice_previews")
                    preview_dir.mkdir(exist_ok=True)
                    
                    # Copy to preview location with consistent naming
                    final_preview_path = preview_dir / f"{voice_name}_preview.wav"
                    import shutil
                    shutil.copy2(preview_file, final_preview_path)
                    
                    print(f"✅ Generated Gemini preview: {final_preview_path}")
                    return str(final_preview_path)
            
            print(f"❌ Failed to generate Gemini preview for {voice_name}")
            return None
            
        except Exception as e:
            print(f"❌ Error generating Gemini preview: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_voice_library_config(self, filename: str = "gemini_voice_config.json"):
        """Save the voice library configuration to a JSON file."""
        try:
            config = {
                "gemini_voices": self.gemini_voices,
                "preview_texts": self.preview_texts,
                "metadata": {
                    "total_languages": len(self.gemini_voices),
                    "total_voices": sum(len(voices) for voices in self.gemini_voices.values()),
                    "version": "1.0"
                }
            }
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Gemini voice library saved to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving voice library: {str(e)}")
            return False
    
    def load_voice_library_config(self, filename: str = "gemini_voice_config.json") -> bool:
        """Load the voice library configuration from a JSON file."""
        try:
            if not os.path.exists(filename):
                print(f"⚠️ Config file not found: {filename}")
                return False
            
            with open(filename, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            if "gemini_voices" in config:
                self.gemini_voices = config["gemini_voices"]
            
            if "preview_texts" in config:
                self.preview_texts = config["preview_texts"]
            
            print(f"✅ Gemini voice library loaded from {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading voice library: {str(e)}")
            return False

def test_gemini_voice_library():
    """Test the Gemini voice library."""
    print("🧪 Testing Gemini Voice Library")
    print("=" * 50)
    
    try:
        # Initialize library
        library = GeminiVoiceLibrary()
        
        # Test basic functionality
        languages = library.get_gemini_languages()
        print(f"✅ Supported languages: {len(languages)}")
        print(f"Languages: {', '.join(languages[:10])}{'...' if len(languages) > 10 else ''}")
        
        # Test voice retrieval
        if languages:
            test_lang = languages[0]
            voices = library.get_gemini_voices(test_lang)
            print(f"✅ Voices for {test_lang}: {len(voices)}")
            print(f"Voices: {', '.join(voices)}")
        
        # Test voice choices
        all_choices = library.get_all_voice_choices()
        print(f"✅ Total voice choices: {len(all_choices)}")
        
        # Test preview text
        if languages:
            preview_text = library.get_preview_text(languages[0])
            print(f"✅ Preview text for {languages[0]}: {preview_text[:50]}...")
        
        # Test voice name parsing
        test_voice = "gemini_hi_deep"
        lang_code = library.get_voice_language(test_voice)
        display_name = library.get_voice_display_name(test_voice)
        print(f"✅ Voice parsing: {test_voice} -> {lang_code} -> {display_name}")
        
        # Save config
        library.save_voice_library_config()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_voice_library()
    
    if success:
        print("\\n🎉 Gemini Voice Library test PASSED!")
    else:
        print("\\n❌ Gemini Voice Library test FAILED!")
    
    exit(0 if success else 1)