#!/usr/bin/env python3
"""
Simple Dubbing Service that handles the complete workflow:
1. Transcription (already done)
2. Translation with JSON prompt
3. TTS generation with chunking
4. Video stitching
"""
import os
import json
import logging
import tempfile
import subprocess
import wave
from typing import List, Dict, Optional, Callable
from api_key_manager import APIKeyManager

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class SimpleDubbingService:
    """Simple dubbing service using Gemini API."""
    
    # Available TTS voices
    AVAILABLE_VOICES = [
        "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", 
        "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba", 
        "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar"
    ]
    
    # TTS models to try
    TTS_MODELS = [
        "gemini-2.5-flash-preview-tts",
        "gemini-2.5-pro-preview-tts"
    ]
    
    # Translation models to try
    TRANSLATION_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-pro", 
        "gemini-2.0-flash-001",
        "gemini-1.5-pro-002"
    ]
    
    def __init__(self):
        """Initialize dubbing service."""
        if not GENAI_AVAILABLE:
            raise ImportError("Google Generative AI library not available")
        
        self.logger = logging.getLogger(__name__)
        self.api_manager = APIKeyManager()
        
        # Create output directories
        os.makedirs("tts_chunks", exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)
    
    def translate_transcription(self, transcription_data: List[Dict], json_prompt: str, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Translate transcription using JSON prompt.
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
                                temperature=0.1
                            )
                        )
                        
                        if response and response.text:
                            if progress_callback:
                                progress_callback(0.7, "Parsing translation response...")
                            
                            # Parse the response
                            translated_segments = json.loads(response.text.strip())
                            
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
    
    def generate_tts_audio(self, translated_segments: List[Dict], voice_name: str = "Kore", progress_callback: Optional[Callable] = None) -> str:
        """
        Generate TTS audio from translated segments with proper chunking.
        Args:
            translated_segments: List of translated segments
            voice_name: TTS voice to use
            progress_callback: Optional progress callback
        Returns:
            Path to directory containing TTS chunks
        """
        if not self.api_manager.has_keys():
            raise Exception("No API keys available. Please save API keys first.")
        
        if voice_name not in self.AVAILABLE_VOICES:
            voice_name = "Kore"
        
        if progress_callback:
            progress_callback(0.1, "Preparing TTS chunks...")
        
        # Calculate chunks (max ~8000 characters per chunk for safety)
        chunks = self._calculate_tts_chunks(translated_segments, max_chars=8000)
        self.logger.info(f"Split into {len(chunks)} TTS chunks")
        
        if progress_callback:
            progress_callback(0.2, f"Generating {len(chunks)} TTS chunks...")
        
        # Generate audio for each chunk
        api_keys = self.api_manager.get_keys()
        successful_chunks = []
        
        for i, chunk_segments in enumerate(chunks):
            if progress_callback:
                progress = 0.2 + (0.7 * (i + 1) / len(chunks))
                progress_callback(progress, f"Generating TTS chunk {i + 1}/{len(chunks)}")
            
            chunk_file = self._generate_single_tts_chunk(chunk_segments, i, voice_name, api_keys)
            if chunk_file:
                successful_chunks.append(chunk_file)
                self.logger.info(f"Generated TTS chunk {i + 1}: {chunk_file}")
            else:
                self.logger.error(f"Failed to generate TTS chunk {i + 1}")
        
        if not successful_chunks:
            raise Exception("Failed to generate any TTS chunks")
        
        if progress_callback:
            progress_callback(1.0, f"TTS generation complete! {len(successful_chunks)} chunks created")
        
        return "tts_chunks"
    
    def _calculate_tts_chunks(self, segments: List[Dict], max_chars: int = 8000) -> List[List[Dict]]:
        """Calculate optimal chunks for TTS generation."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for segment in segments:
            text = segment.get('text_translated', '')
            text_length = len(text)
            
            # If adding this segment would exceed limits, start new chunk
            if (current_length + text_length > max_chars and current_chunk) or len(current_chunk) >= 50:
                chunks.append(current_chunk)
                current_chunk = [segment]
                current_length = text_length
            else:
                current_chunk.append(segment)
                current_length += text_length
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _generate_single_tts_chunk(self, chunk_segments: List[Dict], chunk_index: int, voice_name: str, api_keys: List[str]) -> Optional[str]:
        """Generate TTS audio for a single chunk."""
        try:
            # Combine text from segments
            combined_text = self._combine_chunk_text(chunk_segments)
            if not combined_text.strip():
                return None
            
            # Try each API key and model
            for api_key in api_keys:
                for model in self.TTS_MODELS:
                    try:
                        client = genai.Client(api_key=api_key)
                        
                        response = client.models.generate_content(
                            model=model,
                            contents=combined_text,
                            config=types.GenerateContentConfig(
                                response_modalities=["AUDIO"],
                                speech_config=types.SpeechConfig(
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                            voice_name=voice_name
                                        )
                                    )
                                )
                            )
                        )
                        
                        if response and response.candidates:
                            audio_data = response.candidates[0].content.parts[0].inline_data.data
                            
                            # Save audio to file
                            chunk_file = f"tts_chunks/chunk_{chunk_index:03d}.wav"
                            self._save_wave_file(chunk_file, audio_data)
                            return chunk_file
                    
                    except Exception as e:
                        self.logger.warning(f"TTS generation failed with {model}: {str(e)}")
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate TTS chunk {chunk_index}: {str(e)}")
            return None
    
    def _combine_chunk_text(self, chunk_segments: List[Dict]) -> str:
        """Combine text from multiple segments into a single chunk."""
        texts = []
        for segment in chunk_segments:
            text = segment.get('text_translated', '').strip()
            if text:
                texts.append(text)
        return ". ".join(texts) + "."
    
    def _save_wave_file(self, filename: str, audio_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """Save audio data as a WAV file."""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(audio_data)
    
    def create_dubbed_video(self, original_video_path: str, tts_chunks_dir: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Create dubbed video by combining TTS audio with original video.
        Args:
            original_video_path: Path to original video
            tts_chunks_dir: Directory containing TTS chunks
            progress_callback: Optional progress callback
        Returns:
            Path to dubbed video file
        """
        if progress_callback:
            progress_callback(0.1, "Combining TTS chunks...")
        
        try:
            # Get all TTS chunk files
            chunk_files = []
            for i in range(1000):  # Max 1000 chunks
                chunk_file = os.path.join(tts_chunks_dir, f"chunk_{i:03d}.wav")
                if os.path.exists(chunk_file):
                    chunk_files.append(chunk_file)
                else:
                    break
            
            if not chunk_files:
                raise Exception("No TTS chunks found")
            
            if progress_callback:
                progress_callback(0.3, f"Found {len(chunk_files)} TTS chunks, combining...")
            
            # Combine all TTS chunks into single audio file
            combined_audio = "temp_audio/combined_tts.wav"
            self._combine_audio_files(chunk_files, combined_audio)
            
            if progress_callback:
                progress_callback(0.6, "Replacing audio in video...")
            
            # Replace audio in video
            output_video = "output_dubbed.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', original_video_path,
                '-i', combined_audio,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                output_video
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            if progress_callback:
                progress_callback(1.0, "Dubbed video created successfully!")
            
            return output_video
            
        except Exception as e:
            self.logger.error(f"Failed to create dubbed video: {str(e)}")
            raise
    
    def _combine_audio_files(self, audio_files: List[str], output_file: str):
        """Combine multiple audio files into one."""
        # Create a temporary file list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for audio_file in audio_files:
                f.write(f"file '{os.path.abspath(audio_file)}'\n")
            file_list = f.name
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', file_list,
                '-c', 'copy',
                output_file
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        finally:
            os.unlink(file_list)