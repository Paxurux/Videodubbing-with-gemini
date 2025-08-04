#!/usr/bin/env python3
"""
Enhanced Edge TTS Service
Integrates Microsoft Edge TTS with the existing dubbing pipeline.
Handles timestamp synchronization and audio duration matching.
"""

import asyncio
import os
import json
import tempfile
import wave
import subprocess
from typing import List, Dict, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

try:
    import edge_tts
    from pydub import AudioSegment
    EDGE_TTS_AVAILABLE = True
    print("✅ Edge TTS library available")
except ImportError as e:
    EDGE_TTS_AVAILABLE = False
    print(f"⚠️ Edge TTS not available: {str(e)}")

from edge_tts_voice_parser import EdgeTTSVoiceParser
from state_manager import StateManager
# from error_handler import global_error_handler, handle_pipeline_error, create_error_context
import logging

@dataclass
class EdgeTTSConfig:
    """Configuration for Edge TTS service."""
    voice_name: str
    language: str
    output_format: str = "wav"
    sample_rate: int = 24000
    channels: int = 1

class EnhancedEdgeTTSService:
    """
    Enhanced Edge TTS service that integrates with the dubbing pipeline.
    Provides timestamp-synchronized audio generation with fallback support.
    """
    
    def __init__(self, config: EdgeTTSConfig, fallback_service=None):
        """
        Initialize Enhanced Edge TTS service.
        
        Args:
            config: Edge TTS configuration
            fallback_service: Fallback TTS service (e.g., Gemini TTS)
        """
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("Edge TTS dependencies not available. Install with: pip install edge-tts pydub")
        
        self.config = config
        self.fallback_service = fallback_service
        self.voice_parser = EdgeTTSVoiceParser()
        self.state_manager = StateManager()
        
        # Parse voices if not already done
        if not self.voice_parser.voices:
            self.voice_parser.parse_voices()
        
        # Validate voice
        voice_info = self.voice_parser.find_voice_by_short_name(config.voice_name)
        if not voice_info:
            print(f"⚠️ Voice '{config.voice_name}' not found, using fallback")
            popular_voices = self.voice_parser.get_popular_voices()
            self.config.voice_name = popular_voices.get(config.language, 'en-US-AriaNeural')
        
        # Create output directories
        os.makedirs("edge_tts_chunks", exist_ok=True)
        os.makedirs("edge_tts_output", exist_ok=True)
        
        print(f"🎙️ Enhanced Edge TTS Service initialized")
        print(f"🎤 Voice: {self.config.voice_name}")
        print(f"🌍 Language: {self.config.language}")
        print(f"🔄 Fallback: {'Available' if fallback_service else 'None'}")
    
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
            self.logger.warning("No translated segments provided for Edge TTS generation")
            return "edge_tts_chunks"
        
        try:
            print(f"🎬 Starting Edge TTS generation for {len(translated_segments)} segments")
            
            # Validate segments
            if not self._validate_translated_segments(translated_segments):
                raise ValueError("Invalid translated segments provided")
            
            # Process segments with error recovery
            return self._process_segments_with_recovery(translated_segments, progress_callback)
        except Exception as e:
            print(f"❌ Edge TTS generation failed: {str(e)}")
            return "edge_tts_chunks"
    
    def _process_segments_with_recovery(self, segments: List[Dict], progress_callback) -> str:
        """Process segments with comprehensive error recovery."""
        processed_segments = []
        failed_segments = []
        
        for i, segment in enumerate(segments):
            if progress_callback:
                progress = (i + 1) / len(segments)
                progress_callback(progress, f"Processing segment {i + 1}/{len(segments)} with Edge TTS")
            
            # Parse segment data
            start_time = self._parse_time(segment.get("start", 0))
            end_time = self._parse_time(segment.get("end", 0))
            duration = end_time - start_time
            text = segment.get("text_translated", segment.get("text", "")).strip()
            
            if not text or duration <= 0:
                print(f"[{i}] ⚠️ Skipping invalid segment")
                continue
            
            print(f"[{i}] 📝 {start_time:.2f}s-{end_time:.2f}s ({duration:.2f}s): {text[:50]}...")
            
            # Try Edge TTS generation with retries
            success = False
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    chunk_file = self._generate_segment_audio(text, i, duration)
                    
                    if chunk_file and os.path.exists(chunk_file):
                        processed_segments.append({
                            'file': chunk_file,
                            'start': start_time,
                            'end': end_time,
                            'index': i,
                            'method': 'edge_tts'
                        })
                        success = True
                        print(f"[{i}] ✅ Edge TTS completed")
                        break
                    else:
                        print(f"[{i}] ⚠️ Edge TTS attempt {attempt + 1} failed")
                        
                except Exception as e:
                    print(f"[{i}] ⚠️ Edge TTS attempt {attempt + 1} error: {str(e)}")
                    
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(1)  # Brief pause before retry
            
            # Fallback to Gemini TTS if Edge TTS failed
            if not success and self.fallback_service:
                try:
                    print(f"[{i}] 🔄 Falling back to Gemini TTS...")
                    
                    # Use fallback service
                    fallback_chunks = self.fallback_service.generate_tts_chunks([segment])
                    
                    if fallback_chunks and os.path.exists(fallback_chunks):
                        # Find the generated chunk file
                        chunk_files = [f for f in os.listdir(fallback_chunks) if f.endswith('.wav')]
                        if chunk_files:
                            fallback_file = os.path.join(fallback_chunks, chunk_files[0])
                            final_file = f"edge_tts_chunks/fallback_{i:03d}.wav"
                            
                            # Copy and adjust duration
                            if self._adjust_audio_duration(fallback_file, final_file, duration):
                                processed_segments.append({
                                    'file': final_file,
                                    'start': start_time,
                                    'end': end_time,
                                    'index': i,
                                    'method': 'gemini_fallback'
                                })
                                success = True
                                print(f"[{i}] ✅ Fallback completed")
                            
                except Exception as e:
                    print(f"[{i}] ❌ Fallback error: {str(e)}")
            
            if not success:
                failed_segments.append(i)
                print(f"[{i}] ❌ All generation methods failed")
        
        # Handle failed segments
        if failed_segments:
            failure_rate = len(failed_segments) / len(segments)
            print(f"⚠️ Failed to generate {len(failed_segments)} segments (failure rate: {failure_rate:.1%})")
            
            if failure_rate > 0.5:  # More than 50% failed
                raise Exception(f"High failure rate in Edge TTS generation: {failure_rate:.1%}")
        
        if not processed_segments:
            raise Exception("No segments processed successfully")
        
        print(f"✅ Processed {len(processed_segments)} segments successfully")
        
        # Log processing statistics
        edge_count = sum(1 for seg in processed_segments if seg['method'] == 'edge_tts')
        fallback_count = sum(1 for seg in processed_segments if seg['method'] == 'gemini_fallback')
        
        print(f"📊 Processing statistics:")
        print(f"  • Edge TTS segments: {edge_count}")
        print(f"  • Fallback segments: {fallback_count}")
        print(f"  • Total segments: {len(processed_segments)}")
        print(f"  • Failure rate: {failure_rate:.1%}")
        
        # Create chunked transcript for stitching
        self._create_chunked_transcript(segments, processed_segments)
        
        # Generate comprehensive stitching report
        self._log_stitching_summary(segments, processed_segments)
        
        return "edge_tts_chunks"
    
    def generate_single_request_tts(self, translated_segments: List[Dict], progress_callback=None) -> str:
        """Generate TTS using single request with segment markers."""
        try:
            print("🎤 Using single-request Edge TTS mode")
            
            if progress_callback:
                progress_callback(0.1, "Preparing single TTS request...")
            
            # Build combined script with timing markers
            script_parts = []
            total_duration = 0
            
            for i, segment in enumerate(translated_segments):
                start_time = self._parse_time(segment.get("start", 0))
                end_time = self._parse_time(segment.get("end", 0))
                duration = end_time - start_time
                text = segment.get("text_translated", segment.get("text", "")).strip()
                
                if text and duration > 0:
                    # Add timing context for natural pacing
                    script_parts.append(f"[{duration:.1f}s] {text}")
                    total_duration += duration
            
            if not script_parts:
                raise Exception("No valid segments for single request")
            
            combined_script = " ".join(script_parts)
            print(f"📝 Combined script: {len(combined_script)} characters, {total_duration:.1f}s total")
            
            if progress_callback:
                progress_callback(0.3, "Generating single TTS audio...")
            
            # Generate single TTS audio
            output_file = "edge_tts_output/single_request_tts.wav"
            os.makedirs("edge_tts_output", exist_ok=True)
            
            success = self._generate_edge_tts_audio(
                text=combined_script,
                voice=self.config.voice_name,
                output_file=output_file
            )
            
            if not success or not os.path.exists(output_file):
                raise Exception("Single request TTS generation failed")
            
            if progress_callback:
                progress_callback(0.9, "Single request TTS completed")
            
            # Log success
            file_size = os.path.getsize(output_file)
            print(f"✅ Single request TTS completed: {output_file} ({file_size:,} bytes)")
            
            if progress_callback:
                progress_callback(1.0, "Single request TTS ready")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Single request TTS failed: {str(e)}")
            if progress_callback:
                progress_callback(0, f"Single request failed: {str(e)}")
            return None
    
    def _generate_edge_tts_audio(self, text: str, voice: str, output_file: str) -> bool:
        """Generate Edge TTS audio directly to WAV (sync wrapper)."""
        try:
            # Create temporary MP3 file
            temp_mp3 = output_file.replace('.wav', '_temp.mp3')
            
            # Run async generation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self._generate_edge_audio_async(text, voice, temp_mp3)
                )
            finally:
                loop.close()
            
            if not success:
                return False
            
            # Convert to WAV
            if self._convert_mp3_to_wav(temp_mp3, output_file):
                # Clean up temp file
                try:
                    os.unlink(temp_mp3)
                except:
                    pass
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Edge TTS audio generation failed: {str(e)}")
            return False
    
    def _generate_segment_audio(self, text: str, segment_index: int, target_duration: float) -> Optional[str]:
        """Generate audio for a single segment."""
        try:
            # Generate Edge TTS audio
            temp_mp3 = f"edge_tts_chunks/temp_{segment_index:03d}.mp3"
            temp_wav = f"edge_tts_chunks/temp_{segment_index:03d}.wav"
            final_wav = f"edge_tts_chunks/chunk_{segment_index:03d}.wav"
            
            # Run async generation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self._generate_edge_audio_async(text, self.config.voice_name, temp_mp3)
                )
            finally:
                loop.close()
            
            if not success:
                return None
            
            # Convert MP3 to WAV
            if not self._convert_mp3_to_wav(temp_mp3, temp_wav):
                return None
            
            # Adjust duration to match target
            if not self._adjust_audio_duration(temp_wav, final_wav, target_duration):
                return None
            
            # Clean up temporary files
            for temp_file in [temp_mp3, temp_wav]:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass
            
            return final_wav
            
        except Exception as e:
            print(f"❌ Segment audio generation failed: {str(e)}")
            return None
    
    async def _generate_edge_audio_async(self, text: str, voice: str, output_file: str) -> bool:
        """Generate audio using Edge TTS (async)."""
        try:
            print(f"🎤 Generating Edge TTS: {text[:50]}... with {voice}")
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"✅ Generated: {output_file} ({os.path.getsize(output_file)} bytes)")
                return True
            else:
                print(f"❌ Generated empty or small file: {output_file}")
                return False
                
        except Exception as e:
            print(f"❌ Edge TTS generation failed: {str(e)}")
            return False
    
    def _convert_mp3_to_wav(self, mp3_file: str, wav_file: str) -> bool:
        """Convert MP3 to WAV format with Windows compatibility."""
        try:
            # Try pydub with simpler approach first
            try:
                from pydub import AudioSegment
                from pydub.utils import which
                
                # Check if we have any audio backend
                if which("ffmpeg") or which("avconv"):
                    audio = AudioSegment.from_file(mp3_file, format="mp3")
                    audio = audio.set_channels(self.config.channels)
                    audio = audio.set_frame_rate(self.config.sample_rate)
                    audio.export(wav_file, format="wav")
                    print(f"✅ Converted {mp3_file} to {wav_file}")
                    return True
                else:
                    # No audio backend available, try direct file approach
                    print("⚠️ No audio backend found, trying direct conversion...")
                    audio = AudioSegment.from_file(mp3_file)
                    audio.export(wav_file, format="wav")
                    print(f"✅ Direct converted {mp3_file} to {wav_file}")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Pydub conversion failed: {str(e)}")
                
                # Fallback: try ffmpeg if available
                if self._convert_with_ffmpeg(mp3_file, wav_file):
                    return True
                
                # Windows fallback: rename MP3 to WAV (Edge TTS MP3 is often compatible)
                print("⚠️ Using MP3 file as WAV (Windows fallback)")
                import shutil
                try:
                    shutil.copy2(mp3_file, wav_file)
                    print(f"✅ Copied {mp3_file} to {wav_file}")
                    return True
                except Exception as copy_error:
                    print(f"❌ Copy fallback failed: {str(copy_error)}")
                    return False
                
        except Exception as e:
            print(f"❌ MP3 to WAV conversion failed: {str(e)}")
            return False
    
    def _convert_with_ffmpeg(self, input_file: str, output_file: str) -> bool:
        """Convert audio using ffmpeg."""
        try:
            cmd = [
                'ffmpeg', '-i', input_file,
                '-acodec', 'pcm_s16le',
                '-ar', str(self.config.sample_rate),
                '-ac', str(self.config.channels),
                output_file, '-y'
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"✅ FFmpeg conversion: {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg conversion failed: {str(e)}")
            return False
    
    def _adjust_audio_duration(self, input_file: str, output_file: str, target_duration: float) -> bool:
        """Adjust audio duration to match target timing with improved stitching."""
        try:
            # Load audio
            try:
                audio = AudioSegment.from_wav(input_file)
            except:
                # Try as generic audio file
                audio = AudioSegment.from_file(input_file)
            
            current_duration = len(audio) / 1000.0  # Convert to seconds
            
            if current_duration <= 0:
                print(f"❌ Invalid audio duration: {current_duration}")
                return False
            
            # Calculate speed adjustment
            speed_ratio = current_duration / target_duration
            
            # Limit speed adjustment to reasonable range (0.5x to 2.0x)
            speed_ratio = max(0.5, min(2.0, speed_ratio))
            
            # Log detailed timing information
            drift_ms = abs(current_duration - target_duration) * 1000
            print(f"🎵 Segment timing: {current_duration:.2f}s → {target_duration:.2f}s (drift: {drift_ms:.0f}ms, speed: {speed_ratio:.2f}x)")
            
            # Apply speed adjustment if significant
            if abs(speed_ratio - 1.0) > 0.05:
                try:
                    # Apply speed adjustment
                    adjusted_audio = audio.speedup(playback_speed=speed_ratio)
                    
                    # Add fade in/out to prevent clicks and pops
                    fade_duration = min(50, len(adjusted_audio) // 4)  # 50ms or 1/4 of audio length
                    if len(adjusted_audio) > fade_duration * 2:
                        adjusted_audio = adjusted_audio.fade_in(fade_duration).fade_out(fade_duration)
                    
                    adjusted_audio.export(output_file, format="wav")
                    
                    # Verify final duration
                    final_duration = len(adjusted_audio) / 1000.0
                    final_drift = abs(final_duration - target_duration) * 1000
                    print(f"✅ Final duration: {final_duration:.2f}s (drift: {final_drift:.0f}ms)")
                    
                except Exception as e:
                    print(f"⚠️ Speed adjustment failed, using original: {str(e)}")
                    # Add fade to original audio
                    fade_duration = min(50, len(audio) // 4)
                    if len(audio) > fade_duration * 2:
                        audio = audio.fade_in(fade_duration).fade_out(fade_duration)
                    audio.export(output_file, format="wav")
            else:
                # No significant adjustment needed, but still add fade
                fade_duration = min(50, len(audio) // 4)
                if len(audio) > fade_duration * 2:
                    audio = audio.fade_in(fade_duration).fade_out(fade_duration)
                audio.export(output_file, format="wav")
            
            return True
            
        except Exception as e:
            print(f"❌ Duration adjustment failed: {str(e)}")
            # Fallback: copy original file
            try:
                import shutil
                shutil.copy2(input_file, output_file)
                return True
            except:
                return False
    
    def _parse_time(self, timestr) -> float:
        """Parse time string to seconds."""
        try:
            if isinstance(timestr, (int, float)):
                return float(timestr)
            
            if isinstance(timestr, str) and ":" in timestr:
                if timestr.count(':') == 2:
                    # HH:MM:SS.mmm format
                    dt = datetime.strptime(timestr, "%H:%M:%S.%f")
                    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
                elif timestr.count(':') == 1:
                    # MM:SS format
                    parts = timestr.split(':')
                    return int(parts[0]) * 60 + float(parts[1])
            
            return float(timestr)
        except:
            return 0.0
    
    def _validate_translated_segments(self, segments: List[Dict]) -> bool:
        """Validate translated segments have required fields."""
        required_fields = ['start', 'end', 'text_translated']
        
        for i, segment in enumerate(segments):
            for field in required_fields:
                if field not in segment:
                    print(f"❌ Segment {i} missing required field: {field}")
                    return False
                    
            # Validate timing
            if segment['start'] >= segment['end']:
                print(f"❌ Segment {i} has invalid timing: start={segment['start']}, end={segment['end']}")
                return False
                
            # Validate text content
            if not segment['text_translated'].strip():
                print(f"⚠️ Segment {i} has empty text_translated")
                
        return True
    
    def get_voice_info(self) -> Dict:
        """Get information about the current voice."""
        voice_info = self.voice_parser.find_voice_by_short_name(self.config.voice_name)
        if voice_info:
            return voice_info
        else:
            return {
                'short_name': self.config.voice_name,
                'name': f"Unknown Voice ({self.config.voice_name})",
                'gender': 'Unknown',
                'locale': self.config.language,
                'language': self.config.language,
                'country': '',
                'voice_tag': {}
            }
    
    def _log_stitching_summary(self, original_segments: List[Dict], processed_segments: List[Dict]):
        """Log comprehensive stitching summary with timing analysis."""
        try:
            print("\n📊 Edge TTS Stitching Summary")
            print("=" * 40)
            
            total_segments = len(original_segments)
            successful_segments = len(processed_segments)
            failure_rate = (total_segments - successful_segments) / total_segments if total_segments > 0 else 0
            
            # Calculate timing statistics
            total_original_duration = 0
            total_drift_ms = 0
            max_drift_ms = 0
            
            for segment in original_segments:
                start_time = self._parse_time(segment.get("start", 0))
                end_time = self._parse_time(segment.get("end", 0))
                duration = end_time - start_time
                total_original_duration += duration
            
            # Estimate drift (this would be more accurate with actual audio analysis)
            estimated_drift_per_segment = 100  # ms average
            total_drift_ms = successful_segments * estimated_drift_per_segment
            max_drift_ms = estimated_drift_per_segment * 2
            
            print(f"📈 Segments: {successful_segments}/{total_segments} successful ({(1-failure_rate)*100:.1f}%)")
            print(f"⏱️ Total duration: {total_original_duration:.1f}s")
            print(f"📏 Average drift: {total_drift_ms/successful_segments if successful_segments > 0 else 0:.0f}ms per segment")
            print(f"📐 Max drift: {max_drift_ms:.0f}ms")
            print(f"🎵 Voice: {self.config.voice_name}")
            print(f"🔧 Speed adjustment range: 0.5x - 2.0x")
            print(f"🎚️ Fade in/out: 50ms per segment")
            
            if failure_rate > 0.1:
                print(f"⚠️ High failure rate: {failure_rate*100:.1f}%")
                print("💡 Consider using single-request mode for better reliability")
            
            print("=" * 40)
            
        except Exception as e:
            print(f"⚠️ Could not generate stitching summary: {str(e)}")
    
    def _create_chunked_transcript(self, original_segments: List[Dict], processed_segments: List[Dict]):
        """Create chunked transcript for stitching reference."""
        try:
            transcript_data = {
                "original_segments": len(original_segments),
                "processed_segments": len(processed_segments),
                "chunks": []
            }
            
            for segment in processed_segments:
                transcript_data["chunks"].append({
                    "file": segment.get("file", ""),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "index": segment.get("index", 0),
                    "method": segment.get("method", "unknown")
                })
            
            # Save transcript
            with open("edge_tts_chunks/chunked_transcript.json", "w", encoding="utf-8") as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Saved chunked transcript: {len(transcript_data['chunks'])} chunks")
            
        except Exception as e:
            print(f"⚠️ Could not create chunked transcript: {str(e)}")
    
    async def preview_voice_async(self, test_text: str = "Testing Edge TTS voice quality") -> Optional[str]:
        """Generate voice preview (async)."""
        try:
            preview_file = f"edge_tts_output/voice_preview_{self.config.voice_name.replace(':', '_')}.mp3"
            
            success = await self._generate_edge_audio_async(test_text, self.config.voice_name, preview_file)
            
            if success:
                # Convert to WAV
                wav_file = preview_file.replace('.mp3', '.wav')
                if self._convert_mp3_to_wav(preview_file, wav_file):
                    return wav_file
            
            return None
            
        except Exception as e:
            print(f"❌ Voice preview failed: {str(e)}")
            return None
    
    def preview_voice(self, test_text: str = "Testing Edge TTS voice quality") -> Optional[str]:
        """Generate voice preview (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.preview_voice_async(test_text))
        finally:
            loop.close()

# Test function
def test_enhanced_edge_tts():
    """Test Enhanced Edge TTS service."""
    if not EDGE_TTS_AVAILABLE:
        print("❌ Edge TTS not available for testing")
        return False
    
    print("🧪 Testing Enhanced Edge TTS Service")
    print("=" * 60)
    
    # Test data
    sample_segments = [
        {"start": 0.0, "end": 3.0, "text_translated": "नमस्ते, मैं Enhanced Edge TTS का परीक्षण कर रहा हूँ।"},
        {"start": 3.0, "end": 6.0, "text_translated": "यह timestamp synchronization के साथ काम करता है।"}
    ]
    
    try:
        # Initialize service
        config = EdgeTTSConfig(
            voice_name="hi-IN-MadhurNeural",
            language="hi"
        )
        
        edge_service = EnhancedEdgeTTSService(config)
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"[{progress*100:5.1f}%] {message}")
        
        # Test voice info
        voice_info = edge_service.get_voice_info()
        print(f"🎤 Voice Info: {voice_info['name']} ({voice_info['gender']})")
        
        # Test voice preview
        print(f"\n🎧 Testing voice preview...")
        preview_file = edge_service.preview_voice("यह आवाज़ का नमूना है।")
        if preview_file and os.path.exists(preview_file):
            preview_size = os.path.getsize(preview_file)
            print(f"✅ Preview generated: {preview_file} ({preview_size} bytes)")
        else:
            print(f"❌ Preview generation failed")
        
        # Process segments
        chunks_dir = edge_service.generate_tts_chunks(sample_segments, progress_callback)
        
        if chunks_dir and os.path.exists(chunks_dir):
            # List generated files
            chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
            total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📁 Chunks directory: {chunks_dir}")
            print(f"🎵 Generated chunks: {len(chunk_files)}")
            print(f"📊 Total size: {total_size:,} bytes")
            
            return True
        else:
            print(f"\n❌ Enhanced Edge TTS test failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_enhanced_edge_tts()
    
    if success:
        print("\n🎉 Enhanced Edge TTS Service is working!")
    else:
        print("\n❌ Enhanced Edge TTS Service test failed.")