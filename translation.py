"""
Translation service using Google Gemini API with fallback model support.
Handles translation of ASR segments with style configuration and error recovery.
"""

import json
import logging
import time
import tiktoken
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from config import PIPELINE_DEFAULTS, ERROR_MESSAGES

# Translation models in exact priority order from master prompt
TRANSLATION_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-pro-preview-06-05",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-pro-preview-03-25",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-pro",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-1.5-pro-002",
    "gemini-1.5-pro-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-001"
]
from state_manager import StateManager
from error_handler import global_error_handler, handle_pipeline_error, create_error_context

@dataclass
class TranslatedSegment:
    """Data model for translated segment with timing information."""
    start: float
    end: float
    text_translated: str
    original_text: str = ""

class TranslationService:
    """Service for translating ASR segments using Gemini API with fallback support."""
    
    def __init__(self, api_keys: List[str]):
        """Initialize translation service with API keys."""
        if not GENAI_AVAILABLE:
            raise ImportError("Google Generative AI library not available. Please install: pip install google-generativeai")
            
        if not api_keys:
            raise ValueError(ERROR_MESSAGES["no_api_keys"])
            
        self.api_keys = api_keys
        self.current_key_index = 0
        self.current_model_index = 0
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_retries = PIPELINE_DEFAULTS["max_retry_attempts"]
        
    @handle_pipeline_error("translation", max_recovery_attempts=5)
    def translate_segments(self, segments: List[Dict], style_config: Dict) -> List[TranslatedSegment]:
        """
        Translate a list of ASR segments with style configuration and comprehensive error handling.
        
        Args:
            segments: List of segments with start, end, text fields
            style_config: Dictionary with tone, dialect, genre settings
            
        Returns:
            List of TranslatedSegment objects
        """
        if not segments:
            self.logger.warning("No segments provided for translation")
            return []
        
        # Create error context with relevant information
        context = {
            'stage': 'translation',
            'api_keys': self.api_keys,
            'segments': segments,
            'segment_count': len(segments),
            'current_key_index': self.current_key_index,
            'current_model_index': self.current_model_index
        }
        
        with create_error_context("translation", **context) as error_ctx:
            self.logger.info(f"Starting translation of {len(segments)} segments")
            
            # Calculate total tokens for logging
            total_tokens = self._calculate_total_tokens(segments)
            self.logger.info(f"Total tokens to translate: {total_tokens}")
            context['token_count'] = total_tokens
            
            # Check if we need to batch the request
            if total_tokens > 100000:  # Large request, consider batching
                return self._translate_in_batches(segments, style_config)
            
            # Get healthy API keys
            healthy_keys = global_error_handler.get_healthy_api_keys(self.api_keys)
            if not healthy_keys:
                # Try graceful degradation
                degraded, message = global_error_handler.implement_graceful_degradation(context)
                if degraded:
                    raise Exception(f"Translation service degraded: {message}")
                else:
                    raise Exception("All API keys are exhausted and no graceful degradation is available")
            
            # Update context with healthy keys
            context['healthy_api_keys'] = healthy_keys
            
            # Prepare translation request
            system_prompt = self._build_system_prompt(style_config)
            
            # Use enhanced translation logic with error tracking
            return self._translate_with_error_tracking(segments, system_prompt, context)
    
    def _translate_with_error_tracking(self, segments: List[Dict], system_prompt: str, context: Dict[str, Any]) -> List[TranslatedSegment]:
        """Translate segments with comprehensive error tracking and recovery."""
        healthy_keys = context.get('healthy_api_keys', self.api_keys)
        max_attempts = len(TRANSLATION_MODELS) * len(healthy_keys)
        
        for attempt in range(max_attempts):
            try:
                model = TRANSLATION_MODELS[self.current_model_index]
                
                # Use healthy keys only
                if self.current_key_index >= len(healthy_keys):
                    self.current_key_index = 0
                
                api_key = healthy_keys[self.current_key_index] if healthy_keys else self.api_keys[self.current_key_index]
                
                self.logger.info(f"Translation attempt {attempt + 1}/{max_attempts}: {model} with key {self.current_key_index + 1}")
                
                # Track API key usage
                global_error_handler.track_api_key_status(api_key, success=True)
                
                result = self._make_translation_request(segments, system_prompt, model, api_key)
                
                if result:
                    # Log successful API request
                    self.state_manager.log_api_request(
                        service="translation",
                        model=model,
                        api_key_index=self.current_key_index,
                        success=True,
                        segment_count=len(segments),
                        token_count=context.get('token_count', 0)
                    )
                    
                    # Track successful API key usage
                    global_error_handler.track_api_key_status(api_key, success=True)
                    
                    self.logger.info("Translation completed successfully")
                    return self._parse_translation_result(result, segments)
                    
            except Exception as e:
                # Track failed API key usage
                if 'api_key' in locals():
                    error_type = self._classify_api_error(e)
                    global_error_handler.track_api_key_status(api_key, success=False, error_type=error_type)
                
                # Log failed API request
                self.state_manager.log_api_request(
                    service="translation",
                    model=model,
                    api_key_index=self.current_key_index,
                    success=False,
                    error_msg=str(e),
                    segment_count=len(segments),
                    token_count=context.get('token_count', 0)
                )
                
                self.logger.warning(f"Translation failed with {model}: {str(e)}")
                
                # Handle specific error types
                if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    # Mark key as quota exhausted
                    global_error_handler.track_api_key_status(api_key, success=False, error_type=self._classify_api_error(e))
                    
                    # Wait with exponential backoff
                    wait_time = min(2 ** (attempt % 5), 60)
                    self.logger.info(f"Rate limit detected, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                
                # Rotate to next model/key combination
                self._rotate_to_next_model_key()
                
                # Update healthy keys list
                healthy_keys = global_error_handler.get_healthy_api_keys(self.api_keys)
                if not healthy_keys:
                    # All keys exhausted, try graceful degradation
                    degraded, message = global_error_handler.implement_graceful_degradation(context)
                    if degraded:
                        raise Exception(f"Translation service degraded: {message}")
                    else:
                        raise Exception("All API keys exhausted during translation")
        
        # All attempts failed
        raise Exception("Translation failed after all recovery attempts")
    
    def _classify_api_error(self, exception: Exception) -> 'ErrorType':
        """Classify API errors for proper tracking."""
        from error_handler import ErrorType
        
        error_str = str(exception).lower()
        
        if any(keyword in error_str for keyword in ["api key", "authentication", "unauthorized"]):
            return ErrorType.API_KEY_ERROR
        elif any(keyword in error_str for keyword in ["quota", "limit", "rate limit"]):
            return ErrorType.QUOTA_EXCEEDED
        elif any(keyword in error_str for keyword in ["network", "connection", "timeout"]):
            return ErrorType.NETWORK_ERROR
        else:
            return ErrorType.PROCESSING_ERROR
    
    def _build_system_prompt(self, style_config: Dict) -> str:
        """Build system prompt with style configuration for Hindi translation."""
        tone = style_config.get('tone', 'neutral')
        dialect = style_config.get('dialect', 'hindi_devanagari')
        genre = style_config.get('genre', 'general')
        
        return f"""Translate the following English lines to Hindi, preserving character names. Use Devanagari script even for English words commonly used by Indians. Style: {tone}, Dialect: {dialect}, Genre: {genre}.

Input payload: {{ segments: [ {{start,end,text}}, … ] }}.
Return: JSON array of {{start, end, text_translated}} in the same order.

Example:
Input: "Hey Zoro, are you ready?"
Output: "हे ज़ोरो, आर यू रेडी?"

Input: "Luffy, I was born ready."
Output: "लूफी, मैं तो रेडी पैदा हुआ था।"

Maintain Hindi-English blend as commonly used by Indian speakers."""
    
    def _make_translation_request(self, segments: List[Dict], system_prompt: str, model: str, api_key: str) -> Optional[Dict]:
        """Make translation request to Gemini API following exact specifications."""
        try:
            # Configure API key exactly as specified
            genai.configure(api_key=api_key)
            
            # Prepare input payload exactly as specified in master prompt
            input_data = {"segments": segments}
            
            # Add retry logic for transient failures
            for retry in range(self.max_retries):
                try:
                    # Use the exact API pattern from specifications
                    response = genai.GenerativeModel(model).generate_content(
                        json.dumps(input_data, ensure_ascii=False),
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=8192,
                            response_mime_type="application/json"
                        )
                    )
                    
                    # Validate response
                    if not response.text:
                        raise Exception("Empty response from API")
                        
                    result = json.loads(response.text)
                    
                    # Validate result structure
                    if not isinstance(result, list):
                        raise Exception("Response is not a list")
                        
                    if len(result) != len(segments):
                        self.logger.warning(f"Response length ({len(result)}) doesn't match input length ({len(segments)})")
                        
                    return result
                    
                except json.JSONDecodeError as e:
                    if retry < self.max_retries - 1:
                        self.logger.warning(f"JSON decode error on retry {retry + 1}: {str(e)}")
                        time.sleep(2 ** retry)  # Exponential backoff
                        continue
                    else:
                        raise Exception(f"Invalid JSON response after {self.max_retries} retries: {str(e)}")
                        
                except Exception as e:
                    if retry < self.max_retries - 1 and "timeout" in str(e).lower():
                        self.logger.warning(f"Timeout on retry {retry + 1}, retrying...")
                        time.sleep(2 ** retry)
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            categorized_error = self._handle_api_error(e, model, self.current_key_index)
            raise Exception(categorized_error)
    
    def _parse_translation_result(self, result: List[Dict], original_segments: List[Dict]) -> List[TranslatedSegment]:
        """Parse translation result into TranslatedSegment objects with validation."""
        translated_segments = []
        
        for i, translated_item in enumerate(result):
            original = original_segments[i] if i < len(original_segments) else {}
            
            # Validate translated item structure
            if not isinstance(translated_item, dict):
                self.logger.warning(f"Translated item {i} is not a dictionary, skipping")
                continue
                
            # Extract translated text with fallback
            text_translated = translated_item.get('text_translated', 
                                                translated_item.get('translated_text', 
                                                                   translated_item.get('text', '')))
            
            if not text_translated:
                self.logger.warning(f"No translated text found for segment {i}, using original")
                text_translated = original.get('text', '')
            
            # Preserve original timing or use provided timing
            start_time = translated_item.get('start', original.get('start', 0.0))
            end_time = translated_item.get('end', original.get('end', 0.0))
            
            # Validate timing
            if start_time >= end_time:
                self.logger.warning(f"Invalid timing for segment {i}, using original timing")
                start_time = original.get('start', 0.0)
                end_time = original.get('end', 0.0)
            
            segment = TranslatedSegment(
                start=float(start_time),
                end=float(end_time),
                text_translated=str(text_translated).strip(),
                original_text=original.get('text', '')
            )
            translated_segments.append(segment)
            
        self.logger.info(f"Successfully parsed {len(translated_segments)} translated segments")
        return translated_segments
    
    def _calculate_total_tokens(self, segments: List[Dict]) -> int:
        """Calculate total tokens for all segments."""
        total_tokens = 0
        for segment in segments:
            text = segment.get('text', '')
            total_tokens += len(self.tokenizer.encode(text))
        return total_tokens
    
    def _translate_in_batches(self, segments: List[Dict], style_config: Dict, batch_size: int = 50) -> List[TranslatedSegment]:
        """
        Translate segments in batches to handle large requests.
        
        Args:
            segments: List of segments to translate
            style_config: Style configuration
            batch_size: Number of segments per batch
            
        Returns:
            List of TranslatedSegment objects
        """
        self.logger.info(f"Translating in batches of {batch_size} segments")
        
        all_translated = []
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            self.logger.info(f"Translating batch {i//batch_size + 1}/{(len(segments) + batch_size - 1)//batch_size}")
            
            batch_translated = self.translate_segments(batch, style_config)
            all_translated.extend(batch_translated)
            
            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(segments):
                time.sleep(1)
                
        return all_translated
    
    def validate_segments(self, segments: List[Dict]) -> bool:
        """
        Validate that segments have required fields.
        
        Args:
            segments: List of segments to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['start', 'end', 'text']
        
        for i, segment in enumerate(segments):
            for field in required_fields:
                if field not in segment:
                    self.logger.error(f"Segment {i} missing required field: {field}")
                    return False
                    
            # Validate timing
            if segment['start'] >= segment['end']:
                self.logger.error(f"Segment {i} has invalid timing: start={segment['start']}, end={segment['end']}")
                return False
                
        return True
    
    def _handle_api_error(self, error: Exception, model: str, api_key_index: int) -> str:
        """
        Handle and categorize API errors for better error reporting.
        
        Args:
            error: The exception that occurred
            model: Model name that failed
            api_key_index: Index of API key that failed
            
        Returns:
            Categorized error message
        """
        error_str = str(error).lower()
        
        if "quota" in error_str or "limit" in error_str:
            return f"Quota/Rate limit exceeded for {model} (key {api_key_index + 1})"
        elif "authentication" in error_str or "api key" in error_str:
            return f"Authentication failed for {model} (key {api_key_index + 1})"
        elif "network" in error_str or "connection" in error_str:
            return f"Network error for {model} (key {api_key_index + 1})"
        elif "timeout" in error_str:
            return f"Request timeout for {model} (key {api_key_index + 1})"
        else:
            return f"Unknown error for {model} (key {api_key_index + 1}): {str(error)}"
    
    def _rotate_to_next_model_key(self):
        """Rotate to next model/API key combination."""
        self.current_model_index = (self.current_model_index + 1) % len(TRANSLATION_MODELS)
        
        # If we've cycled through all models, move to next API key
        if self.current_model_index == 0:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
    def get_current_model_info(self) -> Dict:
        """Get information about current model and API key being used."""
        return {
            'model': TRANSLATION_MODELS[self.current_model_index],
            'api_key_index': self.current_key_index,
            'total_models': len(TRANSLATION_MODELS),
            'total_keys': len(self.api_keys)
        }