#!/usr/bin/env python3
"""
Custom Voice Handler
Manages user-uploaded custom voice files and integrates them with the TTS workflow.
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tempfile

class CustomVoiceHandler:
    """Handles custom voice uploads and integration with the TTS system."""
    
    def __init__(self):
        """Initialize the custom voice handler."""
        self.custom_voices_dir = "custom_voices"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure custom voices directory exists."""
        os.makedirs(self.custom_voices_dir, exist_ok=True)
    
    def detect_language_from_filename(self, filename: str) -> str:
        """Detect language code from filename."""
        # Common language patterns in filenames (ordered by specificity)
        language_patterns = [
            (r'(hindi|हिंदी)', 'hi'),
            (r'\b(english)\b', 'en'),
            (r'(spanish|espanol|español)', 'es'),
            (r'\b(japanese)\b', 'ja'),
            (r'\b(french|francais|français)\b', 'fr'),
            (r'\b(german|deutsch)\b', 'de'),
            (r'\b(korean)\b', 'ko'),
            (r'\b(portuguese)\b', 'pt'),
            (r'\b(arabic)\b', 'ar'),
            (r'\b(italian)\b', 'it'),
            (r'\b(russian)\b', 'ru'),
            (r'\b(chinese)\b', 'zh'),
            (r'\b(dutch)\b', 'nl'),
            (r'\b(polish)\b', 'pl'),
            (r'\b(thai)\b', 'th'),
            (r'\b(turkish)\b', 'tr'),
            (r'\b(vietnamese)\b', 'vi'),
            # Short codes last to avoid conflicts
            (r'\b(hi)\b', 'hi'),
            (r'\b(en)\b', 'en'),
            (r'\b(es)\b', 'es'),
            (r'\b(ja)\b', 'ja'),
            (r'\b(fr)\b', 'fr'),
            (r'\b(de)\b', 'de'),
            (r'\b(ko)\b', 'ko'),
            (r'\b(pt)\b', 'pt'),
            (r'\b(ar)\b', 'ar'),
            (r'\b(it)\b', 'it'),
            (r'\b(ru)\b', 'ru'),
            (r'\b(zh)\b', 'zh'),
            (r'\b(nl)\b', 'nl'),
            (r'\b(pl)\b', 'pl'),
            (r'\b(th)\b', 'th'),
            (r'\b(tr)\b', 'tr'),
            (r'\b(vi)\b', 'vi')
        ]
        
        filename_lower = filename.lower()
        
        # Check for language patterns (order matters - more specific first)
        for pattern, lang_code in language_patterns:
            if re.search(pattern, filename_lower):
                return lang_code
        
        # Check for direct language codes (e.g., hi_custom.wav, en_voice.wav)
        lang_match = re.search(r'^([a-z]{2})_', filename_lower)
        if lang_match:
            return lang_match.group(1)
        
        # Default to English if no language detected
        return 'en'
    
    def generate_custom_voice_id(self, original_filename: str, language: str, index: int) -> str:
        """Generate a consistent voice ID for custom voices."""
        # Remove extension and clean filename
        base_name = Path(original_filename).stem
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
        
        # Create voice ID: custom_[lang]_[cleaned_name]_[index]
        voice_id = f"custom_{language}_{clean_name}_{index:02d}"
        return voice_id
    
    def process_uploaded_files(self, uploaded_files: List, video_name: str = "demo") -> List[Dict[str, str]]:
        """Process uploaded custom voice files."""
        if not uploaded_files:
            return []
        
        processed_files = []
        
        for i, file_obj in enumerate(uploaded_files):
            try:
                # Get original filename
                original_filename = os.path.basename(file_obj.name)
                
                # Detect language
                language = self.detect_language_from_filename(original_filename)
                
                # Generate voice ID
                voice_id = self.generate_custom_voice_id(original_filename, language, i + 1)
                
                # Create final filename with video name
                final_filename = f"{voice_id}_{video_name}.wav"
                dest_path = os.path.join(self.custom_voices_dir, final_filename)
                
                # Copy file to custom voices directory
                shutil.copy2(file_obj.name, dest_path)
                
                # Create file info
                file_info = {
                    "file_path": dest_path,
                    "voice_id": voice_id,
                    "original_filename": original_filename,
                    "language": language,
                    "engine": "custom",
                    "display_name": f"{language.upper()} Custom Voice ({original_filename})",
                    "file_size": os.path.getsize(dest_path)
                }
                
                processed_files.append(file_info)
                print(f"✅ Processed custom voice: {original_filename} -> {final_filename}")
                
            except Exception as e:
                print(f"❌ Error processing {file_obj.name}: {str(e)}")
                continue
        
        return processed_files
    
    def get_custom_voice_files(self) -> List[Dict[str, str]]:
        """Get all existing custom voice files."""
        if not os.path.exists(self.custom_voices_dir):
            return []
        
        custom_files = []
        
        for filename in os.listdir(self.custom_voices_dir):
            if filename.endswith('.wav'):
                file_path = os.path.join(self.custom_voices_dir, filename)
                
                # Parse filename to extract info
                voice_info = self.parse_custom_filename(filename)
                if voice_info:
                    voice_info["file_path"] = file_path
                    voice_info["file_size"] = os.path.getsize(file_path)
                    custom_files.append(voice_info)
        
        return custom_files
    
    def parse_custom_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Parse custom voice filename to extract metadata."""
        # Expected format: custom_[lang]_[name]_[index]_[video].wav
        match = re.match(r'custom_([a-z]{2})_(.+?)_(\d+)_(.+?)\.wav$', filename)
        
        if match:
            language, name_part, index, video_name = match.groups()
            
            return {
                "voice_id": f"custom_{language}_{name_part}_{index}",
                "language": language,
                "engine": "custom",
                "display_name": f"{language.upper()} Custom Voice ({name_part})",
                "original_name": name_part,
                "index": int(index),
                "video_name": video_name
            }
        
        # Fallback parsing for simpler formats
        if filename.startswith('custom_') and filename.endswith('.wav'):
            parts = filename[:-4].split('_')  # Remove .wav
            if len(parts) >= 3:
                language = parts[1] if len(parts) > 1 else 'en'
                name_part = '_'.join(parts[2:])
                
                return {
                    "voice_id": filename[:-4],  # Remove .wav
                    "language": language,
                    "engine": "custom",
                    "display_name": f"{language.upper()} Custom Voice ({name_part})",
                    "original_name": name_part,
                    "index": 1,
                    "video_name": "unknown"
                }
        
        return None
    
    def validate_audio_file(self, file_path: str) -> bool:
        """Validate that the uploaded file is a valid audio file."""
        try:
            # Check file extension
            if not file_path.lower().endswith(('.wav', '.mp3', '.m4a')):
                return False
            
            # Check file size (must be at least 1KB)
            if os.path.getsize(file_path) < 1024:
                return False
            
            # Basic WAV header check for WAV files
            if file_path.lower().endswith('.wav'):
                with open(file_path, 'rb') as f:
                    header = f.read(12)
                    if len(header) >= 12 and header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                        return True
                    return False
            
            # For other formats, just check size and extension
            return True
            
        except Exception as e:
            print(f"Error validating audio file {file_path}: {str(e)}")
            return False
    
    def get_language_display_name(self, lang_code: str) -> str:
        """Get display name for language code."""
        language_names = {
            'en': 'English',
            'hi': 'Hindi', 
            'es': 'Spanish',
            'ja': 'Japanese',
            'fr': 'French',
            'de': 'German',
            'ko': 'Korean',
            'pt': 'Portuguese',
            'ar': 'Arabic',
            'it': 'Italian',
            'ru': 'Russian',
            'zh': 'Chinese',
            'nl': 'Dutch',
            'pl': 'Polish',
            'th': 'Thai',
            'tr': 'Turkish',
            'vi': 'Vietnamese'
        }
        
        return language_names.get(lang_code, lang_code.upper())
    
    def clean_custom_voices(self) -> int:
        """Clean up old custom voice files."""
        if not os.path.exists(self.custom_voices_dir):
            return 0
        
        cleaned_count = 0
        
        for filename in os.listdir(self.custom_voices_dir):
            file_path = os.path.join(self.custom_voices_dir, filename)
            
            try:
                # Remove files that are too small or invalid
                if not self.validate_audio_file(file_path):
                    os.remove(file_path)
                    cleaned_count += 1
                    print(f"🗑️ Removed invalid file: {filename}")
                    
            except Exception as e:
                print(f"Error cleaning file {filename}: {str(e)}")
        
        return cleaned_count

# Test the handler
if __name__ == "__main__":
    print("🧪 Testing Custom Voice Handler")
    print("=" * 50)
    
    handler = CustomVoiceHandler()
    
    # Test language detection
    test_filenames = [
        "hi_custom_voice.wav",
        "english_narration.wav", 
        "spanish_audio.wav",
        "my_hindi_voice.wav",
        "custom_en_demo.wav",
        "unknown_file.wav"
    ]
    
    print("🧪 Testing language detection:")
    for filename in test_filenames:
        lang = handler.detect_language_from_filename(filename)
        print(f"  {filename} -> {lang} ({handler.get_language_display_name(lang)})")
    
    # Test voice ID generation
    print("\n🧪 Testing voice ID generation:")
    for i, filename in enumerate(test_filenames[:3]):
        lang = handler.detect_language_from_filename(filename)
        voice_id = handler.generate_custom_voice_id(filename, lang, i + 1)
        print(f"  {filename} -> {voice_id}")
    
    # Test existing custom files
    custom_files = handler.get_custom_voice_files()
    print(f"\n✅ Found {len(custom_files)} existing custom voice files")
    
    print("\n🎉 Custom Voice Handler test complete!")