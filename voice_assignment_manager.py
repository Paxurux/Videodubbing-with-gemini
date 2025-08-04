#!/usr/bin/env python3
"""
Voice Assignment Manager for Multi-Language TTS
Automatically detects and assigns voices from available TTS engines.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class VoiceAssignmentManager:
    """Manages automatic voice assignment for multi-language TTS."""
    
    def __init__(self):
        """Initialize the voice assignment manager."""
        self.voice_assignments_file = "voice_assignments.json"
        self.custom_voice_config_file = "custom_voice_mapping.json"
        self.custom_voices_dir = Path("custom_voices")
        self.custom_voices_dir.mkdir(exist_ok=True)
        
        # Initialize available voices for each engine
        self.available_voices = self._load_available_voices()
        self.custom_voice_mapping = self._load_custom_voice_mapping()
        
    def _load_available_voices(self) -> Dict[str, Dict[str, List[str]]]:
        """Load available voices for each TTS engine."""
        # Initialize Gemini voice library
        try:
            from gemini_voice_library import GeminiVoiceLibrary
            gemini_library = GeminiVoiceLibrary()
            
            # Convert Gemini voices to the expected format
            gemini_voices_dict = {}
            for lang_code, voices in gemini_library.gemini_voices.items():
                gemini_voices_dict[lang_code] = voices
        except Exception as e:
            print(f"⚠️ Error loading Gemini voices: {str(e)}")
            gemini_voices_dict = {
                "hi": ["gemini_hi_deep", "gemini_hi_female"],
                "en": ["gemini_en_soft", "gemini_en_fast"],
                "es": ["gemini_es_bright"]
            }
        
        voices = {
            "gemini": gemini_voices_dict,
            "edge": {
                # Edge TTS voices (comprehensive list)
                "ar-EG": ["ar-EG-SalmaNeural", "ar-EG-ShakirNeural"],
                "de-DE": ["de-DE-AmalaNeural", "de-DE-ConradNeural", "de-DE-KatjaNeural", "de-DE-KillianNeural"],
                "es-US": ["es-US-AlonsoNeural", "es-US-PalomaNeural"],
                "fr-FR": ["fr-FR-DeniseNeural", "fr-FR-EloiseNeural", "fr-FR-HenriNeural", "fr-FR-YvesNeural"],
                "hi-IN": ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
                "id-ID": ["id-ID-ArdiNeural", "id-ID-GadisNeural"],
                "it-IT": ["it-IT-DiegoNeural", "it-IT-ElsaNeural", "it-IT-IsabellaNeural"],
                "ja-JP": ["ja-JP-KeitaNeural", "ja-JP-NanamiNeural"],
                "ko-KR": ["ko-KR-InJoonNeural", "ko-KR-SunHiNeural"],
                "pt-BR": ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural"],
                "ru-RU": ["ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural"],
                "nl-NL": ["nl-NL-ColetteNeural", "nl-NL-FennaNeural", "nl-NL-MaartenNeural"],
                "pl-PL": ["pl-PL-MarekNeural", "pl-PL-ZofiaNeural"],
                "th-TH": ["th-TH-NiwatNeural", "th-TH-PremwadeeNeural"],
                "tr-TR": ["tr-TR-AhmetNeural", "tr-TR-EmelNeural"],
                "vi-VN": ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"],
                "ro-RO": ["ro-RO-AlinaNeural", "ro-RO-EmilNeural"],
                "uk-UA": ["uk-UA-OstapNeural", "uk-UA-PolinaNeural"],
                "bn-BD": ["bn-BD-NabanitaNeural", "bn-BD-PradeepNeural"],
                "en-US": ["en-US-AriaNeural", "en-US-DavisNeural", "en-US-GuyNeural", "en-US-JennyNeural"],
                "en-IN": ["en-IN-NeerjaExpressiveNeural", "en-IN-PrabhatNeural"],
                "mr-IN": ["mr-IN-AarohiNeural", "mr-IN-ManoharNeural"],
                "ta-IN": ["ta-IN-PallaviNeural", "ta-IN-ValluvarNeural"],
                "te-IN": ["te-IN-MohanNeural", "te-IN-ShrutiNeural"]
            },
            "kokoro": {
                # Kokoro TTS voices
                "ja-JP": ["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael"],
                "en-US": ["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael"],
                "ko-KR": ["af_heart", "af_bella"],
                "zh-CN": ["af_heart", "af_bella"]
            }
        }
        return voices
    
    def _load_custom_voice_mapping(self) -> Dict[str, Dict[str, str]]:
        """Load custom voice mapping from JSON file."""
        try:
            if os.path.exists(self.custom_voice_config_file):
                with open(self.custom_voice_config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Error loading custom voice mapping: {str(e)}")
            return {}
    
    def _save_custom_voice_mapping(self, mapping: Dict[str, Dict[str, str]]):
        """Save custom voice mapping to JSON file."""
        try:
            with open(self.custom_voice_config_file, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving custom voice mapping: {str(e)}")
    
    def auto_assign_voices(self, language_codes: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Automatically assign voices for given language codes.
        
        Args:
            language_codes: List of language codes (e.g., ['hi-IN', 'es-US', 'ja-JP'])
            
        Returns:
            Dictionary mapping language codes to voice assignments
        """
        voice_map = {}
        
        for lang_code in language_codes:
            # Check if custom mapping exists
            if lang_code in self.custom_voice_mapping:
                custom = self.custom_voice_mapping[lang_code]
                voice_map[lang_code] = {
                    "engine": custom.get("engine", "gemini"),
                    "voice": custom.get("voice", "default"),
                    "source": "custom_mapping"
                }
                continue
            
            # Check for custom uploaded voice
            custom_voice_file = self.custom_voices_dir / f"{lang_code}_custom.wav"
            if custom_voice_file.exists():
                voice_map[lang_code] = {
                    "engine": "custom",
                    "voice": str(custom_voice_file),
                    "source": "custom_upload"
                }
                continue
            
            # Auto-assign based on priority: Gemini > Edge > Kokoro
            assigned = False
            
            # Priority 1: Gemini TTS
            if lang_code in self.available_voices["gemini"]:
                gemini_voices = self.available_voices["gemini"][lang_code]
                if gemini_voices:
                    voice_map[lang_code] = {
                        "engine": "gemini",
                        "voice": gemini_voices[0],  # Use first available voice
                        "source": "auto_gemini"
                    }
                    assigned = True
            
            # Priority 2: Edge TTS
            if not assigned and lang_code in self.available_voices["edge"]:
                edge_voices = self.available_voices["edge"][lang_code]
                if edge_voices:
                    voice_map[lang_code] = {
                        "engine": "edge",
                        "voice": edge_voices[0],  # Use first available voice
                        "source": "auto_edge"
                    }
                    assigned = True
            
            # Priority 3: Kokoro TTS
            if not assigned and lang_code in self.available_voices["kokoro"]:
                kokoro_voices = self.available_voices["kokoro"][lang_code]
                if kokoro_voices:
                    voice_map[lang_code] = {
                        "engine": "kokoro",
                        "voice": kokoro_voices[0],  # Use first available voice
                        "source": "auto_kokoro"
                    }
                    assigned = True
            
            # No voice found
            if not assigned:
                voice_map[lang_code] = {
                    "engine": "none",
                    "voice": "Voice Not Found",
                    "source": "not_found"
                }
        
        return voice_map
    
    def save_voice_assignments(self, voice_map: Dict[str, Dict[str, str]]):
        """Save voice assignments to JSON file."""
        try:
            with open(self.voice_assignments_file, "w", encoding="utf-8") as f:
                json.dump(voice_map, f, indent=2, ensure_ascii=False)
            print(f"✅ Voice assignments saved to {self.voice_assignments_file}")
        except Exception as e:
            print(f"⚠️ Error saving voice assignments: {str(e)}")
    
    def load_voice_assignments(self) -> Dict[str, Dict[str, str]]:
        """Load voice assignments from JSON file."""
        try:
            if os.path.exists(self.voice_assignments_file):
                with open(self.voice_assignments_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Error loading voice assignments: {str(e)}")
            return {}
    
    def get_available_voices_for_language(self, lang_code: str) -> Dict[str, List[str]]:
        """Get all available voices for a specific language across all engines."""
        available = {}
        
        for engine, voices in self.available_voices.items():
            if lang_code in voices and voices[lang_code]:
                available[engine] = voices[lang_code]
        
        # Add custom voices
        custom_voice_file = self.custom_voices_dir / f"{lang_code}_custom.wav"
        if custom_voice_file.exists():
            available["custom"] = [str(custom_voice_file)]
        
        return available
    
    def update_custom_voice_mapping(self, lang_code: str, engine: str, voice: str):
        """Update custom voice mapping for a language."""
        if lang_code not in self.custom_voice_mapping:
            self.custom_voice_mapping[lang_code] = {}
        
        self.custom_voice_mapping[lang_code] = {
            "engine": engine,
            "voice": voice
        }
        
        self._save_custom_voice_mapping(self.custom_voice_mapping)
        print(f"✅ Updated custom voice mapping for {lang_code}: {engine}:{voice}")
    
    def save_custom_voice_file(self, lang_code: str, voice_file_path: str) -> str:
        """Save a custom voice file for a language."""
        try:
            custom_voice_file = self.custom_voices_dir / f"{lang_code}_custom.wav"
            
            # Copy the uploaded file
            import shutil
            shutil.copy2(voice_file_path, custom_voice_file)
            
            print(f"✅ Custom voice saved for {lang_code}: {custom_voice_file}")
            return str(custom_voice_file)
            
        except Exception as e:
            print(f"⚠️ Error saving custom voice file: {str(e)}")
            return ""
    
    def generate_voice_assignment_summary(self, voice_map: Dict[str, Dict[str, str]]) -> str:
        """Generate a human-readable summary of voice assignments."""
        summary_lines = [
            "🎤 Voice Assignment Summary:",
            "=" * 40
        ]
        
        for lang_code, assignment in voice_map.items():
            engine = assignment["engine"]
            voice = assignment["voice"]
            source = assignment["source"]
            
            if engine == "none":
                status = "❌ Voice Not Found"
            elif source == "custom_mapping":
                status = f"🎯 Custom: {engine}:{voice}"
            elif source == "custom_upload":
                status = f"📁 Custom Upload: {voice}"
            else:
                status = f"✅ Auto: {engine}:{voice}"
            
            summary_lines.append(f"  {lang_code}: {status}")
        
        return "\\n".join(summary_lines)

def test_voice_assignment_manager():
    """Test the voice assignment manager."""
    print("🧪 Testing Voice Assignment Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = VoiceAssignmentManager()
    
    # Test auto-assignment
    test_languages = ["hi-IN", "es-US", "ja-JP", "fr-FR", "de-DE", "ko-KR"]
    
    print(f"\\n🎯 Auto-assigning voices for: {', '.join(test_languages)}")
    voice_map = manager.auto_assign_voices(test_languages)
    
    # Print results
    print("\\n" + manager.generate_voice_assignment_summary(voice_map))
    
    # Save assignments
    manager.save_voice_assignments(voice_map)
    
    # Test loading
    loaded_map = manager.load_voice_assignments()
    print(f"\\n✅ Successfully loaded {len(loaded_map)} voice assignments")
    
    return True

if __name__ == "__main__":
    success = test_voice_assignment_manager()
    
    if success:
        print("\\n🎉 Voice Assignment Manager test PASSED!")
    else:
        print("\\n❌ Voice Assignment Manager test FAILED!")
    
    exit(0 if success else 1)