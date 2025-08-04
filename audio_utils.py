"""
Extended audio processing utilities for dubbing pipeline.
Handles audio stitching, video synchronization, and format conversion.
"""

import os
import subprocess
import tempfile
import logging
import json
import wave
from typing import List, Optional, Dict, Tuple
import glob
from pathlib import Path

from config import PIPELINE_DEFAULTS, FILE_PATHS

class AudioProcessor:
    """Extended audio processing for dubbing pipeline."""
    
    def __init__(self):
        """Initialize audio processor with logging."""
        self.logger = logging.getLogger(__name__)
        self.sample_rate = PIPELINE_DEFAULTS["audio_sample_rate"]
        self.channels = PIPELINE_DEFAULTS["audio_channels"]
        self.audio_format = PIPELINE_DEFAULTS["audio_format"]
        
    def stitch_audio_chunks(self, chunks_directory: str, output_path: str = None, segments_data: List[Dict] = None) -> str:
        """
        Stitch TTS audio chunks in timestamp order with enhanced validation.
        
        Args:
            chunks_directory: Directory containing TTS chunk files
            output_path: Output path for stitched audio
            segments_data: Optional segment timing data for validation
            
        Returns:
            Path to stitched audio file
        """
        if output_path is None:
            output_path = FILE_PATHS["stitched_audio"]
            
        self.logger.info(f"Stitching audio chunks from {chunks_directory}")
        
        # Validate chunks directory exists
        if not os.path.exists(chunks_directory):
            raise Exception(f"Chunks directory does not exist: {chunks_directory}")
        
        # Get all chunk files and sort by name (which includes chunk index)
        chunk_pattern = os.path.join(chunks_directory, "chunk_*.wav")
        chunk_files = sorted(glob.glob(chunk_pattern))
        
        if not chunk_files:
            raise Exception(f"No audio chunks found in {chunks_directory}")
            
        self.logger.info(f"Found {len(chunk_files)} chunks to stitch")
        
        # Validate chunk files before stitching
        self._validate_chunk_files(chunk_files)
        
        # Normalize audio levels across chunks
        normalized_chunks = self._normalize_chunk_levels(chunk_files)
        
        # Create temporary file list for FFmpeg concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for chunk_file in normalized_chunks:
                # Use absolute path for FFmpeg
                abs_path = os.path.abspath(chunk_file)
                f.write(f"file '{abs_path}'\\n")
            list_file = f.name
            
        try:
            # Use FFmpeg to concatenate audio files with enhanced settings
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-acodec', 'pcm_s16le',  # Ensure consistent encoding
                '-ar', str(self.sample_rate),  # Ensure consistent sample rate
                '-ac', str(self.channels),  # Ensure consistent channels
                '-af', 'aresample=resampler=soxr',  # High-quality resampling
                output_path,
                '-y'  # Overwrite output file
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Validate the stitched output
            if not os.path.exists(output_path):
                raise Exception("Stitched audio file was not created")
                
            # Verify audio properties
            audio_info = self.get_audio_info(output_path)
            if audio_info.get('duration', 0) == 0:
                raise Exception("Stitched audio has zero duration")
                
            self.logger.info(f"Audio stitching completed: {output_path} ({audio_info.get('duration', 0):.2f}s)")
            
            # Validate timing if segments data provided
            if segments_data:
                self._validate_stitched_timing(output_path, segments_data)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio stitching failed: {e.stderr}")
            raise Exception(f"Failed to stitch audio chunks: {e.stderr}")
        finally:
            # Clean up temporary files
            if os.path.exists(list_file):
                os.unlink(list_file)
            
            # Clean up normalized chunks if they were temporary
            for chunk_file in normalized_chunks:
                if chunk_file not in chunk_files and os.path.exists(chunk_file):
                    try:
                        os.unlink(chunk_file)
                    except Exception:
                        pass
                        
    def sync_audio_with_video(self, video_path: str, audio_path: str, output_path: str = None) -> str:
        """
        Sync new audio with original video to create dubbed output with enhanced validation.
        
        Args:
            video_path: Path to original video file
            audio_path: Path to new audio track
            output_path: Path for dubbed video output
            
        Returns:
            Path to dubbed video file
        """
        if output_path is None:
            output_path = FILE_PATHS["output_video"]
            
        self.logger.info(f"Syncing audio with video: {video_path} + {audio_path}")
        
        # Validate input files
        if not os.path.exists(video_path):
            raise Exception(f"Video file does not exist: {video_path}")
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file does not exist: {audio_path}")
            
        # Get input file information
        video_info = self._get_video_info(video_path)
        audio_info = self.get_audio_info(audio_path)
        
        self.logger.info(
            f"Video: {video_info.get('duration', 0):.2f}s, "
            f"Audio: {audio_info.get('duration', 0):.2f}s"
        )
        
        # Determine sync strategy based on duration difference
        video_duration = video_info.get('duration', 0)
        audio_duration = audio_info.get('duration', 0)
        duration_diff = abs(video_duration - audio_duration)
        
        # Use different strategies based on duration difference
        if duration_diff > 2.0:  # Significant difference
            self.logger.warning(
                f"Significant duration difference: {duration_diff:.2f}s. "
                "Using audio duration as reference."
            )
            sync_strategy = 'audio_reference'
        else:
            sync_strategy = 'standard'
            
        # Build FFmpeg command based on strategy
        cmd = self._build_sync_command(video_path, audio_path, output_path, sync_strategy)
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Validate output file was created
            if not os.path.exists(output_path):
                raise Exception("Output video file was not created")
                
            # Validate output properties
            output_info = self._get_video_info(output_path)
            if output_info.get('duration', 0) == 0:
                raise Exception("Output video has zero duration")
                
            self.logger.info(
                f"Video dubbing completed: {output_path} "
                f"({output_info.get('duration', 0):.2f}s)"
            )
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Video dubbing failed: {e.stderr}")
            raise Exception(f"Failed to create dubbed video: {e.stderr}")
            
    def validate_audio_sync(self, video_path: str, segments_data: List[Dict]) -> bool:
        """
        Validate that audio-video synchronization is accurate.
        
        Args:
            video_path: Path to video file
            segments_data: List of segment timing data
            
        Returns:
            True if sync is accurate, False otherwise
        """
        try:
            # Get video duration
            video_info = self._get_video_info(video_path)
            video_duration = video_info.get('duration', 0)
            
            if video_duration == 0:
                self.logger.error("Could not determine video duration")
                return False
                
            # Calculate expected duration from segments
            if not segments_data:
                self.logger.warning("No segments data provided for sync validation")
                return True
                
            expected_duration = max(seg.get('end', 0) for seg in segments_data)
            
            # Allow 5% tolerance or 2 seconds, whichever is larger
            tolerance = max(expected_duration * 0.05, 2.0)
            duration_diff = abs(video_duration - expected_duration)
            
            if duration_diff > tolerance:
                self.logger.warning(
                    f"Audio-video sync validation failed: "
                    f"video {video_duration:.2f}s vs expected {expected_duration:.2f}s "
                    f"(diff: {duration_diff:.2f}s, tolerance: {tolerance:.2f}s)"
                )
                return False
            else:
                self.logger.info(
                    f"Audio-video sync validation passed: "
                    f"video {video_duration:.2f}s vs expected {expected_duration:.2f}s "
                    f"(diff: {duration_diff:.2f}s)"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Audio-video sync validation error: {str(e)}")
            return False
            
    def get_audio_info(self, audio_path: str) -> Dict:
        """
        Get detailed information about audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            info = json.loads(result.stdout)
            
            # Extract relevant information
            audio_stream = next((s for s in info['streams'] if s['codec_type'] == 'audio'), {})
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(info['format'].get('bit_rate', 0))
            }
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to get audio info: {str(e)}")
            return {}
            
    def normalize_audio_levels(self, audio_path: str, target_lufs: float = -23.0) -> str:
        """
        Normalize audio levels for consistent volume.
        
        Args:
            audio_path: Path to audio file
            target_lufs: Target LUFS level for normalization
            
        Returns:
            Path to normalized audio file
        """
        normalized_path = audio_path.replace('.wav', '_normalized.wav')
        
        cmd = [
            'ffmpeg',
            '-i', audio_path,
            '-af', f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11',
            normalized_path,
            '-y'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.info(f"Audio normalization completed: {normalized_path}")
            
            # Replace original with normalized
            os.replace(normalized_path, audio_path)
            return audio_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio normalization failed: {e.stderr}")
            return audio_path  # Return original if normalization fails
            
    # Helper methods
    def _validate_chunk_files(self, chunk_files: List[str]):
        """
        Validate chunk files before stitching.
        
        Args:
            chunk_files: List of chunk file paths
        """
        for chunk_file in chunk_files:
            if not os.path.exists(chunk_file):
                raise Exception(f"Chunk file does not exist: {chunk_file}")
                
            # Check file size
            file_size = os.path.getsize(chunk_file)
            if file_size < 100:  # Very small files are likely corrupted
                raise Exception(f"Chunk file too small (likely corrupted): {chunk_file}")
                
            # Try to get audio info to validate format
            try:
                audio_info = self.get_audio_info(chunk_file)
                if audio_info.get('duration', 0) == 0:
                    raise Exception(f"Chunk file has zero duration: {chunk_file}")
            except Exception as e:
                raise Exception(f"Invalid chunk file {chunk_file}: {str(e)}")
                
        self.logger.info(f"Validated {len(chunk_files)} chunk files")
    
    def _normalize_chunk_levels(self, chunk_files: List[str]) -> List[str]:
        """
        Normalize audio levels across chunks for consistent volume.
        
        Args:
            chunk_files: List of chunk file paths
            
        Returns:
            List of normalized chunk file paths
        """
        normalized_files = []
        
        for i, chunk_file in enumerate(chunk_files):
            try:
                # Create normalized version
                normalized_file = f"{chunk_file}_normalized.wav"
                
                cmd = [
                    'ffmpeg',
                    '-i', chunk_file,
                    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # Broadcast standard normalization
                    '-acodec', 'pcm_s16le',
                    '-ar', str(self.sample_rate),
                    '-ac', str(self.channels),
                    normalized_file,
                    '-y'
                ]
                
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                normalized_files.append(normalized_file)
                
            except (subprocess.CalledProcessError, Exception) as e:
                self.logger.warning(f"Could not normalize chunk {chunk_file}: {str(e)}")
                normalized_files.append(chunk_file)  # Use original if normalization fails
                
        self.logger.info(f"Normalized {len([f for f in normalized_files if f.endswith('_normalized.wav')])} chunks")
        return normalized_files
    
    def _validate_stitched_timing(self, audio_path: str, segments_data: List[Dict]):
        """
        Validate that stitched audio timing matches expected segments.
        
        Args:
            audio_path: Path to stitched audio file
            segments_data: List of segment timing data
        """
        if not segments_data:
            return
            
        audio_info = self.get_audio_info(audio_path)
        actual_duration = audio_info.get('duration', 0)
        
        # Calculate expected duration from segments
        expected_duration = max(seg.get('end', 0) for seg in segments_data)
        
        # Allow 5% tolerance or 1 second, whichever is larger
        tolerance = max(expected_duration * 0.05, 1.0)
        duration_diff = abs(actual_duration - expected_duration)
        
        if duration_diff > tolerance:
            self.logger.warning(
                f"Timing validation failed: expected {expected_duration:.2f}s, "
                f"got {actual_duration:.2f}s (diff: {duration_diff:.2f}s)"
            )
        else:
            self.logger.info(
                f"Timing validation passed: {actual_duration:.2f}s "
                f"(expected {expected_duration:.2f}s)"
            )
            
    def _build_sync_command(self, video_path: str, audio_path: str, output_path: str, strategy: str) -> List[str]:
        """
        Build FFmpeg command for audio-video synchronization.
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path to output file
            strategy: Sync strategy ('standard' or 'audio_reference')
            
        Returns:
            FFmpeg command as list of strings
        """
        base_cmd = [
            'ffmpeg',
            '-i', video_path,      # Input video
            '-i', audio_path,      # Input audio
        ]
        
        if strategy == 'audio_reference':
            # Use audio duration as reference, pad or trim video as needed
            cmd = base_cmd + [
                '-c:v', 'copy',        # Copy video stream
                '-c:a', PIPELINE_DEFAULTS["audio_codec"],  # Encode audio
                '-map', '0:v:0',       # Map video from first input
                '-map', '1:a:0',       # Map audio from second input
                '-filter_complex', '[0:v]setpts=PTS-STARTPTS[v]',  # Reset video timing
                '-map', '[v]',         # Use filtered video
                '-avoid_negative_ts', 'make_zero',  # Handle timing issues
                output_path,
                '-y'                   # Overwrite output file
            ]
        else:
            # Standard sync - use shortest stream
            cmd = base_cmd + [
                '-c:v', PIPELINE_DEFAULTS["video_codec"],  # Copy video stream
                '-c:a', PIPELINE_DEFAULTS["audio_codec"],  # Encode audio
                '-map', '0:v:0',       # Map video from first input
                '-map', '1:a:0',       # Map audio from second input
                '-shortest',           # End when shortest stream ends
                output_path,
                '-y'                   # Overwrite output file
            ]
            
        return cmd
    
    def _get_video_info(self, video_path: str) -> Dict:
        """
        Get detailed information about video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            info = json.loads(result.stdout)
            
            # Extract video stream information
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), {})
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),  # Convert fraction to float
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': int(info['format'].get('bit_rate', 0))
            }
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to get video info: {str(e)}")
            return {}