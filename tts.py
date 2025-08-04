"""
Text-to-Speech service using Google Gemini TTS API with chunking and voice consistency.
Handles large content by splitting into manageable chunks and ensuring audio duration matching.
"""

import os
import json
import logging
import wave
import tiktoken
from typing import List, Dict, Optional
from dataclasses import dataclass
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
import subprocess
import tempfile

from config import PIPELINE_DEFAULTS

# TTS models in exact priority order from master prompt
TTS_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts"
]
from state_manager import StateManager
from error_handler import global_error_handler, handle_pipeline_error, create_error_context

# Maximum tokens per TTS chunk
MAX_TOKENS_PER_CHUNK = PIPELINE_DEFAULTS["max_tokens_per_chunk"]

@dataclass
class TTSChunk:
    """Data model for TTS chunk with metadata."""
    chunk_index: int
    segments: List[Dict]
    audio_file_path: str
    token_count: int

class TTSService:
    """Service for generating TTS audio from translated segments with chunking support."""
    
    def __init__(self, api_keys: List[str], voice_name: str = "Kore"):
        """Initialize TTS service with API keys and voice configuration."""
        if not GENAI_AVAILABLE:
            raise ImportError("Google Generative AI library not available. Please install: pip install google-generativeai")
            
        if not api_keys:
            raise ValueError("No API keys provided for TTS service")
            
        self.logger = logging.getLogger(__name__)
        
        # Validate voice name
        from config import TTS_VOICES
        if voice_name not in TTS_VOICES:
            self.logger.warning(f"Voice '{voice_name}' not in supported voices, using 'Kore'")
            voice_name = "Kore"
            
        self.api_keys = api_keys
        self.voice_name = voice_name
        self.current_key_index = 0
        self.current_model_index = 0
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.state_manager = StateManager()
        self.max_retries = PIPELINE_DEFAULTS["max_retry_attempts"]
        
        # Create TTS chunks directory
        os.makedirs("tts_chunks", exist_ok=True)
        
    @handle_pipeline_error("tts", max_recovery_attempts=5)
    def generate_tts_chunks(self, translated_segments: List[Dict], progress_callback=None) -> str:
        """
        Generate TTS audio chunks from translated segments with comprehensive error handling.
        
        Args:
            translated_segments: List of translated segments with timing
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to directory containing TTS chunks
        """
        if not translated_segments:
            self.logger.warning("No translated segments provided for TTS generation")
            return "tts_chunks"
        
        # Create error context with relevant information
        context = {
            'stage': 'tts',
            'api_keys': self.api_keys,
            'segments': translated_segments,
            'segment_count': len(translated_segments),
            'voice_name': self.voice_name,
            'current_key_index': self.current_key_index
        }
        
        with create_error_context("tts", **context) as error_ctx:
            self.logger.info(f"Starting TTS generation for {len(translated_segments)} segments")
            
            # Validate segments
            if not self._validate_translated_segments(translated_segments):
                raise ValueError("Invalid translated segments provided")
            
            # Get healthy API keys
            healthy_keys = global_error_handler.get_healthy_api_keys(self.api_keys)
            if not healthy_keys:
                # Try graceful degradation
                degraded, message = global_error_handler.implement_graceful_degradation(context)
                if degraded:
                    raise Exception(f"TTS service degraded: {message}")
                else:
                    raise Exception("All API keys are exhausted and no graceful degradation is available")
            
            # Update context with healthy keys
            context['healthy_api_keys'] = healthy_keys
            
            # Calculate token-based chunks
            chunks = self._calculate_token_chunks(translated_segments)
            self.logger.info(f"Split into {len(chunks)} chunks for TTS processing")
            
            # Generate audio for each chunk with error recovery
            return self._generate_chunks_with_recovery(chunks, progress_callback, context)
    
    def _generate_chunks_with_recovery(self, chunks: List[List[Dict]], progress_callback, context: Dict) -> str:
        """Generate TTS chunks with comprehensive error recovery."""
        chunk_files = []
        failed_chunks = []
        healthy_keys = context.get('healthy_api_keys', self.api_keys)
        
        for i, chunk_segments in enumerate(chunks):
            if progress_callback:
                progress = (i + 1) / len(chunks)
                progress_callback(progress, f"Generating TTS chunk {i + 1}/{len(chunks)}")
            
            # Try to generate chunk with error recovery
            chunk_success = False
            max_chunk_attempts = min(3, len(healthy_keys))
            
            for attempt in range(max_chunk_attempts):
                try:
                    # Use healthy keys only
                    if self.current_key_index >= len(healthy_keys):
                        self.current_key_index = 0
                    
                    api_key = healthy_keys[self.current_key_index] if healthy_keys else self.api_keys[self.current_key_index]
                    
                    # Track API key usage
                    global_error_handler.track_api_key_status(api_key, success=True)
                    
                    chunk_file = self._generate_chunk_audio_with_key(chunk_segments, i, api_key)
                    
                    if chunk_file:
                        chunk_files.append(chunk_file)
                        chunk_success = True
                        
                        # Track successful API key usage
                        global_error_handler.track_api_key_status(api_key, success=True)
                        break
                    else:
                        # Track failed API key usage
                        global_error_handler.track_api_key_status(api_key, success=False)
                        self.logger.warning(f"TTS chunk {i} generation returned no audio")
                        
                except Exception as e:
                    # Track failed API key usage
                    error_type = self._classify_tts_error(e)
                    global_error_handler.track_api_key_status(api_key, success=False, error_type=error_type)
                    
                    self.logger.warning(f"TTS chunk {i} attempt {attempt + 1} failed: {str(e)}")
                    
                    # Handle specific error types
                    if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                        # Mark key as quota exhausted and rotate
                        global_error_handler.track_api_key_status(api_key, success=False, error_type=error_type)
                        self._rotate_to_next_key()
                        healthy_keys = global_error_handler.get_healthy_api_keys(self.api_keys)
                        
                        if not healthy_keys:
                            self.logger.error("All API keys exhausted during TTS generation")
                            break
                    
                    # Wait before retry
                    if attempt < max_chunk_attempts - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
            
            if not chunk_success:
                failed_chunks.append(i)
                self.logger.error(f"Failed to generate TTS for chunk {i} after all attempts")
        
        # Handle failed chunks
        if failed_chunks:
            self.logger.warning(f"Failed to generate {len(failed_chunks)} chunks: {failed_chunks}")
            
            # If too many chunks failed, try graceful degradation
            failure_rate = len(failed_chunks) / len(chunks)
            if failure_rate > 0.5:  # More than 50% failed
                degraded, message = global_error_handler.implement_graceful_degradation(context)
                if degraded:
                    raise Exception(f"TTS service degraded due to high failure rate: {message}")
        
        if not chunk_files:
            raise Exception("Failed to generate any TTS chunks")
        
        self.logger.info(f"Generated {len(chunk_files)} TTS chunks successfully")
        return "tts_chunks"
    
    def _classify_tts_error(self, exception: Exception) -> 'ErrorType':
        """Classify TTS errors for proper tracking."""
        from error_handler import ErrorType
        
        error_str = str(exception).lower()
        
        if any(keyword in error_str for keyword in ["api key", "authentication", "unauthorized"]):
            return ErrorType.API_KEY_ERROR
        elif any(keyword in error_str for keyword in ["quota", "limit", "rate limit"]):
            return ErrorType.QUOTA_EXCEEDED
        elif any(keyword in error_str for keyword in ["network", "connection", "timeout"]):
            return ErrorType.NETWORK_ERROR
        elif any(keyword in error_str for keyword in ["file", "directory", "path"]):
            return ErrorType.FILE_ERROR
        else:
            return ErrorType.PROCESSING_ERROR
    
    def _rotate_to_next_key(self):
        """Rotate to next API key."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    
    def _generate_chunk_audio_with_key(self, chunk_segments: List[Dict], chunk_index: int, api_key: str) -> Optional[str]:
        """Generate TTS audio for a single chunk with specific API key."""
        # Try splitting chunk if it's too large
        if len(chunk_segments) > 1:
            try:
                return self._attempt_chunk_generation_with_key(chunk_segments, chunk_index, api_key)
            except Exception as e:
                self.logger.warning(f"Chunk {chunk_index} failed, attempting to split: {str(e)}")
                return self._split_and_retry_chunk_with_key(chunk_segments, chunk_index, api_key)
        else:
            return self._attempt_chunk_generation_with_key(chunk_segments, chunk_index, api_key)
    
    def _attempt_chunk_generation_with_key(self, chunk_segments: List[Dict], chunk_index: int, api_key: str) -> Optional[str]:
        """Attempt to generate TTS for chunk with specific API key and model fallback."""
        # Prepare TTS prompt
        tts_prompt = self._build_tts_prompt(chunk_segments)
        
        # Try each model with the specific API key
        for model_index, model in enumerate(TTS_MODELS):
            try:
                self.logger.info(f"TTS attempt for chunk {chunk_index}: {model} with specific key")
                
                audio_data = self._make_tts_request(tts_prompt, model, api_key)
                
                if audio_data:
                    # Log successful API request
                    token_count = sum(len(self.tokenizer.encode(seg.get('text_translated', ''))) for seg in chunk_segments)
                    self.state_manager.log_api_request(
                        service="tts",
                        model=model,
                        api_key_index=self.api_keys.index(api_key) if api_key in self.api_keys else -1,
                        success=True,
                        token_count=token_count,
                        chunk_index=chunk_index
                    )
                    
                    # Save audio file
                    chunk_file = f"tts_chunks/chunk_{chunk_index:03d}.wav"
                    self._save_wave_file(chunk_file, audio_data)
                    
                    # Validate and adjust audio duration
                    expected_duration = self._calculate_expected_duration(chunk_segments)
                    adjusted_file = self._ensure_audio_duration(chunk_file, expected_duration)
                    
                    return adjusted_file
                    
            except Exception as e:
                # Log failed API request
                token_count = sum(len(self.tokenizer.encode(seg.get('text_translated', ''))) for seg in chunk_segments)
                self.state_manager.log_api_request(
                    service="tts",
                    model=model,
                    api_key_index=self.api_keys.index(api_key) if api_key in self.api_keys else -1,
                    success=False,
                    error_msg=str(e),
                    token_count=token_count,
                    chunk_index=chunk_index
                )
                
                self.logger.warning(f"TTS failed for chunk {chunk_index} with {model}: {str(e)}")
                
                # Continue to next model
                continue
        
        # All models failed with this API key
        return None
    
    def _split_and_retry_chunk_with_key(self, chunk_segments: List[Dict], chunk_index: int, api_key: str) -> Optional[str]:
        """Split chunk and retry with specific API key."""
        if len(chunk_segments) <= 1:
            return None
        
        # Split chunk in half
        mid_point = len(chunk_segments) // 2
        first_half = chunk_segments[:mid_point]
        second_half = chunk_segments[mid_point:]
        
        self.logger.info(f"Splitting chunk {chunk_index} into {len(first_half)} + {len(second_half)} segments")
        
        # Generate audio for each half
        first_audio = self._attempt_chunk_generation_with_key(first_half, chunk_index, api_key)
        second_audio = self._attempt_chunk_generation_with_key(second_half, chunk_index, api_key)
        
        if first_audio and second_audio:
            # Combine the audio files
            combined_file = f"tts_chunks/chunk_{chunk_index:03d}.wav"
            self._combine_audio_files([first_audio, second_audio], combined_file)
            
            # Clean up temporary files
            if first_audio != combined_file:
                try:
                    os.remove(first_audio)
                except:
                    pass
            if second_audio != combined_file:
                try:
                    os.remove(second_audio)
                except:
                    pass
            
            return combined_file
        
        return None
    
    def _validate_translated_segments(self, segments: List[Dict]) -> bool:
        """
        Validate translated segments have required fields.
        
        Args:
            segments: List of translated segments to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['start', 'end', 'text_translated']
        
        for i, segment in enumerate(segments):
            for field in required_fields:
                if field not in segment:
                    self.logger.error(f"Segment {i} missing required field: {field}")
                    return False
                    
            # Validate timing
            if segment['start'] >= segment['end']:
                self.logger.error(f"Segment {i} has invalid timing: start={segment['start']}, end={segment['end']}")
                return False
                
            # Validate text content
            if not segment['text_translated'].strip():
                self.logger.warning(f"Segment {i} has empty text_translated")
                
        return True
    
    def _calculate_token_chunks(self, segments: List[Dict]) -> List[List[Dict]]:
        """Split segments into chunks based on token count with improved algorithm."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        # Calculate total tokens for logging
        total_tokens = sum(len(self.tokenizer.encode(seg.get('text_translated', ''))) for seg in segments)
        self.logger.info(f"Total tokens to process: {total_tokens}")
        
        for segment in segments:
            text = segment.get('text_translated', '')
            segment_tokens = len(self.tokenizer.encode(text))
            
            # If single segment exceeds limit, it needs special handling
            if segment_tokens > MAX_TOKENS_PER_CHUNK:
                # Add current chunk if not empty
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_tokens = 0
                
                # Split large segment into smaller parts
                split_segments = self._split_large_segment(segment)
                chunks.extend(split_segments)
                continue
            
            # If adding this segment would exceed limit, start new chunk
            if current_tokens + segment_tokens > MAX_TOKENS_PER_CHUNK and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [segment]
                current_tokens = segment_tokens
            else:
                current_chunk.append(segment)
                current_tokens += segment_tokens
                
        # Add final chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        # Log chunking statistics
        chunk_sizes = [sum(len(self.tokenizer.encode(seg.get('text_translated', ''))) for seg in chunk) for chunk in chunks]
        self.logger.info(f"Created {len(chunks)} chunks with sizes: {chunk_sizes}")
            
        return chunks
    
    def _split_large_segment(self, segment: Dict) -> List[List[Dict]]:
        """
        Split a large segment that exceeds token limit into smaller parts.
        
        Args:
            segment: Large segment to split
            
        Returns:
            List of chunk lists, each containing part of the original segment
        """
        text = segment.get('text_translated', '')
        words = text.split()
        
        if not words:
            return [[segment]]  # Return as single chunk if no words
        
        chunks = []
        current_words = []
        current_tokens = 0
        
        # Calculate timing per word for accurate segment timing
        total_duration = segment['end'] - segment['start']
        time_per_word = total_duration / len(words) if words else 0
        
        for i, word in enumerate(words):
            word_tokens = len(self.tokenizer.encode(word))
            
            if current_tokens + word_tokens > MAX_TOKENS_PER_CHUNK and current_words:
                # Create segment for current words
                start_time = segment['start'] + (i - len(current_words)) * time_per_word
                end_time = segment['start'] + i * time_per_word
                
                chunk_segment = {
                    'start': start_time,
                    'end': end_time,
                    'text_translated': ' '.join(current_words)
                }
                chunks.append([chunk_segment])
                
                current_words = [word]
                current_tokens = word_tokens
            else:
                current_words.append(word)
                current_tokens += word_tokens
        
        # Add final chunk
        if current_words:
            start_time = segment['start'] + (len(words) - len(current_words)) * time_per_word
            end_time = segment['end']
            
            chunk_segment = {
                'start': start_time,
                'end': end_time,
                'text_translated': ' '.join(current_words)
            }
            chunks.append([chunk_segment])
        
        self.logger.info(f"Split large segment into {len(chunks)} parts")
        return chunks
    
    def _generate_chunk_audio(self, chunk_segments: List[Dict], chunk_index: int) -> Optional[str]:
        """Generate TTS audio for a single chunk with retry logic."""
        # Try splitting chunk if it's too large
        if len(chunk_segments) > 1:
            try:
                return self._attempt_chunk_generation(chunk_segments, chunk_index)
            except Exception as e:
                self.logger.warning(f"Chunk {chunk_index} failed, attempting to split: {str(e)}")
                return self._split_and_retry_chunk(chunk_segments, chunk_index)
        else:
            return self._attempt_chunk_generation(chunk_segments, chunk_index)
    
    def _attempt_chunk_generation(self, chunk_segments: List[Dict], chunk_index: int) -> Optional[str]:
        """Attempt to generate TTS for chunk with model fallback."""
        # Prepare TTS prompt
        tts_prompt = self._build_tts_prompt(chunk_segments)
        
        # Try each model/key combination
        for attempt in range(len(TTS_MODELS) * len(self.api_keys)):
            try:
                model = TTS_MODELS[self.current_model_index]
                api_key = self.api_keys[self.current_key_index]
                
                self.logger.info(f"TTS attempt {attempt + 1} for chunk {chunk_index}: {model}")
                
                audio_data = self._make_tts_request(tts_prompt, model, api_key)
                
                if audio_data:
                    # Log successful API request
                    token_count = sum(len(self.tokenizer.encode(seg.get('text_translated', ''))) for seg in chunk_segments)
                    self.state_manager.log_api_request(
                        service="tts",
                        model=model,
                        api_key_index=self.current_key_index,
                        success=True,
                        token_count=token_count,
                        chunk_index=chunk_index
                    )
                    
                    # Save audio file
                    chunk_file = f"tts_chunks/chunk_{chunk_index:03d}.wav"
                    self._save_wave_file(chunk_file, audio_data)
                    
                    # Validate and adjust audio duration
                    expected_duration = self._calculate_expected_duration(chunk_segments)
                    adjusted_file = self._ensure_audio_duration(chunk_file, expected_duration)
                    
                    return adjusted_file
                    
            except Exception as e:
                # Log failed API request
                token_count = sum(len(self.tokenizer.encode(seg.get('text_translated', ''))) for seg in chunk_segments)
                self.state_manager.log_api_request(
                    service="tts",
                    model=model,
                    api_key_index=self.current_key_index,
                    success=False,
                    error_msg=str(e),
                    token_count=token_count,
                    chunk_index=chunk_index
                )
                self.logger.warning(f"TTS failed for chunk {chunk_index} with {model}: {str(e)}")
                self._rotate_to_next_model_key()
                
        return None
    
    def _split_and_retry_chunk(self, chunk_segments: List[Dict], chunk_index: int) -> Optional[str]:
        """Split chunk in half and retry TTS generation."""
        mid_point = len(chunk_segments) // 2
        first_half = chunk_segments[:mid_point]
        second_half = chunk_segments[mid_point:]
        
        # Generate audio for each half
        first_file = self._attempt_chunk_generation(first_half, f"{chunk_index}a")
        second_file = self._attempt_chunk_generation(second_half, f"{chunk_index}b")
        
        if first_file and second_file:
            # Concatenate the two halves
            combined_file = f"tts_chunks/chunk_{chunk_index:03d}.wav"
            self._concatenate_audio_files([first_file, second_file], combined_file)
            
            # Clean up temporary files
            os.remove(first_file)
            os.remove(second_file)
            
            return combined_file
            
        return None
    
    def _build_tts_prompt(self, segments: List[Dict]) -> str:
        """Build TTS prompt from segments."""
        text_parts = []
        for segment in segments:
            text = segment.get('text_translated', '')
            if text.strip():
                text_parts.append(text.strip())
                
        return " ".join(text_parts)
    
    def _make_tts_request(self, text: str, model: str, api_key: str) -> Optional[bytes]:
        """Make TTS request using REST API - FIXED to actually work!"""
        if not text.strip():
            raise ValueError("Empty text provided for TTS generation")
            
        try:
            import requests
            import base64
            
            # Add retry logic for transient failures
            for retry in range(self.max_retries):
                try:
                    # Use REST API directly (fixes blank audio issue)
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    
                    # Request payload with exact specification
                    payload = {
                        "contents": [{"parts": [{"text": text.strip()}]}],
                        "generationConfig": {
                            "response_modalities": ["AUDIO"],
                            "speech_config": {
                                "voice_config": {
                                    "prebuilt_voice_config": {
                                        "voice_name": self.voice_name
                                    }
                                }
                            }
                        }
                    }
                    
                    headers = {"Content-Type": "application/json"}
                    
                    # Make REST API request
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Extract audio data
                        if ('candidates' in result and result['candidates'] and 
                            'content' in result['candidates'][0] and 
                            'parts' in result['candidates'][0]['content']):
                            
                            parts = result['candidates'][0]['content']['parts']
                            
                            if parts and 'inlineData' in parts[0] and 'data' in parts[0]['inlineData']:
                                audio_b64 = parts[0]['inlineData']['data']
                                
                                if audio_b64:
                                    # Decode base64 audio data
                                    audio_data = base64.b64decode(audio_b64)
                                    
                                    if len(audio_data) > 1000:  # Valid audio file
                                        return audio_data
                                    else:
                                        raise Exception(f"Audio data too small: {len(audio_data)} bytes")
                                else:
                                    raise Exception("No audio data in response")
                            else:
                                raise Exception("Invalid response structure")
                        else:
                            raise Exception("No candidates in response")
                    else:
                        raise Exception(f"API error {response.status_code}: {response.text}")
                        
                except Exception as e:
                    if retry < self.max_retries - 1 and ("timeout" in str(e).lower() or "network" in str(e).lower()):
                        self.logger.warning(f"TTS request retry {retry + 1} due to: {str(e)}")
                        time.sleep(2 ** retry)  # Exponential backoff
                        continue
                    else:
                        raise e
                    
                    # Validate response structure
                    if not response.candidates:
                        raise Exception("No candidates in TTS response")
                        
                    if not response.candidates[0].content.parts:
                        raise Exception("No content parts in TTS response")
                        
                    audio_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    if not audio_data:
                        raise Exception("No audio data in TTS response")
                        
                    # Validate audio data is not empty
                    if len(audio_data) == 0:
                        raise Exception("Empty audio data received")
                        
                    return audio_data
                    
                except Exception as e:
                    if retry < self.max_retries - 1 and ("timeout" in str(e).lower() or "network" in str(e).lower()):
                        self.logger.warning(f"TTS request retry {retry + 1} due to: {str(e)}")
                        time.sleep(2 ** retry)  # Exponential backoff
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            categorized_error = self._handle_tts_error(e, model, self.current_key_index)
            raise Exception(categorized_error)
    
    def _handle_tts_error(self, error: Exception, model: str, api_key_index: int) -> str:
        """
        Handle and categorize TTS API errors.
        
        Args:
            error: The exception that occurred
            model: Model name that failed
            api_key_index: Index of API key that failed
            
        Returns:
            Categorized error message
        """
        error_str = str(error).lower()
        
        if "quota" in error_str or "limit" in error_str:
            return f"TTS quota/rate limit exceeded for {model} (key {api_key_index + 1})"
        elif "authentication" in error_str or "api key" in error_str:
            return f"TTS authentication failed for {model} (key {api_key_index + 1})"
        elif "network" in error_str or "connection" in error_str:
            return f"TTS network error for {model} (key {api_key_index + 1})"
        elif "timeout" in error_str:
            return f"TTS request timeout for {model} (key {api_key_index + 1})"
        elif "voice" in error_str:
            return f"TTS voice error for {model} (key {api_key_index + 1}): {str(error)}"
        else:
            return f"TTS unknown error for {model} (key {api_key_index + 1}): {str(error)}"
    
    def _save_wave_file(self, filename: str, audio_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """Save raw audio data as proper WAV file."""
        try:
            # Save as proper WAV file (fixes audio format issues)
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(audio_data)
        except Exception as e:
            self.logger.warning(f"Failed to save as WAV: {str(e)}")
            # Fallback: save raw data
            with open(filename, "wb") as f:
                f.write(audio_data)
    
    def _calculate_expected_duration(self, segments: List[Dict]) -> float:
        """Calculate expected duration from segment timings."""
        if not segments:
            return 0.0
            
        start_time = min(seg.get('start', 0.0) for seg in segments)
        end_time = max(seg.get('end', 0.0) for seg in segments)
        
        return end_time - start_time
    
    def _ensure_audio_duration(self, audio_path: str, expected_duration: float) -> str:
        """Adjust audio duration to match expected timing using FFmpeg."""
        if expected_duration <= 0:
            return audio_path
            
        # Get actual audio duration
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
               '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        
        try:
            output = subprocess.check_output(cmd).decode('utf-8').strip()
            actual_duration = float(output)
            
            # If duration is significantly different, adjust it
            if abs(actual_duration - expected_duration) > 0.1:
                adjusted_path = audio_path.replace('.wav', '_adjusted.wav')
                
                # Use FFmpeg to adjust duration
                cmd = ['ffmpeg', '-i', audio_path, '-filter:a', 
                       f'atempo={actual_duration/expected_duration}', 
                       adjusted_path, '-y']
                
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Replace original with adjusted
                os.replace(adjusted_path, audio_path)
                
        except (subprocess.SubprocessError, ValueError) as e:
            self.logger.warning(f"Could not adjust audio duration: {str(e)}")
            
        return audio_path
    
    def _concatenate_audio_files(self, file_list: List[str], output_path: str):
        """Concatenate multiple audio files using FFmpeg."""
        # Create temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for file_path in file_list:
                f.write(f"file '{os.path.abspath(file_path)}'\n")
            list_file = f.name
            
        try:
            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file, 
                   '-c', 'copy', output_path, '-y']
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        finally:
            os.unlink(list_file)
    
    def get_chunk_info(self, chunks_directory: str = "tts_chunks") -> Dict:
        """
        Get information about generated TTS chunks.
        
        Args:
            chunks_directory: Directory containing TTS chunks
            
        Returns:
            Dictionary with chunk information
        """
        if not os.path.exists(chunks_directory):
            return {'chunk_count': 0, 'total_duration': 0, 'files': []}
            
        chunk_files = sorted([f for f in os.listdir(chunks_directory) if f.endswith('.wav')])
        total_duration = 0
        
        for chunk_file in chunk_files:
            file_path = os.path.join(chunks_directory, chunk_file)
            try:
                duration = self._get_audio_duration(file_path)
                total_duration += duration
            except Exception as e:
                self.logger.warning(f"Could not get duration for {chunk_file}: {str(e)}")
                
        return {
            'chunk_count': len(chunk_files),
            'total_duration': total_duration,
            'files': chunk_files
        }
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file using wave module."""
        try:
            with wave.open(audio_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception as e:
            # Fallback to ffprobe if wave fails
            try:
                cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                       '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
                output = subprocess.check_output(cmd).decode('utf-8').strip()
                return float(output)
            except Exception:
                self.logger.warning(f"Could not determine duration for {audio_path}")
                return 0.0
    
    def validate_chunk_quality(self, chunk_file: str, expected_duration: float, tolerance: float = 0.5) -> bool:
        """
        Validate the quality of a generated TTS chunk.
        
        Args:
            chunk_file: Path to the chunk file
            expected_duration: Expected duration in seconds
            tolerance: Acceptable duration difference in seconds
            
        Returns:
            True if chunk meets quality standards
        """
        if not os.path.exists(chunk_file):
            self.logger.error(f"Chunk file does not exist: {chunk_file}")
            return False
            
        # Check file size (should not be too small)
        file_size = os.path.getsize(chunk_file)
        if file_size < 1000:  # Less than 1KB is suspicious
            self.logger.warning(f"Chunk file suspiciously small: {file_size} bytes")
            return False
            
        # Check duration
        actual_duration = self._get_audio_duration(chunk_file)
        if actual_duration == 0:
            self.logger.error(f"Could not determine duration for chunk: {chunk_file}")
            return False
            
        duration_diff = abs(actual_duration - expected_duration)
        if duration_diff > tolerance:
            self.logger.warning(f"Duration mismatch for {chunk_file}: expected {expected_duration:.2f}s, got {actual_duration:.2f}s")
            return False
            
        return True
    
    def cleanup_failed_chunks(self, chunks_directory: str = "tts_chunks"):
        """
        Clean up any failed or incomplete chunk files.
        
        Args:
            chunks_directory: Directory containing TTS chunks
        """
        if not os.path.exists(chunks_directory):
            return
            
        chunk_files = [f for f in os.listdir(chunks_directory) if f.endswith('.wav')]
        removed_count = 0
        
        for chunk_file in chunk_files:
            file_path = os.path.join(chunks_directory, chunk_file)
            
            # Remove files that are too small or corrupted
            try:
                file_size = os.path.getsize(file_path)
                if file_size < 100:  # Very small files are likely corrupted
                    os.remove(file_path)
                    removed_count += 1
                    self.logger.info(f"Removed corrupted chunk: {chunk_file}")
                    continue
                    
                # Try to open as wave file to validate
                with wave.open(file_path, 'rb'):
                    pass  # If this succeeds, file is likely valid
                    
            except Exception as e:
                # File is corrupted, remove it
                try:
                    os.remove(file_path)
                    removed_count += 1
                    self.logger.info(f"Removed corrupted chunk: {chunk_file} ({str(e)})")
                except Exception:
                    self.logger.warning(f"Could not remove corrupted chunk: {chunk_file}")
                    
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} corrupted chunk files")
    
    def _rotate_to_next_model_key(self):
        """Rotate to next model/API key combination."""
        self.current_model_index = (self.current_model_index + 1) % len(TTS_MODELS)
        
        # If we've cycled through all models, move to next API key
        if self.current_model_index == 0:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
    def get_current_model_info(self) -> Dict:
        """Get information about current model and API key being used."""
        return {
            'model': TTS_MODELS[self.current_model_index],
            'api_key_index': self.current_key_index,
            'voice_name': self.voice_name,
            'total_models': len(TTS_MODELS),
            'total_keys': len(self.api_keys)
        }