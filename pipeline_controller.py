"""
Pipeline controller for orchestrating the complete dubbing workflow.
Manages automatic and manual modes, state persistence, and error recovery.
"""

import os
import json
import logging
import traceback
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import time

from translation import TranslationService
from tts import TTSService
from state_manager import StateManager
from audio_utils import AudioProcessor
from config import PIPELINE_DEFAULTS, FILE_PATHS
from error_handler import global_error_handler, handle_pipeline_error, create_error_context

@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    video_path: str
    api_keys: List[str]
    voice_name: str
    style_config: Dict
    mode: str  # 'automatic' or 'manual'
    manual_translation: Optional[str] = None

class PipelineController:
    """Main controller for the dubbing pipeline workflow."""
    
    def __init__(self):
        """Initialize pipeline controller with services."""
        self.state_manager = StateManager()
        self.audio_processor = AudioProcessor()
        self.logger = logging.getLogger(__name__)
        
        # Services initialized per run
        self.translation_service = None
        self.tts_service = None
        
        # Error recovery settings
        self.max_retry_attempts = PIPELINE_DEFAULTS.get("max_retry_attempts", 3)
        self.retry_delay = PIPELINE_DEFAULTS.get("retry_delay_seconds", 5)
        
        # Progress tracking
        self.current_progress = 0.0
        self.current_status = "Initialized"
        
    @handle_pipeline_error("pipeline_orchestration", max_recovery_attempts=3)
    def run_automatic_pipeline(self, config: PipelineConfig, progress_callback: Optional[Callable] = None) -> str:
        """
        Run complete automatic pipeline with comprehensive error handling: ASR → Translation → TTS → Dubbing.
        
        Args:
            config: Pipeline configuration
            progress_callback: Optional progress update callback
            
        Returns:
            Path to final dubbed video
        """
        # Create comprehensive error context
        context = {
            'stage': 'pipeline_orchestration',
            'mode': 'automatic',
            'api_keys': config.api_keys,
            'video_path': config.video_path,
            'voice_name': config.voice_name,
            'style_config': config.style_config
        }
        
        with create_error_context("pipeline_orchestration", **context) as error_ctx:
            self.logger.info("Starting automatic dubbing pipeline with enhanced error handling")
            self._update_progress(0.0, "Initializing pipeline...", progress_callback)
            
            # Validate configuration
            self._validate_pipeline_config(config)
            
            # Check API key health before starting
            healthy_keys = global_error_handler.get_healthy_api_keys(config.api_keys)
            if not healthy_keys:
                # Try graceful degradation
                degraded, message = global_error_handler.implement_graceful_degradation(context)
                if degraded:
                    raise Exception(f"Pipeline degraded: {message}")
                else:
                    raise Exception("All API keys are exhausted and no graceful degradation is available")
            
            self.logger.info(f"Pipeline starting with {len(healthy_keys)}/{len(config.api_keys)} healthy API keys")
            
            # Initialize services with error handling
            try:
                self.translation_service = TranslationService(healthy_keys)
                self.tts_service = TTSService(healthy_keys, config.voice_name)
            except Exception as e:
                self.logger.error(f"Failed to initialize services: {str(e)}")
                raise Exception(f"Service initialization failed: {str(e)}")
            
            # Save initial state with error tracking
            pipeline_state = {
                'mode': 'automatic',
                'video_path': config.video_path,
                'voice_name': config.voice_name,
                'style_config': config.style_config,
                'current_stage': 'starting',
                'started_at': datetime.now().isoformat(),
                'retry_count': 0,
                'api_keys_count': len(config.api_keys),
                'healthy_keys_count': len(healthy_keys),
                'error_recovery_enabled': True
            }
            self.state_manager.save_pipeline_state(pipeline_state)
            
            # Execute pipeline stages with comprehensive error handling
            return self._execute_automatic_pipeline_stages(config, progress_callback, context)
    
    def _execute_automatic_pipeline_stages(self, config: PipelineConfig, progress_callback, context: Dict) -> str:
        """Execute automatic pipeline stages with error recovery."""
        try:
            # Stage 1: Validate ASR results
            self._update_progress(0.1, "Validating ASR results...", progress_callback)
            asr_segments = self._validate_asr_results_with_recovery()
            
            # Stage 2: Translation with comprehensive error handling
            self._update_progress(0.2, "Starting translation...", progress_callback)
            translated_segments = self._run_translation_stage_with_comprehensive_recovery(
                config, asr_segments, progress_callback, context
            )
            
            # Stage 3: TTS Generation with error recovery
            self._update_progress(0.5, "Starting TTS generation...", progress_callback)
            tts_chunks_dir = self._run_tts_stage_with_recovery(
                translated_segments, config, progress_callback, context
            )
            
            # Stage 4: Audio processing with validation
            self._update_progress(0.8, "Processing audio...", progress_callback)
            final_video = self._run_audio_processing_with_recovery(
                config.video_path, tts_chunks_dir, progress_callback, context
            )
            
            # Stage 5: Final validation and cleanup
            self._update_progress(0.95, "Finalizing...", progress_callback)
            validated_video = self._finalize_pipeline_with_validation(final_video, context)
            
            self._update_progress(1.0, "Pipeline completed successfully!", progress_callback)
            
            # Update final state
            final_state = self.state_manager.load_pipeline_state()
            final_state.update({
                'current_stage': 'completed',
                'completed_at': datetime.now().isoformat(),
                'final_output': validated_video,
                'success': True
            })
            self.state_manager.save_pipeline_state(final_state)
            
            self.logger.info(f"Automatic pipeline completed successfully: {validated_video}")
            return validated_video
            
        except Exception as e:
            # Log comprehensive error information
            error_state = self.state_manager.load_pipeline_state()
            error_state.update({
                'current_stage': 'failed',
                'failed_at': datetime.now().isoformat(),
                'error_message': str(e),
                'success': False
            })
            self.state_manager.save_pipeline_state(error_state)
            
            # Get error recovery status
            recovery_status = global_error_handler.get_recovery_status()
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.logger.info(f"Error recovery status: {recovery_status}")
            
            raise
    
    def _validate_asr_results_with_recovery(self) -> List[Dict]:
        """Validate ASR results with recovery options."""
        try:
            return self._validate_asr_results()
        except Exception as e:
            self.logger.warning(f"ASR validation failed: {str(e)}")
            
            # Try to recover from common ASR issues
            if "file not found" in str(e).lower():
                # Check for alternative ASR file formats
                alternative_files = ["original_asr.json", "asr_results.json", "transcription.json"]
                for alt_file in alternative_files:
                    if os.path.exists(alt_file):
                        self.logger.info(f"Found alternative ASR file: {alt_file}")
                        try:
                            with open(alt_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list) and len(data) > 0:
                                    return data
                        except:
                            continue
            
            # If no recovery possible, re-raise with user-friendly message
            raise Exception("ASR results are not available. Please run transcription first.")
    
    def _run_translation_stage_with_comprehensive_recovery(self, config: PipelineConfig, asr_segments: List[Dict], 
                                                         progress_callback, context: Dict) -> List[Dict]:
        """Run translation stage with comprehensive error recovery."""
        max_translation_attempts = 3
        
        for attempt in range(max_translation_attempts):
            try:
                # Update progress
                base_progress = 0.2 + (attempt * 0.1)
                self._update_progress(base_progress, f"Translation attempt {attempt + 1}...", progress_callback)
                
                # Check if we have healthy API keys
                healthy_keys = global_error_handler.get_healthy_api_keys(config.api_keys)
                if not healthy_keys:
                    # Try graceful degradation
                    degraded, message = global_error_handler.implement_graceful_degradation(context)
                    if degraded:
                        raise Exception(f"Translation service degraded: {message}")
                    else:
                        raise Exception("All API keys exhausted during translation")
                
                # Update translation service with healthy keys
                self.translation_service = TranslationService(healthy_keys)
                
                # Attempt translation
                translated_segments = self.translation_service.translate_segments(asr_segments, config.style_config)
                
                # Validate translation results
                if not translated_segments or len(translated_segments) == 0:
                    raise Exception("Translation returned no results")
                
                self.logger.info(f"Translation completed successfully with {len(translated_segments)} segments")
                return translated_segments
                
            except Exception as e:
                self.logger.warning(f"Translation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_translation_attempts - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 5 * (2 ** attempt)
                    self.logger.info(f"Retrying translation in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # All attempts failed
                    raise Exception(f"Translation failed after {max_translation_attempts} attempts: {str(e)}")
    
    def _run_tts_stage_with_recovery(self, translated_segments: List[Dict], config: PipelineConfig, 
                                   progress_callback, context: Dict) -> str:
        """Run TTS stage with comprehensive error recovery."""
        max_tts_attempts = 3
        
        for attempt in range(max_tts_attempts):
            try:
                # Update progress
                base_progress = 0.5 + (attempt * 0.1)
                self._update_progress(base_progress, f"TTS attempt {attempt + 1}...", progress_callback)
                
                # Check if we have healthy API keys
                healthy_keys = global_error_handler.get_healthy_api_keys(config.api_keys)
                if not healthy_keys:
                    # Try graceful degradation
                    degraded, message = global_error_handler.implement_graceful_degradation(context)
                    if degraded:
                        raise Exception(f"TTS service degraded: {message}")
                    else:
                        raise Exception("All API keys exhausted during TTS generation")
                
                # Update TTS service with healthy keys
                self.tts_service = TTSService(healthy_keys, config.voice_name)
                
                # Create TTS progress callback
                def tts_progress(progress, status):
                    overall_progress = base_progress + (progress * 0.25)  # TTS takes 25% of total
                    self._update_progress(overall_progress, f"TTS: {status}", progress_callback)
                
                # Attempt TTS generation
                tts_chunks_dir = self.tts_service.generate_tts_chunks(translated_segments, tts_progress)
                
                # Validate TTS results
                if not os.path.exists(tts_chunks_dir) or len(os.listdir(tts_chunks_dir)) == 0:
                    raise Exception("TTS generation produced no audio files")
                
                self.logger.info(f"TTS generation completed successfully")
                return tts_chunks_dir
                
            except Exception as e:
                self.logger.warning(f"TTS attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_tts_attempts - 1:
                    # Wait before retry
                    wait_time = 10 * (2 ** attempt)
                    self.logger.info(f"Retrying TTS in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # All attempts failed
                    raise Exception(f"TTS generation failed after {max_tts_attempts} attempts: {str(e)}")
    
    def _run_audio_processing_with_recovery(self, video_path: str, tts_chunks_dir: str, 
                                          progress_callback, context: Dict) -> str:
        """Run audio processing stage with error recovery."""
        max_audio_attempts = 2
        
        for attempt in range(max_audio_attempts):
            try:
                # Update progress
                base_progress = 0.8 + (attempt * 0.05)
                self._update_progress(base_progress, f"Audio processing attempt {attempt + 1}...", progress_callback)
                
                # Initialize audio processor
                audio_processor = AudioProcessor()
                
                # Stitch audio chunks
                self._update_progress(base_progress + 0.02, "Stitching audio chunks...", progress_callback)
                stitched_audio = audio_processor.stitch_audio_chunks(tts_chunks_dir)
                
                # Sync with video
                self._update_progress(base_progress + 0.04, "Syncing with video...", progress_callback)
                final_video = audio_processor.sync_audio_with_video(video_path, stitched_audio)
                
                # Validate output
                if not os.path.exists(final_video) or os.path.getsize(final_video) == 0:
                    raise Exception("Audio processing produced invalid output file")
                
                self.logger.info("Audio processing completed successfully")
                return final_video
                
            except Exception as e:
                self.logger.warning(f"Audio processing attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_audio_attempts - 1:
                    # Wait before retry
                    time.sleep(5)
                else:
                    # All attempts failed
                    raise Exception(f"Audio processing failed after {max_audio_attempts} attempts: {str(e)}")
    
    def _finalize_pipeline_with_validation(self, final_video: str, context: Dict) -> str:
        """Finalize pipeline with comprehensive validation."""
        try:
            # Validate final output
            if not os.path.exists(final_video):
                raise Exception("Final video file does not exist")
            
            file_size = os.path.getsize(final_video)
            if file_size == 0:
                raise Exception("Final video file is empty")
            
            # Basic video validation using ffprobe if available
            try:
                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', final_video],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    format_info = json.loads(result.stdout)
                    duration = float(format_info.get('format', {}).get('duration', 0))
                    if duration == 0:
                        self.logger.warning("Final video appears to have zero duration")
                    else:
                        self.logger.info(f"Final video duration: {duration:.2f} seconds")
                else:
                    self.logger.warning("Could not validate video format with ffprobe")
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                self.logger.warning("Video validation skipped (ffprobe not available or failed)")
            
            # Log success metrics
            self.logger.info(f"Pipeline finalized successfully:")
            self.logger.info(f"  Final video: {final_video}")
            self.logger.info(f"  File size: {file_size / (1024*1024):.2f} MB")
            
            return final_video
            
        except Exception as e:
            raise Exception(f"Pipeline finalization failed: {str(e)}")
            self._update_progress(0.5, "Generating TTS audio...", progress_callback)
            tts_chunks_dir = self._run_tts_stage_with_retry(translated_segments, progress_callback)
            
            # Stage 4: Audio Processing and Final Assembly
            self._update_progress(0.8, "Processing audio and creating final video...", progress_callback)
            output_path = self._run_dubbing_stage_with_validation(config.video_path, tts_chunks_dir, translated_segments)
            
            # Final validation and cleanup
            self._update_progress(0.95, "Validating output...", progress_callback)
            self._validate_final_output(output_path, translated_segments)
            
            # Update final state
            final_state = {
                'current_stage': 'complete',
                'output_path': output_path,
                'completed_at': datetime.now().isoformat(),
                'total_segments': len(translated_segments),
                'success': True
            }
            self.state_manager.save_pipeline_state(final_state)
            
            self._update_progress(1.0, "Pipeline completed successfully!", progress_callback)
            self.logger.info(f"Automatic pipeline completed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            error_details = {
                'current_stage': 'error',
                'error_message': str(e),
                'error_traceback': traceback.format_exc(),
                'error_at': datetime.now().isoformat(),
                'progress_at_error': self.current_progress
            }
            
            self.logger.error(f"Automatic pipeline failed at {self.current_progress*100:.1f}%: {str(e)}")
            self.logger.debug(f"Error traceback: {traceback.format_exc()}")
            
            self.state_manager.save_pipeline_state(error_details)
            
            # Provide user-friendly error message
            user_error = self._format_user_error(e, self.current_progress)
            raise Exception(user_error)
    
    def run_manual_pipeline(self, config: PipelineConfig, progress_callback: Optional[Callable] = None) -> str:
        """
        Run manual pipeline: User Translation → TTS → Dubbing.
        
        Args:
            config: Pipeline configuration with manual translation
            progress_callback: Optional progress update callback
            
        Returns:
            Path to final dubbed video
        """
        self.logger.info("Starting manual dubbing pipeline")
        self._update_progress(0.0, "Initializing manual pipeline...", progress_callback)
        
        # Validate configuration
        self._validate_pipeline_config(config)
        
        # Initialize TTS service
        try:
            self.tts_service = TTSService(config.api_keys, config.voice_name)
        except Exception as e:
            raise Exception(f"Failed to initialize TTS service: {str(e)}")
        
        # Save initial state
        pipeline_state = {
            'mode': 'manual',
            'video_path': config.video_path,
            'voice_name': config.voice_name,
            'current_stage': 'starting',
            'started_at': datetime.now().isoformat(),
            'api_keys_count': len(config.api_keys)
        }
        self.state_manager.save_pipeline_state(pipeline_state)
        
        try:
            # Stage 1: Process and validate manual translation
            self._update_progress(0.1, "Processing manual translation...", progress_callback)
            translated_segments = self._process_manual_translation_enhanced(config.manual_translation)
            
            # Stage 2: TTS Generation with retry logic
            self._update_progress(0.3, "Generating TTS audio...", progress_callback)
            tts_chunks_dir = self._run_tts_stage_with_retry(translated_segments, progress_callback)
            
            # Stage 3: Audio Processing and Final Assembly
            self._update_progress(0.7, "Creating final dubbed video...", progress_callback)
            output_path = self._run_dubbing_stage_with_validation(config.video_path, tts_chunks_dir, translated_segments)
            
            # Final validation
            self._update_progress(0.95, "Validating output...", progress_callback)
            self._validate_final_output(output_path, translated_segments)
            
            # Update final state
            final_state = {
                'current_stage': 'complete',
                'output_path': output_path,
                'completed_at': datetime.now().isoformat(),
                'total_segments': len(translated_segments),
                'success': True
            }
            self.state_manager.save_pipeline_state(final_state)
            
            self._update_progress(1.0, "Manual pipeline completed successfully!", progress_callback)
            self.logger.info(f"Manual pipeline completed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            error_details = {
                'current_stage': 'error',
                'error_message': str(e),
                'error_traceback': traceback.format_exc(),
                'error_at': datetime.now().isoformat(),
                'progress_at_error': self.current_progress
            }
            
            self.logger.error(f"Manual pipeline failed at {self.current_progress*100:.1f}%: {str(e)}")
            self.state_manager.save_pipeline_state(error_details)
            
            user_error = self._format_user_error(e, self.current_progress)
            raise Exception(user_error)
    
    def continue_from_checkpoint(self, config: PipelineConfig, progress_callback: Optional[Callable] = None) -> str:
        """
        Continue pipeline from last checkpoint with enhanced error handling.
        
        Args:
            config: Pipeline configuration
            progress_callback: Optional progress update callback
            
        Returns:
            Path to final dubbed video
        """
        current_stage = self.detect_pipeline_state()
        self.logger.info(f"Continuing pipeline from stage: {current_stage}")
        
        # Load previous state if available
        try:
            previous_state = self.state_manager.load_pipeline_state()
            self.logger.info(f"Loaded previous state: {previous_state.get('current_stage', 'unknown')}")
        except Exception as e:
            self.logger.warning(f"Could not load previous state: {str(e)}")
            previous_state = {}
        
        # Validate configuration
        self._validate_pipeline_config(config)
        
        # Initialize services based on what's needed
        try:
            if current_stage in ['translation_needed', 'tts_needed', 'stitching_needed']:
                if current_stage == 'translation_needed':
                    self.translation_service = TranslationService(config.api_keys)
                    
                if current_stage in ['translation_needed', 'tts_needed']:
                    self.tts_service = TTSService(config.api_keys, config.voice_name)
                    
        except Exception as e:
            raise Exception(f"Failed to initialize services for continuation: {str(e)}")
        
        # Update state for continuation
        continuation_state = {
            'mode': previous_state.get('mode', 'continuation'),
            'video_path': config.video_path,
            'voice_name': config.voice_name,
            'current_stage': f'continuing_from_{current_stage}',
            'continued_at': datetime.now().isoformat(),
            'original_start': previous_state.get('started_at'),
            'continuation_count': previous_state.get('continuation_count', 0) + 1
        }
        self.state_manager.save_pipeline_state(continuation_state)
        
        try:
            if current_stage == 'asr_needed':
                raise Exception(
                    "Cannot continue from checkpoint: ASR results not found. "
                    "Please run transcription first."
                )
                
            elif current_stage == 'translation_needed':
                self._update_progress(0.2, "Continuing from translation stage...", progress_callback)
                translated_segments = self._run_translation_stage_with_retry(config, progress_callback)
                
                self._update_progress(0.5, "Proceeding to TTS generation...", progress_callback)
                tts_chunks_dir = self._run_tts_stage_with_retry(translated_segments, progress_callback)
                
                self._update_progress(0.8, "Creating final video...", progress_callback)
                output_path = self._run_dubbing_stage_with_validation(config.video_path, tts_chunks_dir, translated_segments)
                
            elif current_stage == 'tts_needed':
                self._update_progress(0.5, "Continuing from TTS generation...", progress_callback)
                translated_segments = self._load_translated_segments()
                
                # Validate loaded segments
                if not translated_segments:
                    raise Exception("No translated segments found. Translation may need to be rerun.")
                    
                tts_chunks_dir = self._run_tts_stage_with_retry(translated_segments, progress_callback)
                
                self._update_progress(0.8, "Creating final video...", progress_callback)
                output_path = self._run_dubbing_stage_with_validation(config.video_path, tts_chunks_dir, translated_segments)
                
            elif current_stage == 'stitching_needed':
                self._update_progress(0.8, "Continuing from audio stitching...", progress_callback)
                translated_segments = self._load_translated_segments()
                
                # Validate TTS chunks exist
                tts_chunks_dir = FILE_PATHS.get("tts_chunks", "tts_chunks")
                if not os.path.exists(tts_chunks_dir) or len(os.listdir(tts_chunks_dir)) == 0:
                    raise Exception("TTS chunks not found. TTS generation may need to be rerun.")
                    
                output_path = self._run_dubbing_stage_with_validation(config.video_path, tts_chunks_dir, translated_segments)
                
            elif current_stage == 'complete':
                self._update_progress(1.0, "Pipeline already complete", progress_callback)
                self.logger.info("Pipeline already complete")
                
                # Try to get output path from state
                output_path = previous_state.get('output_path')
                if not output_path or not os.path.exists(output_path):
                    output_path = FILE_PATHS.get("output_video", "output_dubbed.mp4")
                    
                if not os.path.exists(output_path):
                    raise Exception("Pipeline marked complete but output file not found. Please restart pipeline.")
                    
                return output_path
                
            else:
                raise Exception(f"Cannot continue from unknown stage: {current_stage}")
            
            # Validate final output
            self._update_progress(0.95, "Validating continued pipeline output...", progress_callback)
            translated_segments = self._load_translated_segments()
            self._validate_final_output(output_path, translated_segments)
            
            # Update final state
            final_state = {
                'current_stage': 'complete',
                'output_path': output_path,
                'completed_at': datetime.now().isoformat(),
                'continued_from': current_stage,
                'success': True
            }
            self.state_manager.save_pipeline_state(final_state)
            
            self._update_progress(1.0, "Pipeline continuation completed successfully!", progress_callback)
            self.logger.info(f"Pipeline continuation completed successfully: {output_path}")
            return output_path
                
        except Exception as e:
            error_details = {
                'current_stage': 'continuation_error',
                'error_message': str(e),
                'error_traceback': traceback.format_exc(),
                'error_at': datetime.now().isoformat(),
                'failed_continuation_from': current_stage,
                'progress_at_error': self.current_progress
            }
            
            self.logger.error(f"Pipeline continuation failed from {current_stage}: {str(e)}")
            self.state_manager.save_pipeline_state(error_details)
            
            user_error = f"Failed to continue from {current_stage}: {self._format_user_error(e, self.current_progress)}"
            raise Exception(user_error)
    
    def detect_pipeline_state(self) -> str:
        """Detect current pipeline state based on existing files."""
        if not os.path.exists('original_asr.json'):
            return 'asr_needed'
        elif not os.path.exists('translated.json'):
            return 'translation_needed'
        elif not os.path.exists('tts_chunks') or len(os.listdir('tts_chunks')) == 0:
            return 'tts_needed'
        elif not os.path.exists('output_dubbed.mp4'):
            return 'stitching_needed'
        else:
            return 'complete'
    
    def _run_translation_stage(self, config: PipelineConfig) -> List[Dict]:
        """Run translation stage and save results."""
        # Load ASR segments
        with open('original_asr.json', 'r') as f:
            asr_segments = json.load(f)
            
        # Translate segments
        translated_segments = self.translation_service.translate_segments(
            asr_segments, config.style_config
        )
        
        # Save translated results
        translated_data = [asdict(seg) for seg in translated_segments]
        with open('translated.json', 'w') as f:
            json.dump(translated_data, f, indent=2)
            
        self.state_manager.save_pipeline_state({'current_stage': 'translation_complete'})
        return translated_data
    
    def _run_tts_stage(self, translated_segments: List[Dict], progress_callback: Optional[Callable] = None) -> str:
        """Run TTS stage and return chunks directory."""
        tts_chunks_dir = self.tts_service.generate_tts_chunks(
            translated_segments, progress_callback
        )
        
        self.state_manager.save_pipeline_state({'current_stage': 'tts_complete'})
        return tts_chunks_dir
    
    def _run_dubbing_stage(self, video_path: str, tts_chunks_dir: str) -> str:
        """Run final dubbing stage."""
        # Stitch audio chunks
        stitched_audio = self.audio_processor.stitch_audio_chunks(tts_chunks_dir)
        
        # Create dubbed video
        output_path = self.audio_processor.sync_audio_with_video(
            video_path, stitched_audio, 'output_dubbed.mp4'
        )
        
        self.state_manager.save_pipeline_state({'current_stage': 'dubbing_complete'})
        return output_path
    
    def _process_manual_translation(self, manual_translation: str) -> List[Dict]:
        """Process and validate manual translation JSON."""
        try:
            translated_data = json.loads(manual_translation)
            
            # Validate format
            for item in translated_data:
                if not all(key in item for key in ['start', 'end', 'text_translated']):
                    raise ValueError("Invalid translation format. Required fields: start, end, text_translated")
                    
            # Save to translated.json
            with open('translated.json', 'w') as f:
                json.dump(translated_data, f, indent=2)
                
            return translated_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    def _process_manual_translation_enhanced(self, manual_translation: str) -> List[Dict]:
        """Process and validate manual translation JSON with enhanced validation."""
        if not manual_translation or not manual_translation.strip():
            raise ValueError("Manual translation cannot be empty")
            
        try:
            # Parse JSON
            translated_data = json.loads(manual_translation.strip())
            
            # Validate it's a list
            if not isinstance(translated_data, list):
                raise ValueError("Translation must be a JSON array of segments")
                
            if len(translated_data) == 0:
                raise ValueError("Translation cannot be empty")
            
            # Validate each segment
            for i, segment in enumerate(translated_data):
                if not isinstance(segment, dict):
                    raise ValueError(f"Segment {i+1} must be a JSON object")
                
                # Check required fields
                required_fields = ['start', 'end', 'text_translated']
                for field in required_fields:
                    if field not in segment:
                        raise ValueError(f"Segment {i+1} missing required field: {field}")
                
                # Validate field types and values
                try:
                    start_time = float(segment['start'])
                    end_time = float(segment['end'])
                except (ValueError, TypeError):
                    raise ValueError(f"Segment {i+1} has invalid start/end times (must be numbers)")
                
                if start_time < 0:
                    raise ValueError(f"Segment {i+1} has negative start time")
                    
                if end_time <= start_time:
                    raise ValueError(f"Segment {i+1} has invalid timing: end time must be greater than start time")
                
                if not isinstance(segment['text_translated'], str) or not segment['text_translated'].strip():
                    raise ValueError(f"Segment {i+1} has empty or invalid translated text")
            
            # Check for overlapping segments
            sorted_segments = sorted(translated_data, key=lambda x: x['start'])
            for i in range(len(sorted_segments) - 1):
                current_end = sorted_segments[i]['end']
                next_start = sorted_segments[i + 1]['start']
                if current_end > next_start:
                    self.logger.warning(f"Overlapping segments detected: segment ending at {current_end}s overlaps with segment starting at {next_start}s")
            
            # Save to translated.json with UTF-8 encoding
            translated_file = FILE_PATHS.get("translated", "translated.json")
            with open(translated_file, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, indent=2, ensure_ascii=False)
            
            # Update state
            self.state_manager.save_pipeline_state({
                'current_stage': 'manual_translation_processed',
                'manual_segments_count': len(translated_data),
                'total_duration': max(seg['end'] for seg in translated_data),
                'manual_translation_processed_at': datetime.now().isoformat()
            })
            
            self.logger.info(f"Manual translation processed successfully: {len(translated_data)} segments, {max(seg['end'] for seg in translated_data):.2f}s total duration")
            return translated_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}. Please ensure your translation is valid JSON.")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            else:
                raise ValueError(f"Error processing manual translation: {str(e)}")
    
    def _load_translated_segments(self) -> List[Dict]:
        """Load translated segments from file."""
        with open('translated.json', 'r') as f:
            return json.load(f)
    
    def _validate_pipeline_config(self, config: PipelineConfig):
        """Validate pipeline configuration before starting."""
        if not config.video_path or not os.path.exists(config.video_path):
            raise ValueError(f"Video file not found: {config.video_path}")
            
        if not config.api_keys or len(config.api_keys) == 0:
            raise ValueError("At least one API key is required")
            
        if not config.voice_name:
            raise ValueError("Voice name is required")
            
        if config.mode not in ['automatic', 'manual']:
            raise ValueError(f"Invalid mode: {config.mode}")
            
        if config.mode == 'manual' and not config.manual_translation:
            raise ValueError("Manual translation is required for manual mode")
            
        self.logger.info(f"Pipeline configuration validated: {config.mode} mode, {len(config.api_keys)} API keys")
    
    def _validate_asr_results(self) -> List[Dict]:
        """Validate ASR results exist and are properly formatted."""
        asr_file = FILE_PATHS.get("original_asr", "original_asr.json")
        
        if not os.path.exists(asr_file):
            raise Exception(
                f"ASR results not found at {asr_file}. "
                "Please run transcription first or check if the file exists."
            )
            
        try:
            with open(asr_file, 'r', encoding='utf-8') as f:
                asr_segments = json.load(f)
                
            if not isinstance(asr_segments, list) or len(asr_segments) == 0:
                raise ValueError("ASR file contains no valid segments")
                
            # Validate segment format
            for i, segment in enumerate(asr_segments):
                if not isinstance(segment, dict):
                    raise ValueError(f"Segment {i} is not a dictionary")
                    
                required_fields = ['start', 'end', 'text']
                for field in required_fields:
                    if field not in segment:
                        raise ValueError(f"Segment {i} missing required field: {field}")
                        
                # Validate timing
                if segment['start'] >= segment['end']:
                    raise ValueError(f"Segment {i} has invalid timing: start >= end")
                    
            self.logger.info(f"ASR validation passed: {len(asr_segments)} segments")
            return asr_segments
            
        except json.JSONDecodeError as e:
            raise Exception(f"ASR file is corrupted or invalid JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"ASR validation failed: {str(e)}")
    
    def _run_translation_stage_with_retry(self, config: PipelineConfig, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Run translation stage with retry logic and progress tracking."""
        for attempt in range(self.max_retry_attempts):
            try:
                self.logger.info(f"Translation attempt {attempt + 1}/{self.max_retry_attempts}")
                
                # Load ASR segments
                with open(FILE_PATHS.get("original_asr", "original_asr.json"), 'r', encoding='utf-8') as f:
                    asr_segments = json.load(f)
                
                # Update progress
                self._update_progress(0.25, f"Translating {len(asr_segments)} segments...", progress_callback)
                
                # Translate segments
                translated_segments = self.translation_service.translate_segments(
                    asr_segments, config.style_config
                )
                
                # Validate translation results
                if not translated_segments or len(translated_segments) != len(asr_segments):
                    raise Exception(f"Translation returned {len(translated_segments)} segments, expected {len(asr_segments)}")
                
                # Save translated results
                translated_data = [asdict(seg) if hasattr(seg, '__dict__') else seg for seg in translated_segments]
                
                with open(FILE_PATHS.get("translated", "translated.json"), 'w', encoding='utf-8') as f:
                    json.dump(translated_data, f, indent=2, ensure_ascii=False)
                
                # Update state
                self.state_manager.save_pipeline_state({
                    'current_stage': 'translation_complete',
                    'translated_segments_count': len(translated_data),
                    'translation_completed_at': datetime.now().isoformat()
                })
                
                self.logger.info(f"Translation completed successfully: {len(translated_data)} segments")
                return translated_data
                
            except Exception as e:
                self.logger.warning(f"Translation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retry_attempts - 1:
                    self.logger.info(f"Retrying translation in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Translation failed after {self.max_retry_attempts} attempts: {str(e)}")
    
    def _run_tts_stage_with_retry(self, translated_segments: List[Dict], progress_callback: Optional[Callable] = None) -> str:
        """Run TTS stage with retry logic and enhanced progress tracking."""
        for attempt in range(self.max_retry_attempts):
            try:
                self.logger.info(f"TTS attempt {attempt + 1}/{self.max_retry_attempts}")
                
                # Create progress wrapper for TTS
                def tts_progress_wrapper(progress: float, message: str):
                    # Map TTS progress (0.0-1.0) to overall progress (0.5-0.8)
                    overall_progress = 0.5 + (progress * 0.3)
                    self._update_progress(overall_progress, f"TTS: {message}", progress_callback)
                
                # Generate TTS chunks
                tts_chunks_dir = self.tts_service.generate_tts_chunks(
                    translated_segments, tts_progress_wrapper
                )
                
                # Validate TTS output
                if not os.path.exists(tts_chunks_dir):
                    raise Exception(f"TTS chunks directory not created: {tts_chunks_dir}")
                    
                chunk_files = [f for f in os.listdir(tts_chunks_dir) if f.endswith('.wav')]
                if len(chunk_files) == 0:
                    raise Exception("No TTS audio chunks were generated")
                
                # Update state
                self.state_manager.save_pipeline_state({
                    'current_stage': 'tts_complete',
                    'tts_chunks_count': len(chunk_files),
                    'tts_chunks_dir': tts_chunks_dir,
                    'tts_completed_at': datetime.now().isoformat()
                })
                
                self.logger.info(f"TTS generation completed: {len(chunk_files)} chunks in {tts_chunks_dir}")
                return tts_chunks_dir
                
            except Exception as e:
                self.logger.warning(f"TTS attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retry_attempts - 1:
                    self.logger.info(f"Retrying TTS in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"TTS generation failed after {self.max_retry_attempts} attempts: {str(e)}")
    
    def _run_dubbing_stage_with_validation(self, video_path: str, tts_chunks_dir: str, translated_segments: List[Dict]) -> str:
        """Run final dubbing stage with comprehensive validation."""
        try:
            self.logger.info("Starting audio stitching and video dubbing")
            
            # Stitch audio chunks with validation
            stitched_audio = self.audio_processor.stitch_audio_chunks(
                tts_chunks_dir, 
                output_path=FILE_PATHS.get("stitched_audio", "stitched_audio.wav"),
                segments_data=translated_segments
            )
            
            if not os.path.exists(stitched_audio):
                raise Exception(f"Stitched audio file not created: {stitched_audio}")
            
            # Validate stitched audio duration
            audio_info = self.audio_processor.get_audio_info(stitched_audio)
            if audio_info.get('duration', 0) == 0:
                raise Exception("Stitched audio has zero duration")
            
            self.logger.info(f"Audio stitching completed: {audio_info.get('duration', 0):.2f}s")
            
            # Create dubbed video with sync validation
            output_path = self.audio_processor.sync_audio_with_video(
                video_path, 
                stitched_audio, 
                FILE_PATHS.get("output_video", "output_dubbed.mp4")
            )
            
            if not os.path.exists(output_path):
                raise Exception(f"Dubbed video file not created: {output_path}")
            
            # Validate final sync
            sync_valid = self.audio_processor.validate_audio_sync(output_path, translated_segments)
            if not sync_valid:
                self.logger.warning("Audio-video sync validation failed, but output was created")
            
            # Update state
            self.state_manager.save_pipeline_state({
                'current_stage': 'dubbing_complete',
                'stitched_audio_path': stitched_audio,
                'stitched_audio_duration': audio_info.get('duration', 0),
                'sync_validation_passed': sync_valid,
                'dubbing_completed_at': datetime.now().isoformat()
            })
            
            self.logger.info(f"Dubbing stage completed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Dubbing stage failed: {str(e)}")
            raise Exception(f"Failed to create dubbed video: {str(e)}")
    
    def _validate_final_output(self, output_path: str, translated_segments: List[Dict]):
        """Validate the final output file."""
        if not os.path.exists(output_path):
            raise Exception(f"Final output file not found: {output_path}")
            
        # Check file size
        file_size = os.path.getsize(output_path)
        if file_size < 1000:  # Less than 1KB is likely an error
            raise Exception(f"Output file is too small ({file_size} bytes), likely corrupted")
            
        # Validate video properties if possible
        try:
            video_info = self.audio_processor._get_video_info(output_path)
            if video_info.get('duration', 0) == 0:
                raise Exception("Output video has zero duration")
                
            self.logger.info(f"Final output validation passed: {file_size} bytes, {video_info.get('duration', 0):.2f}s")
            
        except Exception as e:
            self.logger.warning(f"Could not validate video properties: {str(e)}")
    
    def _update_progress(self, progress: float, status: str, callback: Optional[Callable] = None):
        """Update progress tracking and call callback if provided."""
        self.current_progress = progress
        self.current_status = status
        
        self.logger.info(f"Progress: {progress*100:.1f}% - {status}")
        
        if callback:
            try:
                callback(progress, status)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {str(e)}")
    
    def _format_user_error(self, error: Exception, progress: float) -> str:
        """Format error message for user display."""
        error_str = str(error)
        
        # Provide context based on progress
        if progress < 0.2:
            context = "during initialization"
        elif progress < 0.5:
            context = "during translation"
        elif progress < 0.8:
            context = "during TTS generation"
        else:
            context = "during final video creation"
            
        # Common error patterns and user-friendly messages
        if "API key" in error_str.lower():
            return f"API key error {context}. Please check your Gemini API keys and ensure they have sufficient quota."
        elif "quota" in error_str.lower() or "limit" in error_str.lower():
            return f"API quota exceeded {context}. Please try again later or use additional API keys."
        elif "network" in error_str.lower() or "connection" in error_str.lower():
            return f"Network error {context}. Please check your internet connection and try again."
        elif "file not found" in error_str.lower():
            return f"File error {context}. Please ensure all required files exist and are accessible."
        else:
            return f"Pipeline failed {context}: {error_str}"