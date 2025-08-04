#!/usr/bin/env python3
"""
Working Dubbing Service using the old Google Generative AI API (v0.3.2).
This version focuses on translation only since TTS is not available in the old API.
"""
import os
import json
import logging
import tempfile
import subprocess
from typing import List, Dict, Optional, Callable
from api_key_manager import APIKeyManager

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class WorkingDubbingService:
    """Working dubbing service using old Gemini API for translation only."""
    
    # Translation models that work with old API
    TRANSLATION_MODELS = [
        "gemini-pro",
        "gemini-pro-latest"
    ]
    
    def __init__(self):
        """Initialize dubbing service."""
        if not GENAI_AVAILABLE:
            raise ImportError("Google Generative AI library not available")
        
        self.logger = logging.getLogger(__name__)
        self.api_manager = APIKeyManager()
        
        # Create output directories
        os.makedirs("temp_audio", exist_ok=True)
    
    def translate_transcription(self, transcription_data: List[Dict], json_prompt: str, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Translate transcription using JSON prompt with old API.
        Args:
            transcription_data: List of transcription segments with timing
            json_prompt: User's JSON prompt for translation
            progress_callback: Optional progress callback
        Returns:
            List of translated segments
        """
        if not self.api_manager.has_keys():
            raise Exception("No API keys available. Please save API keys first.")
        
        if progress_callback:
            progress_callback(0.1, "Starting translation...")
        
        try:
            # Prepare the transcription as JSON
            transcription_json = json.dumps(transcription_data, indent=2, ensure_ascii=False)
            
            # Build the complete prompt
            full_prompt = f"""
{json_prompt}

Here is the transcription data in JSON format:
{transcription_json}

Please return the translated segments in the same JSON format, preserving the 'start' and 'end' timing fields exactly, but replacing the 'text' field with 'text_translated' containing your translation.

IMPORTANT: Return ONLY the JSON array, no additional text or explanation.
"""
            
            if progress_callback:
                progress_callback(0.3, "Sending translation request...")
            
            # Try each API key and model
            api_keys = self.api_manager.get_keys()
            for key_idx, api_key in enumerate(api_keys):
                for model in self.TRANSLATION_MODELS:
                    try:
                        self.logger.info(f"Trying translation with {model}")
                        genai.configure(api_key=api_key)
                        
                        # Use the old API syntax
                        model_instance = genai.GenerativeModel(model)
                        response = model_instance.generate_content(
                            full_prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.1,
                                max_output_tokens=8192
                            )
                        )
                        
                        if response and response.text:
                            if progress_callback:
                                progress_callback(0.7, "Parsing translation response...")
                            
                            # Clean the response text
                            response_text = response.text.strip()
                            
                            # Remove any markdown formatting
                            if response_text.startswith('```json'):
                                response_text = response_text[7:]
                            if response_text.endswith('```'):
                                response_text = response_text[:-3]
                            response_text = response_text.strip()
                            
                            # Parse the response
                            translated_segments = json.loads(response_text)
                            
                            # Validate format
                            if isinstance(translated_segments, list):
                                validated_segments = []
                                for segment in translated_segments:
                                    if all(key in segment for key in ['start', 'end', 'text_translated']):
                                        validated_segments.append(segment)
                                
                                if validated_segments:
                                    if progress_callback:
                                        progress_callback(1.0, f"Translation complete! {len(validated_segments)} segments translated")
                                    return validated_segments
                    
                    except Exception as e:
                        self.logger.warning(f"Translation failed with {model}: {str(e)}")
                        continue
            
            raise Exception("All translation attempts failed")
            
        except Exception as e:
            self.logger.error(f"Translation failed: {str(e)}")
            raise
    
    def create_simple_audio_replacement(self, original_video_path: str, translated_segments: List[Dict], progress_callback: Optional[Callable] = None) -> str:
        """
        Create a simple audio replacement using text-to-speech (placeholder for now).
        Args:
            original_video_path: Path to original video
            translated_segments: List of translated segments
            progress_callback: Optional progress callback
        Returns:
            Path to output video (for now, just returns original with subtitle file)
        """
        if progress_callback:
            progress_callback(0.1, "Creating subtitle file...")
        
        try:
            # For now, create an SRT subtitle file with translations
            srt_content = self._create_srt_from_segments(translated_segments)
            
            srt_file = "translated_subtitles.srt"
            with open(srt_file, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            if progress_callback:
                progress_callback(0.5, "Creating video with subtitles...")
            
            # Create a video with burned-in subtitles
            output_video = "output_with_subtitles.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', original_video_path,
                '-vf', f"subtitles={srt_file}:force_style='FontSize=24,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,Outline=2'",
                '-c:a', 'copy',
                output_video
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            if progress_callback:
                progress_callback(1.0, "Video with subtitles created successfully!")
            
            return output_video
            
        except Exception as e:
            self.logger.error(f"Failed to create video with subtitles: {str(e)}")
            raise
    
    def _create_srt_from_segments(self, segments: List[Dict]) -> str:
        """Create SRT subtitle content from translated segments."""
        srt_content = []
        
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_srt_time(segment['start'])
            end_time = self._seconds_to_srt_time(segment['end'])
            text = segment['text_translated']
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between subtitles
        
        return "\n".join(srt_content)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"