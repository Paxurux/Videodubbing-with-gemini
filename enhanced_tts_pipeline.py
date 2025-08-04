#!/usr/bin/env python3
"""
Enhanced TTS Pipeline - Step-by-Step Breakdown Implementation
Following the exact specifications for individual segment processing with time matching.
"""

import os
import json
import logging
import wave
import subprocess
import tempfile
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

try:
    import google.generativeai as genai
    import google.generativeai.types as types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

@dataclass
class TTSSegment:
    """Individual TTS segment with timing and audio data."""
    index: int
    start_time: float
    end_time: float
    original_duration: float
    text: str
    audio_file: str
    actual_duration: float = 0.0
    adjusted_file: str = ""

class EnhancedTTSPipeline:
    """
    Enhanced TTS Pipeline with step-by-step processing.
    Processes each segment individually for perfect timing control.
    """
    
    # TTS models in exact priority order
    TTS_MODELS = [
        "gemini-2.5-flash-preview-tts",
        "gemini-2.5-pro-preview-tts"
    ]
    
    # Voice choices optimized for Hindi clarity
    HINDI_VOICE_RECOMMENDATIONS = {
        "serious": "Kore",      # Firm and clear
        "friendly": "Puck",     # Friendly and natural  
        "energetic": "Zephyr",  # Bright and energetic
        "default": "Kore"       # Best for Hindi clarity
    }
    
    def __init__(self, api_keys: List[str], voice_name: str = "Kore"):
        """Initialize enhanced TTS pipeline."""
        if not GENAI_AVAILABLE:
            raise ImportError("Google Generative AI library not available")
        
        self.api_keys = api_keys
        self.voice_name = voice_name
        self.current_key_index = 0
        self.current_model_index = 0
        self.logger = logging.getLogger(__name__)
        
        # Set up logging
        log_handler = logging.FileHandler('pipeline.log')
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.INFO)
        
        # Create output directories
        os.makedirs("tts_chunks", exist_ok=True)
        os.makedirs("temp_audio", exist_ok=True)
        
        self.logger.info(f"Enhanced TTS Pipeline initialized with voice: {voice_name}")
    
    def process_translated_json(self, translated_json: List[Dict], progress_callback: Optional[Callable] = None) -> str:
        """
        🎙️ Main TTS Pipeline - Step-by-Step Processing
        
        Args:
            translated_json: List of translated segments with timing
            progress_callback: Optional progress callback
            
        Returns:
            Path to final combined audio file
        """
        if progress_callback:
            progress_callback(0.1, "🔁 Starting enhanced TTS pipeline...")
        
        self.logger.info(f"Processing {len(translated_json)} translated segments")
        
        # Step 1: Pre-process JSON script for TTS
        if progress_callback:
            progress_callback(0.2, "📥 Pre-processing JSON script...")
        
        processed_segments = self._preprocess_json_script(translated_json)
        self.logger.info(f"Pre-processed {len(processed_segments)} valid segments")
        
        # Step 2: Process each segment individually (one-by-one)
        if progress_callback:
            progress_callback(0.3, "🪓 Processing segments individually...")
        
        tts_segments = self._process_segments_individually(processed_segments, progress_callback)
        
        if not tts_segments:
            raise Exception("Failed to generate any TTS segments")
        
        # Step 3: Time matching optimization
        if progress_callback:
            progress_callback(0.8, "⏱️ Optimizing timing alignment...")
        
        aligned_segments = self._optimize_time_matching(tts_segments)
        
        # Step 4: Combine all audio chunks
        if progress_callback:
            progress_callback(0.9, "🧬 Combining audio chunks...")
        
        final_audio = self._combine_audio_chunks(aligned_segments)
        
        if progress_callback:
            progress_callback(1.0, "✅ Enhanced TTS pipeline complete!")
        
        self.logger.info(f"Enhanced TTS pipeline completed: {final_audio}")
        return final_audio
    
    def _preprocess_json_script(self, translated_json: List[Dict]) -> List[Dict]:
        """
        🔁 1. Pre-Processing the JSON Script for TTS
        
        Filters and cleans the translated JSON:
        - Skips start/end (used only for sync)
        - Sends ONLY the "text_translated" part to Gemini TTS
        - Filters out timestamps or formatting junk
        - Ignores lines like [music] or [laughs]
        """
        processed_segments = []
        
        for i, segment in enumerate(translated_json):
            # Skip segments without required fields
            if not all(key in segment for key in ['start', 'end', 'text_translated']):
                self.logger.warning(f"Segment {i} missing required fields, skipping")
                continue
            
            # Extract text and clean it
            text = segment.get('text_translated', '').strip()
            
            # Filter out non-speech content
            if self._should_skip_segment(text):
                self.logger.info(f"Skipping non-speech segment {i}: {text[:50]}...")
                continue
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            if cleaned_text:
                processed_segment = {
                    'index': i,
                    'start': float(segment['start']),
                    'end': float(segment['end']),
                    'text_translated': cleaned_text,
                    'original_duration': float(segment['end']) - float(segment['start'])
                }
                processed_segments.append(processed_segment)
                self.logger.debug(f"Processed segment {i}: {cleaned_text[:50]}...")
        
        return processed_segments
    
    def _should_skip_segment(self, text: str) -> bool:
        """Check if segment should be skipped (music, sound effects, etc.)."""
        skip_patterns = [
            '[music]', '[laughs]', '[applause]', '[silence]', 
            '[sound]', '[noise]', '[background]', '♪', '♫',
            '[inaudible]', '[unclear]', '...'
        ]
        
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in skip_patterns) or len(text.strip()) < 3
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for optimal TTS generation."""
        # Remove timestamps and formatting
        import re
        
        # Remove timestamp patterns
        text = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}', '', text)
        text = re.sub(r'\[\d+:\d+:\d+\]', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special formatting characters
        text = text.replace('*', '').replace('_', '').replace('~', '')
        
        return text.strip()
    
    def _process_segments_individually(self, segments: List[Dict], progress_callback: Optional[Callable] = None) -> List[TTSSegment]:
        """
        🪓 2. Chunked Request Handling (One-by-One)
        
        Process each segment individually to avoid:
        - Token limit issues (32k context cap)
        - Mixing voice tones
        - Loss of alignment
        """
        tts_segments = []
        total_segments = len(segments)
        
        for i, segment in enumerate(segments):
            if progress_callback:
                progress = 0.3 + (0.5 * (i + 1) / total_segments)
                progress_callback(progress, f"Processing segment {i + 1}/{total_segments}")
            
            self.logger.info(f"Processing TTS for segment {i + 1}/{total_segments}")
            
            # Create TTS segment
            tts_segment = TTSSegment(
                index=segment['index'],
                start_time=segment['start'],
                end_time=segment['end'],
                original_duration=segment['original_duration'],
                text=segment['text_translated'],
                audio_file=""
            )
            
            # Generate TTS audio with retry logic
            success = self._generate_segment_audio(tts_segment)
            
            if success:
                tts_segments.append(tts_segment)
                self.logger.info(f"Successfully generated TTS for segment {i + 1}")
            else:
                self.logger.error(f"Failed to generate TTS for segment {i + 1}")
                # Continue with other segments rather than failing completely
        
        return tts_segments
    
    def _generate_segment_audio(self, tts_segment: TTSSegment) -> bool:
        """
        🧠 3. TTS Request Structure
        
        Generate TTS audio for a single segment with retry logic and fallback.
        """
        max_attempts = len(self.TTS_MODELS) * len(self.api_keys) * 3  # 3 retries per model/key
        
        for attempt in range(max_attempts):
            try:
                model = self.TTS_MODELS[self.current_model_index]
                api_key = self.api_keys[self.current_key_index]
                
                self.logger.info(f"TTS attempt {attempt + 1} for segment {tts_segment.index}: {model}")
                
                # Make TTS request
                audio_data = self._make_tts_request(tts_segment.text, model, api_key)
                
                if audio_data:
                    # Save audio file
                    audio_filename = f"tts_chunks/segment_{tts_segment.index:03d}.wav"
                    self._save_wave_file(audio_filename, audio_data)
                    
                    # Validate audio file
                    actual_duration = self._get_audio_duration(audio_filename)
                    
                    if actual_duration > 0:
                        tts_segment.audio_file = audio_filename
                        tts_segment.actual_duration = actual_duration
                        
                        self.logger.info(f"Generated TTS audio: {audio_filename} ({actual_duration:.2f}s)")
                        return True
                    else:
                        self.logger.warning(f"Generated audio file has zero duration: {audio_filename}")
                        
            except Exception as e:
                self.logger.warning(f"TTS generation failed for segment {tts_segment.index}: {str(e)}")
                
                # Handle specific error types
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    self.logger.info("Rate limit detected, waiting before retry...")
                    time.sleep(min(2 ** (attempt % 5), 60))
                
                # Rotate to next model/key combination
                self._rotate_to_next_model_key()
        
        # All attempts failed - create fallback
        self.logger.error(f"All TTS attempts failed for segment {tts_segment.index}, creating silence")
        return self._create_fallback_audio(tts_segment)
    
    def _make_tts_request(self, text: str, model: str, api_key: str) -> Optional[bytes]:
        """Make TTS request using exact API specification."""
        try:
            # Configure API key
            genai.configure(api_key=api_key)
            
            # Create model instance
            model_instance = genai.GenerativeModel(model)
            
            # Make TTS request with exact specification
            response = model_instance.generate_content(
                text.strip(),
                generation_config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name
                            )
                        )
                    )
                )
            )
            
            # Extract audio data
            if response and response.candidates:
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                if audio_data and len(audio_data) > 0:
                    return audio_data
            
            raise Exception("No audio data in response")
            
        except Exception as e:
            raise Exception(f"TTS request failed: {str(e)}")
    
    def _optimize_time_matching(self, tts_segments: List[TTSSegment]) -> List[TTSSegment]:
        """
        ⏱️ 4. Time Matching Optimization
        
        Match output audio with original timestamps using FFmpeg.
        """
        aligned_segments = []
        
        for segment in tts_segments:
            self.logger.info(f"Optimizing timing for segment {segment.index}")
            
            # Calculate timing difference
            duration_diff = segment.actual_duration - segment.original_duration
            tolerance = 0.1  # 100ms tolerance
            
            if abs(duration_diff) <= tolerance:
                # Duration is close enough, no adjustment needed
                segment.adjusted_file = segment.audio_file
                aligned_segments.append(segment)
                self.logger.debug(f"Segment {segment.index} timing OK ({duration_diff:.2f}s diff)")
            else:
                # Adjust audio duration
                adjusted_file = self._adjust_audio_duration(segment)
                if adjusted_file:
                    segment.adjusted_file = adjusted_file
                    aligned_segments.append(segment)
                    self.logger.info(f"Adjusted segment {segment.index} timing: {duration_diff:.2f}s")
                else:
                    # Use original file if adjustment fails
                    segment.adjusted_file = segment.audio_file
                    aligned_segments.append(segment)
                    self.logger.warning(f"Failed to adjust segment {segment.index}, using original")
        
        return aligned_segments
    
    def _adjust_audio_duration(self, segment: TTSSegment) -> Optional[str]:
        """Adjust audio duration using FFmpeg."""
        try:
            adjusted_file = f"temp_audio/adjusted_{segment.index:03d}.wav"
            
            if segment.actual_duration > segment.original_duration:
                # Speed up audio slightly
                speed_factor = segment.actual_duration / segment.original_duration
                speed_factor = min(speed_factor, 1.25)  # Max 25% speedup
                
                cmd = [
                    'ffmpeg', '-y', '-i', segment.audio_file,
                    '-filter:a', f'atempo={speed_factor}',
                    adjusted_file
                ]
                
            else:
                # Add pause or stretch duration
                padding_duration = segment.original_duration - segment.actual_duration
                
                cmd = [
                    'ffmpeg', '-y', '-i', segment.audio_file,
                    '-af', f'apad=pad_dur={padding_duration}',
                    '-t', str(segment.original_duration),
                    adjusted_file
                ]
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(adjusted_file):
                return adjusted_file
            else:
                self.logger.warning(f"FFmpeg adjustment failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Audio duration adjustment failed: {str(e)}")
            return None
    
    def _combine_audio_chunks(self, aligned_segments: List[TTSSegment]) -> str:
        """
        🧬 5. Combining All Audio Chunks
        
        Combine all segments with proper timing and gaps.
        """
        if not aligned_segments:
            raise Exception("No aligned segments to combine")
        
        # Sort segments by start time
        sorted_segments = sorted(aligned_segments, key=lambda x: x.start_time)
        
        # Create file list for FFmpeg concat
        concat_file = "temp_audio/concat_list.txt"
        
        try:
            with open(concat_file, 'w') as f:
                current_time = 0.0
                
                for i, segment in enumerate(sorted_segments):
                    # Add silence gap if needed
                    gap = segment.start_time - current_time
                    if gap > 0.1:  # Add silence for gaps > 100ms
                        silence_file = f"temp_audio/silence_{i:03d}.wav"
                        self._create_silence_audio(silence_file, gap)
                        f.write(f"file '{os.path.abspath(silence_file)}'\n")
                    
                    # Add segment audio
                    audio_file = segment.adjusted_file or segment.audio_file
                    f.write(f"file '{os.path.abspath(audio_file)}'\n")
                    
                    current_time = segment.end_time
            
            # Combine using FFmpeg
            final_audio = "final_dubbed_audio.wav"
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_file, '-c', 'copy', final_audio
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(final_audio):
                self.logger.info(f"Successfully combined audio: {final_audio}")
                return final_audio
            else:
                # Fallback: use Python wave library
                return self._combine_audio_python(sorted_segments)
                
        except Exception as e:
            self.logger.error(f"Audio combination failed: {str(e)}")
            # Fallback: use Python wave library
            return self._combine_audio_python(sorted_segments)
    
    def _combine_audio_python(self, segments: List[TTSSegment]) -> str:
        """Fallback audio combination using Python wave library."""
        try:
            import numpy as np
            
            final_audio = "final_dubbed_audio.wav"
            sample_rate = 24000
            combined_audio = []
            current_time = 0.0
            
            for segment in segments:
                # Add silence gap if needed
                gap = segment.start_time - current_time
                if gap > 0.1:
                    silence_samples = int(sample_rate * gap)
                    combined_audio.extend([0] * silence_samples)
                
                # Add segment audio
                audio_file = segment.adjusted_file or segment.audio_file
                try:
                    with wave.open(audio_file, 'rb') as wf:
                        frames = wf.readframes(wf.getnframes())
                        audio_data = np.frombuffer(frames, dtype=np.int16)
                        combined_audio.extend(audio_data)
                except Exception as e:
                    self.logger.warning(f"Failed to read audio file {audio_file}: {str(e)}")
                
                current_time = segment.end_time
            
            # Save combined audio
            if combined_audio:
                combined_array = np.array(combined_audio, dtype=np.int16)
                with wave.open(final_audio, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(combined_array.tobytes())
                
                return final_audio
            
        except Exception as e:
            self.logger.error(f"Python audio combination failed: {str(e)}")
        
        raise Exception("Failed to combine audio chunks")
    
    def _create_fallback_audio(self, tts_segment: TTSSegment) -> bool:
        """Create silence audio as fallback when TTS fails."""
        try:
            silence_file = f"tts_chunks/segment_{tts_segment.index:03d}.wav"
            self._create_silence_audio(silence_file, tts_segment.original_duration)
            
            tts_segment.audio_file = silence_file
            tts_segment.actual_duration = tts_segment.original_duration
            
            self.logger.warning(f"Created silence fallback for segment {tts_segment.index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create fallback audio: {str(e)}")
            return False
    
    def _create_silence_audio(self, filename: str, duration: float):
        """Create silence audio file."""
        import numpy as np
        
        sample_rate = 24000
        samples = int(sample_rate * duration)
        audio_data = np.zeros(samples, dtype=np.int16)
        
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
    
    def _save_wave_file(self, filename: str, audio_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """Save audio data as WAV file."""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(audio_data)
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """Get audio file duration."""
        try:
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0
    
    def _rotate_to_next_model_key(self):
        """Rotate to next model/API key combination."""
        self.current_model_index = (self.current_model_index + 1) % len(self.TTS_MODELS)
        
        # If we've cycled through all models, move to next API key
        if self.current_model_index == 0:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    
    def get_voice_recommendation(self, video_tone: str = "default") -> str:
        """Get recommended voice based on video tone."""
        return self.HINDI_VOICE_RECOMMENDATIONS.get(video_tone.lower(), "Kore")
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            import shutil
            if os.path.exists("temp_audio"):
                shutil.rmtree("temp_audio")
            self.logger.info("Cleaned up temporary files")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {str(e)}")

# 🔄 Error Handling & Fallback Strategy Implementation
class TTSErrorHandler:
    """Enhanced error handling for TTS pipeline."""
    
    @staticmethod
    def handle_tts_failure(segment_index: int, error: Exception, retry_count: int) -> bool:
        """
        Handle TTS failures with smart retry logic:
        1. Retry if blank/error (up to 3 times)
        2. Log failed chunks for manual fallback
        3. Try alternative voice (Puck instead of Kore)
        """
        logger = logging.getLogger(__name__)
        
        if retry_count < 3:
            if "blank" in str(error).lower() or "empty" in str(error).lower():
                logger.warning(f"Blank response for segment {segment_index}, retry {retry_count + 1}")
                return True  # Retry
            
            if "quota" in str(error).lower() or "limit" in str(error).lower():
                wait_time = min(2 ** retry_count, 60)
                logger.info(f"Rate limit for segment {segment_index}, waiting {wait_time}s")
                time.sleep(wait_time)
                return True  # Retry
        
        # Log for manual fallback
        logger.error(f"TTS failed for segment {segment_index} after {retry_count} retries: {str(error)}")
        return False  # Don't retry