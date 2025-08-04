"""
Comprehensive error handling and recovery system for the dubbing pipeline.
Provides centralized error management, recovery strategies, and user-friendly messaging.
"""

import logging
import traceback
import time
import json
import os
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

class ErrorType(Enum):
    """Types of errors that can occur in the pipeline."""
    API_KEY_ERROR = "api_key_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK_ERROR = "network_error"
    FILE_ERROR = "file_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorInfo:
    """Detailed error information."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: str
    timestamp: str
    stage: str
    recoverable: bool
    recovery_suggestions: List[str]
    context: Dict[str, Any]

class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)
    
    def can_recover(self, error_info: ErrorInfo) -> bool:
        """Check if this strategy can recover from the given error."""
        return error_info.recoverable
    
    def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Attempt to recover from the error."""
        raise NotImplementedError("Subclasses must implement recover method")

class APIKeyRotationStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for API key related errors with intelligent rotation."""
    
    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.error_type in [ErrorType.API_KEY_ERROR, ErrorType.QUOTA_EXCEEDED]
    
    def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Rotate to next available healthy API key."""
        from error_handler import global_error_handler  # Import here to avoid circular import
        
        api_keys = context.get('api_keys', [])
        current_key_index = context.get('current_key_index', 0)
        
        # Mark current key as problematic
        if current_key_index < len(api_keys):
            current_key = api_keys[current_key_index]
            global_error_handler.track_api_key_status(
                current_key, 
                success=False, 
                error_type=error_info.error_type
            )
        
        # Get healthy API keys
        healthy_keys = global_error_handler.get_healthy_api_keys(api_keys)
        
        if not healthy_keys:
            # Try graceful degradation
            degraded, message = global_error_handler.implement_graceful_degradation(context)
            if degraded:
                return True, f"Graceful degradation: {message}"
            return False, "All API keys exhausted and no degradation available"
        
        # Find next healthy key
        for i, key in enumerate(api_keys):
            if key in healthy_keys and i != current_key_index:
                context['current_key_index'] = i
                self.logger.info(f"Rotating to healthy API key {i + 1}/{len(api_keys)}")
                return True, f"Rotated to healthy API key {i + 1}/{len(api_keys)}"
        
        # If we're here, current key might still be the only healthy one
        if current_key_index < len(api_keys) and api_keys[current_key_index] in healthy_keys:
            # Wait a bit before retrying the same key
            time.sleep(5)
            return True, "Retrying with current API key after delay"
        
        return False, "No healthy API keys available"

class ModelFallbackStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for model fallback."""
    
    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.error_type in [ErrorType.API_KEY_ERROR, ErrorType.QUOTA_EXCEEDED, ErrorType.PROCESSING_ERROR]
    
    def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Fallback to next available model."""
        fallback_models = context.get('fallback_models', [])
        current_model_index = context.get('current_model_index', 0)
        
        if current_model_index + 1 < len(fallback_models):
            new_index = current_model_index + 1
            context['current_model_index'] = new_index
            new_model = fallback_models[new_index]
            
            self.logger.info(f"Falling back to model: {new_model}")
            return True, f"Switched to fallback model: {new_model}"
        else:
            return False, "All fallback models exhausted"

class RetryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy with intelligent exponential backoff retry."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        super().__init__(max_retries, base_delay)
        self.max_delay = max_delay
    
    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR, ErrorType.PROCESSING_ERROR]
    
    def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Retry with intelligent exponential backoff."""
        retry_count = context.get('retry_count', 0)
        
        if retry_count < self.max_retries:
            # Calculate delay with jitter to avoid thundering herd
            base_delay = self.base_delay * (2 ** retry_count)
            jitter = base_delay * 0.1 * (time.time() % 1)  # Add up to 10% jitter
            delay = min(base_delay + jitter, self.max_delay)
            
            context['retry_count'] = retry_count + 1
            
            # Adjust delay based on error type
            if error_info.error_type == ErrorType.NETWORK_ERROR:
                delay *= 1.5  # Longer delay for network issues
            elif error_info.error_type == ErrorType.TIMEOUT_ERROR:
                delay *= 2.0  # Even longer delay for timeouts
            
            delay = min(delay, self.max_delay)
            
            self.logger.info(f"Retrying in {delay:.1f}s (attempt {retry_count + 1}/{self.max_retries})")
            time.sleep(delay)
            
            return True, f"Retrying after {delay:.1f}s delay (attempt {retry_count + 1}/{self.max_retries})"
        else:
            return False, f"Maximum retry attempts ({self.max_retries}) exceeded"

class FileRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for file-related errors."""
    
    def can_recover(self, error_info: ErrorInfo) -> bool:
        return error_info.error_type == ErrorType.FILE_ERROR
    
    def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Attempt to recover from file errors."""
        file_path = context.get('file_path', '')
        
        # Try to create missing directories
        if "No such file or directory" in error_info.details:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                return True, f"Created missing directory for {file_path}"
            except Exception as e:
                return False, f"Failed to create directory: {str(e)}"
        
        # Try to recover corrupted files
        if "corrupted" in error_info.details.lower() or "invalid" in error_info.details.lower():
            backup_path = file_path + ".backup"
            if os.path.exists(backup_path):
                try:
                    os.replace(backup_path, file_path)
                    return True, f"Restored from backup: {backup_path}"
                except Exception as e:
                    return False, f"Failed to restore from backup: {str(e)}"
        
        return False, "No file recovery strategy available"

class ErrorHandler:
    """Comprehensive error handler with recovery strategies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: List[ErrorRecoveryStrategy] = [
            APIKeyRotationStrategy(),
            ModelFallbackStrategy(),
            RetryStrategy(),
            FileRecoveryStrategy()
        ]
        self.api_key_status: Dict[str, Dict] = {}  # Track API key health
        self.model_status: Dict[str, Dict] = {}    # Track model availability
        self.graceful_degradation_enabled = True
        
    def classify_error(self, exception: Exception, stage: str, context: Dict[str, Any]) -> ErrorInfo:
        """Classify an error and create ErrorInfo."""
        error_str = str(exception).lower()
        error_type = ErrorType.UNKNOWN_ERROR
        severity = ErrorSeverity.MEDIUM
        recoverable = True
        recovery_suggestions = []
        
        # Classify error type
        if any(keyword in error_str for keyword in ["api key", "authentication", "unauthorized"]):
            error_type = ErrorType.API_KEY_ERROR
            severity = ErrorSeverity.HIGH
            recovery_suggestions = [
                "Check API key validity",
                "Verify API key permissions",
                "Try rotating to another API key"
            ]
        elif any(keyword in error_str for keyword in ["quota", "limit", "rate limit"]):
            error_type = ErrorType.QUOTA_EXCEEDED
            severity = ErrorSeverity.HIGH
            recovery_suggestions = [
                "Wait for quota reset",
                "Use additional API keys",
                "Switch to different model"
            ]
        elif any(keyword in error_str for keyword in ["network", "connection", "timeout", "dns"]):
            error_type = ErrorType.NETWORK_ERROR
            severity = ErrorSeverity.MEDIUM
            recovery_suggestions = [
                "Check internet connection",
                "Retry after a short delay",
                "Check firewall settings"
            ]
        elif any(keyword in error_str for keyword in ["file", "directory", "path", "permission"]):
            error_type = ErrorType.FILE_ERROR
            severity = ErrorSeverity.MEDIUM
            recovery_suggestions = [
                "Check file permissions",
                "Verify file paths exist",
                "Ensure sufficient disk space"
            ]
        elif any(keyword in error_str for keyword in ["validation", "invalid", "format"]):
            error_type = ErrorType.VALIDATION_ERROR
            severity = ErrorSeverity.LOW
            recoverable = False
            recovery_suggestions = [
                "Check input format",
                "Validate data structure",
                "Review input requirements"
            ]
        elif any(keyword in error_str for keyword in ["timeout", "timed out"]):
            error_type = ErrorType.TIMEOUT_ERROR
            severity = ErrorSeverity.MEDIUM
            recovery_suggestions = [
                "Increase timeout duration",
                "Retry the operation",
                "Check system resources"
            ]
        else:
            error_type = ErrorType.PROCESSING_ERROR
            recovery_suggestions = [
                "Review error details",
                "Check system resources",
                "Retry the operation"
            ]
        
        return ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(exception),
            details=traceback.format_exc(),
            timestamp=datetime.now().isoformat(),
            stage=stage,
            recoverable=recoverable,
            recovery_suggestions=recovery_suggestions,
            context=context.copy()
        )
    
    def handle_error(self, exception: Exception, stage: str, context: Dict[str, Any]) -> Tuple[bool, str, ErrorInfo]:
        """Handle an error with recovery attempts."""
        error_info = self.classify_error(exception, stage, context)
        self.error_history.append(error_info)
        
        self.logger.error(f"Error in {stage}: {error_info.message}")
        self.logger.debug(f"Error details: {error_info.details}")
        
        # Save error to log file
        self._save_error_log(error_info)
        
        # Attempt recovery if error is recoverable
        if error_info.recoverable:
            for strategy in self.recovery_strategies:
                if strategy.can_recover(error_info):
                    try:
                        recovered, recovery_message = strategy.recover(error_info, context)
                        if recovered:
                            self.logger.info(f"Recovery successful: {recovery_message}")
                            return True, recovery_message, error_info
                    except Exception as recovery_error:
                        self.logger.warning(f"Recovery strategy failed: {str(recovery_error)}")
                        continue
        
        # No recovery possible
        user_message = self._format_user_error_message(error_info)
        return False, user_message, error_info
    
    def _save_error_log(self, error_info: ErrorInfo):
        """Save error information to log file."""
        try:
            log_entry = {
                "timestamp": error_info.timestamp,
                "stage": error_info.stage,
                "error_type": error_info.error_type.value,
                "severity": error_info.severity.value,
                "message": error_info.message,
                "recoverable": error_info.recoverable,
                "recovery_suggestions": error_info.recovery_suggestions
            }
            
            log_file = "error_log.json"
            
            # Load existing log or create new
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
            else:
                log_data = {"errors": []}
            
            log_data["errors"].append(log_entry)
            
            # Keep only last 100 errors
            if len(log_data["errors"]) > 100:
                log_data["errors"] = log_data["errors"][-100:]
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.warning(f"Failed to save error log: {str(e)}")
    
    def _format_user_error_message(self, error_info: ErrorInfo) -> str:
        """Format error message for user display."""
        stage_context = {
            "initialization": "during system startup",
            "asr": "during transcription",
            "translation": "during translation",
            "tts": "during text-to-speech generation",
            "audio_processing": "during audio processing",
            "video_creation": "during video creation"
        }
        
        context_msg = stage_context.get(error_info.stage, f"in {error_info.stage}")
        
        if error_info.error_type == ErrorType.API_KEY_ERROR:
            return f"API key error {context_msg}. Please check your Gemini API keys and ensure they are valid and have sufficient permissions."
        elif error_info.error_type == ErrorType.QUOTA_EXCEEDED:
            return f"API quota exceeded {context_msg}. Please wait for quota reset or use additional API keys."
        elif error_info.error_type == ErrorType.NETWORK_ERROR:
            return f"Network error {context_msg}. Please check your internet connection and try again."
        elif error_info.error_type == ErrorType.FILE_ERROR:
            return f"File error {context_msg}. Please check file permissions and ensure all required files exist."
        elif error_info.error_type == ErrorType.VALIDATION_ERROR:
            return f"Validation error {context_msg}. Please check your input format and try again."
        elif error_info.error_type == ErrorType.TIMEOUT_ERROR:
            return f"Timeout error {context_msg}. The operation took too long. Please try again."
        else:
            return f"An error occurred {context_msg}: {error_info.message}"
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        if not self.error_history:
            return {"total_errors": 0, "recent_errors": []}
        
        recent_errors = self.error_history[-10:]  # Last 10 errors
        
        error_counts = {}
        for error in recent_errors:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "error_types": error_counts,
            "last_error": {
                "timestamp": recent_errors[-1].timestamp,
                "stage": recent_errors[-1].stage,
                "type": recent_errors[-1].error_type.value,
                "message": recent_errors[-1].message
            } if recent_errors else None
        }
    
    def get_recovery_suggestions(self, error_type: ErrorType) -> List[str]:
        """Get recovery suggestions for a specific error type."""
        suggestions_map = {
            ErrorType.API_KEY_ERROR: [
                "Verify your Gemini API keys are valid",
                "Check API key permissions and quotas",
                "Ensure API keys are properly formatted",
                "Try using different API keys"
            ],
            ErrorType.QUOTA_EXCEEDED: [
                "Wait for quota reset (usually 24 hours)",
                "Use additional API keys to distribute load",
                "Switch to different Gemini models",
                "Reduce request frequency"
            ],
            ErrorType.NETWORK_ERROR: [
                "Check your internet connection",
                "Verify firewall and proxy settings",
                "Try again after a short delay",
                "Check if the service is available"
            ],
            ErrorType.FILE_ERROR: [
                "Check file and directory permissions",
                "Ensure sufficient disk space",
                "Verify file paths are correct",
                "Check if files are not locked by other processes"
            ],
            ErrorType.VALIDATION_ERROR: [
                "Review input data format",
                "Check required fields are present",
                "Validate data types and ranges",
                "Refer to documentation for correct format"
            ],
            ErrorType.TIMEOUT_ERROR: [
                "Increase timeout duration",
                "Check system resources (CPU, memory)",
                "Try processing smaller chunks",
                "Retry the operation"
            ]
        }
        
        return suggestions_map.get(error_type, ["Review error details and try again"])
    
    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()
        self.logger.info("Error history cleared")
    
    def track_api_key_status(self, api_key: str, success: bool, error_type: Optional[ErrorType] = None):
        """Track API key health and quota status."""
        key_hash = api_key[:10] + "..." if len(api_key) > 10 else api_key
        
        if key_hash not in self.api_key_status:
            self.api_key_status[key_hash] = {
                'success_count': 0,
                'error_count': 0,
                'last_success': None,
                'last_error': None,
                'quota_exhausted': False,
                'quota_reset_time': None,
                'consecutive_failures': 0
            }
        
        status = self.api_key_status[key_hash]
        
        if success:
            status['success_count'] += 1
            status['last_success'] = datetime.now().isoformat()
            status['consecutive_failures'] = 0
            status['quota_exhausted'] = False
        else:
            status['error_count'] += 1
            status['last_error'] = datetime.now().isoformat()
            status['consecutive_failures'] += 1
            
            if error_type == ErrorType.QUOTA_EXCEEDED:
                status['quota_exhausted'] = True
                # Estimate quota reset time (typically 24 hours)
                reset_time = datetime.now().timestamp() + (24 * 60 * 60)
                status['quota_reset_time'] = reset_time
    
    def get_healthy_api_keys(self, api_keys: List[str]) -> List[str]:
        """Get list of healthy API keys that are not quota exhausted."""
        healthy_keys = []
        current_time = datetime.now().timestamp()
        
        for api_key in api_keys:
            key_hash = api_key[:10] + "..." if len(api_key) > 10 else api_key
            status = self.api_key_status.get(key_hash, {})
            
            # Check if quota is exhausted and if reset time has passed
            if status.get('quota_exhausted', False):
                reset_time = status.get('quota_reset_time', 0)
                if current_time < reset_time:
                    self.logger.debug(f"API key {key_hash} still quota exhausted")
                    continue
                else:
                    # Reset quota status
                    status['quota_exhausted'] = False
                    status['quota_reset_time'] = None
                    self.logger.info(f"API key {key_hash} quota reset")
            
            # Check consecutive failures
            if status.get('consecutive_failures', 0) < 5:  # Allow up to 5 consecutive failures
                healthy_keys.append(api_key)
            else:
                self.logger.debug(f"API key {key_hash} has too many consecutive failures")
        
        return healthy_keys
    
    def implement_graceful_degradation(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Implement graceful degradation when all API keys are exhausted."""
        if not self.graceful_degradation_enabled:
            return False, "Graceful degradation is disabled"
        
        stage = context.get('stage', 'unknown')
        
        # Different degradation strategies based on stage
        if stage == 'translation':
            return self._degrade_translation_service(context)
        elif stage == 'tts':
            return self._degrade_tts_service(context)
        else:
            return False, f"No graceful degradation available for stage: {stage}"
    
    def _degrade_translation_service(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Graceful degradation for translation service."""
        # Option 1: Use cached translations if available
        segments = context.get('segments', [])
        if self._has_cached_translations(segments):
            self.logger.info("Using cached translations for graceful degradation")
            return True, "Using cached translations due to API limitations"
        
        # Option 2: Provide template for manual translation
        if self._can_generate_manual_template(segments):
            self.logger.info("Generating manual translation template")
            return True, "API quota exhausted. Please use manual translation mode."
        
        # Option 3: Suggest reducing content size
        if len(segments) > 10:
            suggested_size = len(segments) // 2
            return True, f"API quota exhausted. Consider processing in smaller batches (try {suggested_size} segments at a time)."
        
        return False, "All translation options exhausted"
    
    def _degrade_tts_service(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Graceful degradation for TTS service."""
        # Option 1: Use cached TTS if available
        segments = context.get('segments', [])
        if self._has_cached_tts(segments):
            self.logger.info("Using cached TTS for graceful degradation")
            return True, "Using cached TTS audio due to API limitations"
        
        # Option 2: Suggest alternative TTS services
        return True, "TTS API quota exhausted. Consider using alternative TTS services or waiting for quota reset."
    
    def _has_cached_translations(self, segments: List[Dict]) -> bool:
        """Check if cached translations are available."""
        # Implementation would check for cached translation files
        return os.path.exists("translated.json")
    
    def _can_generate_manual_template(self, segments: List[Dict]) -> bool:
        """Check if manual translation template can be generated."""
        return len(segments) > 0 and os.path.exists("original_asr.json")
    
    def _has_cached_tts(self, segments: List[Dict]) -> bool:
        """Check if cached TTS audio is available."""
        return os.path.exists("tts_chunks") and len(os.listdir("tts_chunks")) > 0
    
    def get_user_friendly_error_message(self, error_info: ErrorInfo, context: Dict[str, Any] = None) -> str:
        """Generate user-friendly error messages with actionable suggestions."""
        if context is None:
            context = {}
        
        base_message = self._format_user_error_message(error_info)
        
        # Add specific suggestions based on error type and context
        suggestions = []
        
        if error_info.error_type == ErrorType.API_KEY_ERROR:
            healthy_keys = len(self.get_healthy_api_keys(context.get('api_keys', [])))
            if healthy_keys == 0:
                suggestions.append("All API keys appear to be invalid. Please check your Gemini API keys.")
                suggestions.append("Visit https://makersuite.google.com/app/apikey to verify your keys.")
            else:
                suggestions.append(f"{healthy_keys} API key(s) still available. The system will retry automatically.")
        
        elif error_info.error_type == ErrorType.QUOTA_EXCEEDED:
            exhausted_keys = sum(1 for status in self.api_key_status.values() if status.get('quota_exhausted', False))
            total_keys = len(context.get('api_keys', []))
            
            if exhausted_keys == total_keys:
                suggestions.append("All API keys have reached their quota limit.")
                suggestions.append("Quotas typically reset after 24 hours.")
                suggestions.append("Consider upgrading your API plan or adding more keys.")
            else:
                remaining_keys = total_keys - exhausted_keys
                suggestions.append(f"{remaining_keys} API key(s) still have quota available.")
        
        elif error_info.error_type == ErrorType.NETWORK_ERROR:
            suggestions.append("Check your internet connection and try again.")
            suggestions.append("If the problem persists, the service may be temporarily unavailable.")
        
        elif error_info.error_type == ErrorType.FILE_ERROR:
            file_path = context.get('file_path', 'unknown file')
            suggestions.append(f"Check that the file '{file_path}' exists and is accessible.")
            suggestions.append("Ensure you have read/write permissions for the file location.")
        
        # Combine base message with suggestions
        if suggestions:
            suggestion_text = "\n\nSuggestions:\n" + "\n".join(f"• {s}" for s in suggestions)
            return base_message + suggestion_text
        
        return base_message
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get comprehensive recovery status information."""
        return {
            'api_key_status': self.api_key_status,
            'model_status': self.model_status,
            'total_errors': len(self.error_history),
            'recent_error_types': [e.error_type.value for e in self.error_history[-10:]],
            'graceful_degradation_enabled': self.graceful_degradation_enabled,
            'recovery_strategies_available': len(self.recovery_strategies)
        }

# Global error handler instance
global_error_handler = ErrorHandler()

def handle_pipeline_error(stage: str, context: Dict[str, Any] = None, max_recovery_attempts: int = 3):
    """Enhanced decorator for handling pipeline errors with comprehensive recovery."""
    if context is None:
        context = {}
    
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            recovery_attempts = 0
            last_error = None
            
            while recovery_attempts <= max_recovery_attempts:
                try:
                    # Reset retry count for each recovery attempt
                    if recovery_attempts > 0:
                        context['retry_count'] = 0
                    
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    recovery_attempts += 1
                    
                    # Handle the error
                    recovered, message, error_info = global_error_handler.handle_error(e, stage, context)
                    
                    if not recovered:
                        # Generate user-friendly error message
                        user_message = global_error_handler.get_user_friendly_error_message(error_info, context)
                        raise Exception(user_message) from e
                    
                    # Log recovery attempt
                    global_error_handler.logger.info(f"Recovery attempt {recovery_attempts}/{max_recovery_attempts}: {message}")
                    
                    # If this was the last recovery attempt, fail
                    if recovery_attempts > max_recovery_attempts:
                        break
            
            # All recovery attempts failed
            user_message = global_error_handler.get_user_friendly_error_message(
                global_error_handler.classify_error(last_error, stage, context), 
                context
            )
            raise Exception(f"All recovery attempts failed. {user_message}") from last_error
            
        return wrapper
    return decorator

class PipelineErrorContext:
    """Context manager for pipeline error handling with automatic cleanup."""
    
    def __init__(self, stage: str, context: Dict[str, Any] = None):
        self.stage = stage
        self.context = context or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        global_error_handler.logger.info(f"Starting pipeline stage: {self.stage}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            global_error_handler.logger.info(f"Pipeline stage '{self.stage}' completed successfully in {duration:.2f}s")
            return False
        
        # Handle the exception
        try:
            recovered, message, error_info = global_error_handler.handle_error(exc_val, self.stage, self.context)
            
            if recovered:
                global_error_handler.logger.info(f"Pipeline stage '{self.stage}' recovered: {message}")
                return True  # Suppress the exception
            else:
                user_message = global_error_handler.get_user_friendly_error_message(error_info, self.context)
                global_error_handler.logger.error(f"Pipeline stage '{self.stage}' failed after {duration:.2f}s: {user_message}")
                
                # Replace the original exception with a user-friendly one
                raise Exception(user_message) from exc_val
                
        except Exception as handler_error:
            global_error_handler.logger.error(f"Error handler itself failed: {str(handler_error)}")
            return False  # Let the original exception propagate

def with_error_recovery(stage: str, **context_kwargs):
    """Simplified decorator for error recovery."""
    return handle_pipeline_error(stage, context_kwargs)

def create_error_context(stage: str, **context_kwargs) -> PipelineErrorContext:
    """Create an error context manager."""
    return PipelineErrorContext(stage, context_kwargs)