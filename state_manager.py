"""
State management for pipeline persistence and recovery.
Handles saving/loading pipeline state and comprehensive logging.
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime

class StateManager:
    """Manages pipeline state persistence and logging."""
    
    def __init__(self):
        """Initialize state manager with logging configuration."""
        self.state_file = 'pipeline_state.json'
        self.log_file = 'pipeline.log'
        
        # Configure logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def _setup_logging(self):
        """Configure comprehensive logging system."""
        # Remove existing handlers to avoid duplicates
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
    def cleanup_logging(self):
        """Clean up logging handlers to prevent file locking issues."""
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
            logger.removeHandler(handler)
        
    def save_pipeline_state(self, state_update: Dict):
        """
        Save or update pipeline state.
        
        Args:
            state_update: Dictionary with state updates to merge
        """
        # Load existing state
        current_state = self.load_pipeline_state()
        
        # Merge updates
        current_state.update(state_update)
        current_state['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        with open(self.state_file, 'w') as f:
            json.dump(current_state, f, indent=2)
            
        self.logger.info(f"Pipeline state updated: {state_update}")
        
    def load_pipeline_state(self) -> Dict:
        """
        Load current pipeline state.
        
        Returns:
            Dictionary with current state or empty dict if no state exists
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Could not load pipeline state: {str(e)}")
                return {}
        return {}
        
    def detect_current_stage(self) -> str:
        """
        Detect current pipeline stage based on existing files.
        
        Returns:
            String indicating current stage
        """
        if not os.path.exists('original_asr.json'):
            return 'asr_needed'
        elif not os.path.exists('translated.json'):
            return 'translation_needed'
        elif not os.path.exists('tts_chunks') or not os.listdir('tts_chunks'):
            return 'tts_needed'
        elif not os.path.exists('output_dubbed.mp4'):
            return 'stitching_needed'
        else:
            return 'complete'
            
    def log_api_request(self, service: str, model: str, api_key_index: int, success: bool, error_msg: Optional[str] = None, **kwargs):
        """
        Log API request details for monitoring and debugging.
        
        Args:
            service: Service name (translation, tts)
            model: Model name used
            api_key_index: Index of API key used (not the actual key)
            success: Whether request succeeded
            error_msg: Error message if failed
            **kwargs: Additional metadata (token_count, duration, etc.)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'model': model,
            'api_key_index': api_key_index,
            'success': success,
            'error': error_msg,
            **kwargs
        }
        
        # Also save to structured log file for analysis
        self._save_structured_log(log_entry)
        
        if success:
            extra_info = f" ({kwargs.get('token_count', 'N/A')} tokens)" if 'token_count' in kwargs else ""
            self.logger.info(f"API Success - {service}/{model} (key {api_key_index + 1}){extra_info}")
        else:
            self.logger.error(f"API Failed - {service}/{model} (key {api_key_index + 1}): {error_msg}")
            
    def _save_structured_log(self, log_entry: Dict):
        """Save structured log entry to JSON log file for analysis."""
        structured_log_file = 'pipeline_api_log.json'
        
        # Load existing logs
        logs = []
        if os.path.exists(structured_log_file):
            try:
                with open(structured_log_file, 'r') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                logs = []
                
        # Add new entry
        logs.append(log_entry)
        
        # Keep only last 1000 entries to prevent file from growing too large
        if len(logs) > 1000:
            logs = logs[-1000:]
            
        # Save back to file
        try:
            with open(structured_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except IOError as e:
            self.logger.warning(f"Could not save structured log: {str(e)}")
            
    def get_api_usage_stats(self) -> Dict:
        """
        Get API usage statistics from structured logs.
        
        Returns:
            Dictionary with usage statistics
        """
        structured_log_file = 'pipeline_api_log.json'
        
        if not os.path.exists(structured_log_file):
            return {'total_requests': 0, 'success_rate': 0, 'services': {}}
            
        try:
            with open(structured_log_file, 'r') as f:
                logs = json.load(f)
                
            # Calculate statistics
            total_requests = len(logs)
            successful_requests = sum(1 for log in logs if log.get('success', False))
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Service breakdown
            services = {}
            for log in logs:
                service = log.get('service', 'unknown')
                if service not in services:
                    services[service] = {'total': 0, 'success': 0, 'models': {}}
                    
                services[service]['total'] += 1
                if log.get('success', False):
                    services[service]['success'] += 1
                    
                model = log.get('model', 'unknown')
                if model not in services[service]['models']:
                    services[service]['models'][model] = {'total': 0, 'success': 0}
                    
                services[service]['models'][model]['total'] += 1
                if log.get('success', False):
                    services[service]['models'][model]['success'] += 1
                    
            return {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': round(success_rate, 2),
                'services': services
            }
            
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Could not load API usage stats: {str(e)}")
            return {'total_requests': 0, 'success_rate': 0, 'services': {}}
            
    def clear_pipeline_state(self):
        """Clear all pipeline state and intermediate files."""
        files_to_remove = [
            self.state_file,
            'original_asr.json',
            'translated.json',
            'output_dubbed.mp4'
        ]
        
        # Remove files
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Removed {file_path}")
                
        # Remove TTS chunks directory
        if os.path.exists('tts_chunks'):
            import shutil
            shutil.rmtree('tts_chunks')
            self.logger.info("Removed tts_chunks directory")
            
        self.logger.info("Pipeline state cleared")
        
    def get_pipeline_summary(self) -> Dict:
        """
        Get summary of current pipeline state and files.
        
        Returns:
            Dictionary with pipeline summary information
        """
        state = self.load_pipeline_state()
        current_stage = self.detect_current_stage()
        
        # Check file existence
        files_status = {
            'original_asr.json': os.path.exists('original_asr.json'),
            'translated.json': os.path.exists('translated.json'),
            'tts_chunks': os.path.exists('tts_chunks') and bool(os.listdir('tts_chunks')) if os.path.exists('tts_chunks') else False,
            'output_dubbed.mp4': os.path.exists('output_dubbed.mp4')
        }
        
        # Count TTS chunks if directory exists
        tts_chunk_count = 0
        if os.path.exists('tts_chunks'):
            tts_chunk_count = len([f for f in os.listdir('tts_chunks') if f.endswith('.wav')])
            
        return {
            'current_stage': current_stage,
            'pipeline_state': state,
            'files_status': files_status,
            'tts_chunk_count': tts_chunk_count,
            'can_continue': current_stage in ['translation_needed', 'tts_needed', 'stitching_needed']
        }