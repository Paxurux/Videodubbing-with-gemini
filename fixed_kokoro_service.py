#!/usr/bin/env python3
"""
Kokoro TTS Service Integration
Fixed multilingual setup with proper model loading.
"""

import os
from typing import List, Dict, Optional
from kokoro import KPipeline
import soundfile as sf

class FixedKokoroTTSService:
    """Fixed Kokoro TTS service with proper multilingual support."""
    
    def __init__(self, lang_code: str = "a", voice: str = "af_heart"):
        """Initialize with proper model path."""
        # Ensure model path is set
        if not os.environ.get("KOKORO_MODEL_PATH"):
            model_path = os.path.abspath("Kokoro-82M")
            if os.path.exists(model_path):
                os.environ["KOKORO_MODEL_PATH"] = model_path
        
        self.lang_code = lang_code
        self.voice = voice
        self.pipeline = None
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the Kokoro pipeline."""
        try:
            self.pipeline = KPipeline(lang_code=self.lang_code)
            print(f"✅ Kokoro pipeline initialized: {self.lang_code}/{self.voice}")
        except Exception as e:
            print(f"❌ Failed to initialize Kokoro pipeline: {str(e)}")
            raise
    
    def generate_tts_chunks(self, segments: List[Dict], progress_callback=None) -> str:
        """Generate TTS chunks from segments."""
        if not self.pipeline:
            raise Exception("Kokoro pipeline not initialized")
        
        os.makedirs("kokoro_chunks", exist_ok=True)
        
        for i, segment in enumerate(segments):
            if progress_callback:
                progress = (i + 1) / len(segments)
                progress_callback(progress, f"Generating Kokoro TTS {i+1}/{len(segments)}")
            
            text = segment.get("text_translated", segment.get("text", ""))
            if not text.strip():
                continue
            
            try:
                # Generate audio
                output = self.pipeline(text, voice=self.voice)
                
                # Save chunk
                chunk_file = f"kokoro_chunks/chunk_{i:03d}.wav"
                for j, (_, _, audio) in enumerate(output):
                    sf.write(chunk_file, audio, 24000)
                    break  # Only save first segment
                
                print(f"✅ Generated {chunk_file}")
                
            except Exception as e:
                print(f"❌ Failed to generate chunk {i}: {str(e)}")
        
        return "kokoro_chunks"

# Language and voice mappings
KOKORO_LANGUAGES = {
    "a": "American English",
    "b": "British English", 
    "j": "Japanese",
    "h": "Hindi",
    "z": "Chinese",
    "f": "French"
}

KOKORO_VOICES = {
    "a": ["af_heart", "am_heart", "af_sky", "am_sky"],
    "b": ["bf_heart", "bm_heart"],
    "j": ["jf_heart", "jm_heart"],
    "h": ["hf_heart", "hm_heart"],
    "z": ["zf_heart", "zm_heart"],
    "f": ["ff_heart", "fm_heart"]
}

def get_available_voices(lang_code: str) -> List[str]:
    """Get available voices for a language."""
    return KOKORO_VOICES.get(lang_code, [])

def test_fixed_kokoro():
    """Test the fixed Kokoro service."""
    try:
        service = FixedKokoroTTSService("a", "af_heart")
        
        test_segments = [
            {"text_translated": "This is a test of the fixed Kokoro TTS service."},
            {"text_translated": "It should work properly with multilingual support."}
        ]
        
        chunks_dir = service.generate_tts_chunks(test_segments)
        print(f"✅ Fixed Kokoro test completed: {chunks_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Fixed Kokoro test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_fixed_kokoro()
