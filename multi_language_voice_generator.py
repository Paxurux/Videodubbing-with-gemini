#!/usr/bin/env python3
"""
Multi-Language Voice Generator
Generates audio for each translated language using assigned voices and TTS engines.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import traceback

class MultiLanguageVoiceGenerator:
    """Generates voices for multiple languages using assigned TTS engines."""
    
    def __init__(self):
        """Initialize the voice generator."""
        self.voices_dir = Path("voices")
        self.voices_dir.mkdir(exist_ok=True)
        
        self.voice_assignments_file = "voice_assignments.json"
        self.translation_files_dir = Path("translations")
        
        # Initialize TTS services
        self._initialize_tts_services()
        
    def _initialize_tts_services(self):
        """Initialize all TTS services."""
        try:
            # Import TTS services
            from api_key_manager import APIKeyManager
            from real_gemini_service import RealGeminiService
            from enhanced_edge_tts_service import EnhancedEdgeTTSService
            from kokoro_tts_service import KokoroTTSService
            
            # Initialize API manager
            self.api_manager = APIKeyManager()
            
            # Initialize services
            self.gemini_service = None
            self.edge_service = None
            self.kokoro_service = None
            
            # Initialize Gemini service if API keys available
            if self.api_manager.has_keys():
                api_keys = self.api_manager.get_keys()
                self.gemini_service = RealGeminiService(api_keys)
                print("✅ Gemini TTS service initialized")
            
            # Initialize Edge TTS service
            try:
                from enhanced_edge_tts_service import EdgeTTSConfig
                edge_config = EdgeTTSConfig()
                self.edge_service = EnhancedEdgeTTSService(edge_config)
                print("✅ Edge TTS service initialized")
            except Exception as e:
                print(f"⚠️ Edge TTS service not available: {str(e)}")
            
            # Initialize Kokoro TTS service
            try:
                self.kokoro_service = KokoroTTSService()
                print("✅ Kokoro TTS service initialized")
            except Exception as e:
                print(f"⚠️ Kokoro TTS service not available: {str(e)}")
                
        except Exception as e:
            print(f"⚠️ Error initializing TTS services: {str(e)}")
    
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
    
    def load_translations(self) -> Dict[str, List[Dict]]:
        """Load all translation files."""
        translations = {}
        
        if not self.translation_files_dir.exists():
            print("⚠️ Translations directory not found")
            return translations
        
        # Load each translation file
        for json_file in self.translation_files_dir.glob("transcript_*.json"):
            lang_code = json_file.stem.replace("transcript_", "")
            if lang_code == "original":
                continue
                
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    translation_data = json.load(f)
                    translations[lang_code] = translation_data
                    print(f"✅ Loaded translation for {lang_code}: {len(translation_data)} segments")
            except Exception as e:
                print(f"⚠️ Error loading translation for {lang_code}: {str(e)}")
        
        return translations
    
    def get_video_name(self) -> str:
        """Extract video name from available files or use default."""
        # Try to find video file name from common locations
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        
        for ext in video_extensions:
            video_files = list(Path(".").glob(f"*{ext}"))
            if video_files:
                return video_files[0].stem
        
        # Fallback to generic name
        return "demo"
    
    def generate_gemini_audio(self, segments: List[Dict], voice: str, lang_code: str) -> Optional[str]:
        """Generate audio using Gemini TTS."""
        try:
            if not self.gemini_service:
                print("❌ Gemini TTS service not available")
                return None
            
            print(f"🎤 Generating Gemini TTS audio with voice: {voice}")
            
            # Use Gemini TTS to generate audio chunks
            def progress_callback(progress, message):
                print(f"[Gemini TTS {progress:.1%}] {message}")
            
            chunks_dir = self.gemini_service.generate_tts_chunks(
                segments, voice, progress_callback
            )
            
            if chunks_dir and os.path.exists(chunks_dir):
                # Find generated audio files and combine them
                chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith('.wav')])
                
                if chunk_files:
                    # For now, use the first chunk or combine all chunks
                    first_chunk = os.path.join(chunks_dir, chunk_files[0])
                    
                    if len(chunk_files) == 1:
                        return first_chunk
                    else:
                        # Combine multiple chunks
                        return self._combine_audio_chunks(chunks_dir, chunk_files)
            
            return None
            
        except Exception as e:
            print(f"❌ Gemini TTS generation failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_edge_audio(self, segments: List[Dict], voice: str, lang_code: str) -> Optional[str]:
        """Generate audio using Edge TTS."""
        try:
            if not self.edge_service:
                print("❌ Edge TTS service not available")
                return None
            
            print(f"🎤 Generating Edge TTS audio with voice: {voice}")
            
            # Use Edge TTS to generate audio chunks
            def progress_callback(progress, message):
                print(f"[Edge TTS {progress:.1%}] {message}")
            
            chunks_dir = self.edge_service.generate_tts_chunks(
                segments, progress_callback
            )
            
            if chunks_dir and os.path.exists(chunks_dir):
                # Find generated audio files and combine them
                chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith('.wav')])
                
                if chunk_files:
                    # For now, use the first chunk or combine all chunks
                    first_chunk = os.path.join(chunks_dir, chunk_files[0])
                    
                    if len(chunk_files) == 1:
                        return first_chunk
                    else:
                        # Combine multiple chunks
                        return self._combine_audio_chunks(chunks_dir, chunk_files)
            
            return None
            
        except Exception as e:
            print(f"❌ Edge TTS generation failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_kokoro_audio(self, segments: List[Dict], voice: str, lang_code: str) -> Optional[str]:
        """Generate audio using Kokoro TTS."""
        try:
            if not self.kokoro_service:
                print("❌ Kokoro TTS service not available")
                return None
            
            print(f"🎤 Generating Kokoro TTS audio with voice: {voice}")
            
            # Use Kokoro TTS to generate audio chunks
            def progress_callback(progress, message):
                print(f"[Kokoro TTS {progress:.1%}] {message}")
            
            chunks_dir = self.kokoro_service.generate_tts_chunks(
                segments, progress_callback
            )
            
            if chunks_dir and os.path.exists(chunks_dir):
                # Find generated audio files and combine them
                chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.endswith('.wav')])
                
                if chunk_files:
                    # For now, use the first chunk or combine all chunks
                    first_chunk = os.path.join(chunks_dir, chunk_files[0])
                    
                    if len(chunk_files) == 1:
                        return first_chunk
                    else:
                        # Combine multiple chunks
                        return self._combine_audio_chunks(chunks_dir, chunk_files)
            
            return None
            
        except Exception as e:
            print(f"❌ Kokoro TTS generation failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_custom_audio(self, segments: List[Dict], voice_file: str, lang_code: str) -> Optional[str]:
        """Use custom uploaded voice file."""
        try:
            if not os.path.exists(voice_file):
                print(f"❌ Custom voice file not found: {voice_file}")
                return None
            
            print(f"🎤 Using custom voice file: {voice_file}")
            
            # For custom voices, we'll just copy the file for now
            # In a full implementation, you might want to use voice cloning
            video_name = self.get_video_name()
            voice_name = Path(voice_file).stem
            final_path = self.voices_dir / f"{voice_name}_{video_name}.wav"
            
            import shutil
            shutil.copy2(voice_file, final_path)
            
            return str(final_path)
            
        except Exception as e:
            print(f"❌ Custom voice processing failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def _combine_audio_chunks(self, chunks_dir: str, chunk_files: List[str]) -> Optional[str]:
        """Combine multiple audio chunks into a single file."""
        try:
            import soundfile as sf
            import numpy as np
            
            combined_audio = []
            sample_rate = None
            
            for chunk_file in chunk_files:
                chunk_path = os.path.join(chunks_dir, chunk_file)
                audio_data, sr = sf.read(chunk_path)
                
                if sample_rate is None:
                    sample_rate = sr
                elif sample_rate != sr:
                    print(f"⚠️ Sample rate mismatch in {chunk_file}")
                
                combined_audio.append(audio_data)
            
            if combined_audio:
                # Concatenate all audio
                final_audio = np.concatenate(combined_audio)
                
                # Save combined audio
                combined_file = os.path.join(chunks_dir, "combined.wav")
                sf.write(combined_file, final_audio, sample_rate)
                
                return combined_file
            
            return None
            
        except Exception as e:
            print(f"❌ Error combining audio chunks: {str(e)}")
            return None
    
    def generate_voice_for_language(self, lang_code: str, assignment: Dict[str, str], 
                                  segments: List[Dict], video_name: str) -> Optional[str]:
        """Generate voice for a specific language."""
        try:
            engine = assignment.get("engine", "none")
            voice = assignment.get("voice", "default")
            
            print(f"\\n🎯 Generating voice for {lang_code} using {engine}:{voice}")
            
            # Generate audio based on engine
            temp_audio_file = None
            
            if engine == "gemini":
                temp_audio_file = self.generate_gemini_audio(segments, voice, lang_code)
            elif engine == "edge":
                temp_audio_file = self.generate_edge_audio(segments, voice, lang_code)
            elif engine == "kokoro":
                temp_audio_file = self.generate_kokoro_audio(segments, voice, lang_code)
            elif engine == "custom":
                temp_audio_file = self.generate_custom_audio(segments, voice, lang_code)
            else:
                print(f"❌ Unknown engine: {engine}")
                return None
            
            if not temp_audio_file or not os.path.exists(temp_audio_file):
                print(f"❌ Failed to generate audio for {lang_code}")
                return None
            
            # Create final filename with consistent naming scheme
            final_filename = f"{voice}_{video_name}.wav"
            final_path = self.voices_dir / final_filename
            
            # Copy to final location
            import shutil
            shutil.copy2(temp_audio_file, final_path)
            
            print(f"✅ Generated voice for {lang_code}: {final_path}")
            return str(final_path)
            
        except Exception as e:
            print(f"❌ Error generating voice for {lang_code}: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_all_voices(self, progress_callback=None) -> Dict[str, str]:
        """Generate voices for all languages with assignments."""
        try:
            # Load voice assignments
            voice_assignments = self.load_voice_assignments()
            if not voice_assignments:
                print("❌ No voice assignments found")
                return {}
            
            # Load translations
            translations = self.load_translations()
            if not translations:
                print("❌ No translations found")
                return {}
            
            # Get video name
            video_name = self.get_video_name()
            
            print(f"🎬 Generating voices for video: {video_name}")
            print(f"📊 Processing {len(voice_assignments)} language assignments")
            
            final_audio_files = {}
            successful_generations = 0
            
            # Process each language
            for i, (lang_code, assignment) in enumerate(voice_assignments.items()):
                if progress_callback:
                    progress = (i + 1) / len(voice_assignments)
                    progress_callback(progress, f"Generating voice for {lang_code} ({i+1}/{len(voice_assignments)})")
                
                # Check if translation exists
                if lang_code not in translations:
                    print(f"⚠️ No translation found for {lang_code}, skipping")
                    continue
                
                # Check if voice assignment is valid
                if assignment.get("engine") == "none" or assignment.get("voice") == "Voice Not Found":
                    print(f"⚠️ No valid voice assignment for {lang_code}, skipping")
                    continue
                
                # Generate voice
                try:
                    segments = translations[lang_code]
                    audio_file = self.generate_voice_for_language(
                        lang_code, assignment, segments, video_name
                    )
                    
                    if audio_file:
                        final_audio_files[lang_code] = audio_file
                        successful_generations += 1
                        print(f"✅ [{i+1}/{len(voice_assignments)}] {lang_code}: {audio_file}")
                    else:
                        print(f"❌ [{i+1}/{len(voice_assignments)}] {lang_code}: Generation failed")
                        
                except Exception as e:
                    print(f"❌ [{i+1}/{len(voice_assignments)}] {lang_code}: {str(e)}")
                    continue
                
                # Small delay between generations
                time.sleep(0.1)
            
            print(f"\\n📊 Voice generation complete!")
            print(f"✅ Successfully generated: {successful_generations}/{len(voice_assignments)} voices")
            print(f"📁 Audio files saved in: {self.voices_dir}")
            
            return final_audio_files
            
        except Exception as e:
            print(f"❌ Error in bulk voice generation: {str(e)}")
            traceback.print_exc()
            return {}
    
    def regenerate_voice_for_language(self, lang_code: str) -> Optional[str]:
        """Regenerate voice for a specific language."""
        try:
            # Load voice assignments
            voice_assignments = self.load_voice_assignments()
            if lang_code not in voice_assignments:
                print(f"❌ No voice assignment found for {lang_code}")
                return None
            
            # Load translation
            translations = self.load_translations()
            if lang_code not in translations:
                print(f"❌ No translation found for {lang_code}")
                return None
            
            # Get video name
            video_name = self.get_video_name()
            
            # Generate voice
            assignment = voice_assignments[lang_code]
            segments = translations[lang_code]
            
            audio_file = self.generate_voice_for_language(
                lang_code, assignment, segments, video_name
            )
            
            if audio_file:
                print(f"✅ Regenerated voice for {lang_code}: {audio_file}")
                return audio_file
            else:
                print(f"❌ Failed to regenerate voice for {lang_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error regenerating voice for {lang_code}: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_generated_voices_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of generated voice files."""
        summary = {}
        
        if not self.voices_dir.exists():
            return summary
        
        # Load voice assignments for reference
        voice_assignments = self.load_voice_assignments()
        
        # Scan voice files
        for voice_file in self.voices_dir.glob("*.wav"):
            # Try to extract language code from filename
            filename = voice_file.stem
            
            # Find matching language code
            for lang_code, assignment in voice_assignments.items():
                voice_name = assignment.get("voice", "")
                if voice_name in filename:
                    summary[lang_code] = {
                        "file_path": str(voice_file),
                        "file_size": voice_file.stat().st_size,
                        "voice_name": voice_name,
                        "engine": assignment.get("engine", "unknown"),
                        "filename": voice_file.name
                    }
                    break
        
        return summary

def test_multi_language_voice_generator():
    """Test the multi-language voice generator."""
    print("🧪 Testing Multi-Language Voice Generator")
    print("=" * 60)
    
    try:
        # Initialize generator
        generator = MultiLanguageVoiceGenerator()
        
        # Test loading voice assignments
        voice_assignments = generator.load_voice_assignments()
        print(f"✅ Loaded {len(voice_assignments)} voice assignments")
        
        # Test loading translations
        translations = generator.load_translations()
        print(f"✅ Loaded {len(translations)} translations")
        
        if voice_assignments and translations:
            print("\\n🎤 Ready for voice generation!")
            print("Voice assignments:", list(voice_assignments.keys()))
            print("Available translations:", list(translations.keys()))
        else:
            print("⚠️ No voice assignments or translations found for testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multi_language_voice_generator()
    
    if success:
        print("\\n🎉 Multi-Language Voice Generator test PASSED!")
    else:
        print("\\n❌ Multi-Language Voice Generator test FAILED!")
    
    exit(0 if success else 1)