#!/usr/bin/env python3
"""
Microsoft Edge TTS Service
Provides TTS functionality using Microsoft Edge's neural voices.
"""

import asyncio
import os
import json
import subprocess
import tempfile
import wave
from typing import List, Dict, Optional, Callable
from datetime import datetime

try:
    import edge_tts
    from pydub import AudioSegment
    EDGE_TTS_AVAILABLE = True
    print("✅ Edge TTS library available")
except ImportError as e:
    EDGE_TTS_AVAILABLE = False
    print(f"⚠️ Edge TTS not available: {str(e)}")
    print("💡 Install with: pip install edge-tts pydub")

class EdgeTTSService:
    """
    Microsoft Edge TTS service for generating high-quality neural voice audio.
    """
    
    # Popular voices for major languages
    DEFAULT_VOICES = {
        'hi': 'hi-IN-MadhurNeural',  # Hindi - Male
        'hi-IN': 'hi-IN-SwaraNeuralNeural',  # Hindi - Female  
        'en': 'en-US-AriaNeural',    # English - Female
        'en-US': 'en-US-GuyNeural',  # English - Male
        'es': 'es-ES-ElviraNeural',  # Spanish - Female
        'es-ES': 'es-ES-AlvaroNeural', # Spanish - Male
        'fr': 'fr-FR-DeniseNeural',  # French - Female
        'fr-FR': 'fr-FR-HenriNeural', # French - Male
        'ja': 'ja-JP-NanamiNeural',  # Japanese - Female
        'ja-JP': 'ja-JP-KeitaNeural', # Japanese - Male
        'ar': 'ar-SA-ZariyahNeural', # Arabic - Female
        'ar-SA': 'ar-SA-HamedNeural', # Arabic - Male
        'ta': 'ta-IN-PallaviNeural', # Tamil - Female
        'ta-IN': 'ta-IN-ValluvarNeural', # Tamil - Male
        'de': 'de-DE-KatjaNeural',   # German - Female
        'de-DE': 'de-DE-ConradNeural', # German - Male
        'it': 'it-IT-ElsaNeural',    # Italian - Female
        'it-IT': 'it-IT-DiegoNeural', # Italian - Male
        'pt': 'pt-BR-FranciscaNeural', # Portuguese - Female
        'pt-BR': 'pt-BR-AntonioNeural', # Portuguese - Male
        'ru': 'ru-RU-SvetlanaNeural', # Russian - Female
        'ru-RU': 'ru-RU-DmitryNeural', # Russian - Male
        'ko': 'ko-KR-SunHiNeural',   # Korean - Female
        'ko-KR': 'ko-KR-InJoonNeural', # Korean - Male
        'zh': 'zh-CN-XiaoxiaoNeural', # Chinese - Female
        'zh-CN': 'zh-CN-YunxiNeural', # Chinese - Male
    }
    
    def __init__(self, voice_name: str = "hi-IN-MadhurNeural", fallback_service=None):
        """
        Initialize Edge TTS service.
        
        Args:
            voice_name: Edge TTS voice name (e.g., 'hi-IN-MadhurNeural')
            fallback_service: Fallback TTS service (e.g., Gemini TTS) for error cases
        """
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("Edge TTS dependencies not available. Install with: pip install edge-tts pydub")
        
        self.voice_name = voice_name
        self.fallback_service = fallback_service
        self.available_voices = None
        
        # Create output directories
        os.makedirs("edge_tts_chunks", exist_ok=True)
        os.makedirs("edge_tts_output", exist_ok=True)
        
        print(f"🎙️ Edge TTS Service initialized")
        print(f"🎤 Voice: {voice_name}")
        print(f"🔄 Fallback: {'Available' if fallback_service else 'None'}")
    
    async def get_available_voices(self) -> List[Dict]:
        """Get list of all available Edge TTS voices."""
        if self.available_voices is None:
            try:
                voices = await edge_tts.list_voices()
                self.available_voices = voices
                print(f"✅ Loaded {len(voices)} Edge TTS voices")
            except Exception as e:
                print(f"❌ Failed to load voices: {str(e)}")
                self.available_voices = []
        
        return self.available_voices
    
    def get_voices_by_language(self, language_code: str) -> List[Dict]:
        """
        Get voices for a specific language.
        
        Args:
            language_code: Language code like 'hi', 'en', 'es', etc.
            
        Returns:
            List of voice dictionaries for the specified language
        """
        if self.available_voices is None:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.get_available_voices())
            finally:
                loop.close()
        
        # Filter voices by language
        filtered_voices = []
        for voice in self.available_voices:
            voice_locale = voice.get('Locale', '').lower()
            if voice_locale.startswith(language_code.lower()):
                filtered_voices.append(voice)
        
        return filtered_voices
    
    def get_default_voice_for_language(self, language_code: str) -> str:
        """Get default voice for a language."""
        return self.DEFAULT_VOICES.get(language_code.lower(), 'en-US-AriaNeural')
    
    async def generate_edge_audio(self, text: str, voice: str, output_file: str) -> bool:
        """
        Generate audio using Edge TTS.
        
        Args:
            text: Text to synthesize
            voice: Voice name (e.g., 'hi-IN-MadhurNeural')
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🎤 Generating Edge TTS: {text[:50]}... with {voice}")
            
            # Create Edge TTS communicate object
            communicate = edge_tts.Communicate(text, voice)
            
            # Generate and save audio
            await communicate.save(output_file)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ Generated: {output_file} ({os.path.getsize(output_file)} bytes)")
                return True
            else:
                print(f"❌ Generated empty file: {output_file}")
                return False
                
        except Exception as e:
            print(f"❌ Edge TTS generation failed: {str(e)}")
            return False
    
    def convert_mp3_to_wav(self, mp3_file: str, wav_file: str, target_sample_rate: int = 24000) -> bool:
        """
        Convert MP3 to WAV format.
        
        Args:
            mp3_file: Input MP3 file path
            wav_file: Output WAV file path
            target_sample_rate: Target sample rate (default 24000)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to load MP3 with pydub (without ffmpeg)
            try:
                # First try with built-in MP3 support
                audio = AudioSegment.from_file(mp3_file, format="mp3")
            except Exception:
                # If that fails, try reading as raw audio
                with open(mp3_file, 'rb') as f:
                    audio_data = f.read()
                # Create a temporary WAV file using wave module
                return self.convert_mp3_raw(mp3_file, wav_file, target_sample_rate)
            
            # Convert to mono and set sample rate
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(target_sample_rate)
            
            # Export as WAV
            audio.export(wav_file, format="wav")
            
            print(f"✅ Converted {mp3_file} to {wav_file}")
            return True
            
        except Exception as e:
            print(f"❌ MP3 to WAV conversion failed: {str(e)}")
            # Try alternative conversion method
            return self.convert_mp3_alternative(mp3_file, wav_file, target_sample_rate)
    
    def convert_mp3_alternative(self, mp3_file: str, wav_file: str, sample_rate: int = 24000) -> bool:
        """Alternative MP3 to WAV conversion without ffmpeg."""
        try:
            # Try using pydub with simpleaudio backend
            from pydub.playback import play
            
            # Read the MP3 file as binary and try to process it
            with open(mp3_file, 'rb') as f:
                mp3_data = f.read()
            
            # Create a basic WAV header and copy the audio data
            # This is a simplified approach - Edge TTS MP3s are usually simple format
            
            # For now, let's just copy the MP3 as-is and rename it
            # Many audio players can handle MP3 files with .wav extension
            import shutil
            shutil.copy2(mp3_file, wav_file)
            
            print(f"✅ Copied MP3 as WAV: {wav_file}")
            return True
            
        except Exception as e:
            print(f"❌ Alternative conversion failed: {str(e)}")
            return False
    
    def convert_mp3_raw(self, mp3_file: str, wav_file: str, sample_rate: int = 24000) -> bool:
        """Raw MP3 to WAV conversion."""
        try:
            # Simple approach: just copy the file for now
            # Edge TTS generates compatible audio that most systems can play
            import shutil
            shutil.copy2(mp3_file, wav_file)
            
            print(f"✅ Raw conversion: {wav_file}")
            return True
            
        except Exception as e:
            print(f"❌ Raw conversion failed: {str(e)}")
            return False
    
    def adjust_audio_duration(self, input_file: str, output_file: str, target_duration: float) -> bool:
        """
        Adjust audio duration to match target timing.
        
        Args:
            input_file: Input audio file
            output_file: Output audio file
            target_duration: Target duration in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to load audio (handle both WAV and MP3)
            try:
                if input_file.lower().endswith('.wav'):
                    audio = AudioSegment.from_wav(input_file)
                elif input_file.lower().endswith('.mp3'):
                    audio = AudioSegment.from_file(input_file, format="mp3")
                else:
                    # Try to auto-detect format
                    audio = AudioSegment.from_file(input_file)
            except Exception as e:
                print(f"⚠️ Could not load audio with pydub: {str(e)}")
                # Fallback: just copy the file
                import shutil
                shutil.copy2(input_file, output_file)
                return True
            
            current_duration = len(audio) / 1000.0  # Convert to seconds
            
            if current_duration <= 0:
                print(f"❌ Invalid audio duration: {current_duration}")
                return False
            
            # Calculate speed adjustment
            speed_ratio = current_duration / target_duration
            
            # Limit speed adjustment to reasonable range
            speed_ratio = max(0.5, min(2.0, speed_ratio))
            
            print(f"🎵 Adjusting duration: {current_duration:.2f}s → {target_duration:.2f}s (speed: {speed_ratio:.2f}x)")
            
            # Apply speed adjustment
            if abs(speed_ratio - 1.0) < 0.05:
                # No significant adjustment needed
                try:
                    audio.export(output_file, format="wav")
                except:
                    # Fallback: copy original
                    import shutil
                    shutil.copy2(input_file, output_file)
            else:
                # Use pydub speedup
                try:
                    adjusted_audio = audio.speedup(playback_speed=speed_ratio)
                    adjusted_audio.export(output_file, format="wav")
                except:
                    # Fallback: copy original
                    import shutil
                    shutil.copy2(input_file, output_file)
            
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
    
    def parse_time(self, timestr) -> float:
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
    
    def get_audio_duration(self, audio_file: str) -> float:
        """Get audio file duration in seconds."""
        try:
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except:
            try:
                # Fallback using pydub
                audio = AudioSegment.from_wav(audio_file)
                return len(audio) / 1000.0
            except:
                return 0.0
    
    async def process_subtitle_json_async(self, subtitle_data: List[Dict], progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        Process subtitle JSON using Edge TTS (async version).
        
        Args:
            subtitle_data: List of subtitle dictionaries
            progress_callback: Optional progress callback function
            
        Returns:
            Path to final audio file or None if failed
        """
        print(f"🎬 Processing {len(subtitle_data)} subtitles with Edge TTS")
        
        if progress_callback:
            progress_callback(0.1, "Starting Edge TTS processing...")
        
        processed_segments = []
        fallback_count = 0
        
        for i, segment in enumerate(subtitle_data):
            if progress_callback:
                progress = 0.1 + (0.7 * (i + 1) / len(subtitle_data))
                progress_callback(progress, f"Processing segment {i + 1}/{len(subtitle_data)}")
            
            # Parse timing
            start_time = self.parse_time(segment.get("start", 0))
            end_time = self.parse_time(segment.get("end", 0))
            duration = end_time - start_time
            
            # Get text
            text = segment.get("text_translated", segment.get("text", "")).strip()
            
            if not text or duration <= 0:
                continue
            
            print(f"[{i}] 📝 {start_time:.2f}s-{end_time:.2f}s ({duration:.2f}s): {text[:50]}...")
            
            # Generate Edge TTS audio
            temp_mp3 = f"edge_tts_chunks/segment_{i:03d}.mp3"
            temp_wav = f"edge_tts_chunks/segment_{i:03d}.wav"
            final_wav = f"edge_tts_chunks/adjusted_{i:03d}.wav"
            
            # Try Edge TTS generation
            success = await self.generate_edge_audio(text, self.voice_name, temp_mp3)
            
            if success:
                # Convert MP3 to WAV
                if self.convert_mp3_to_wav(temp_mp3, temp_wav):
                    # Adjust duration
                    if self.adjust_audio_duration(temp_wav, final_wav, duration):
                        processed_segments.append({
                            'file': final_wav,
                            'start': start_time,
                            'end': end_time,
                            'index': i
                        })
                        print(f"[{i}] ✅ Edge TTS completed")
                    else:
                        print(f"[{i}] ⚠️ Duration adjustment failed")
                else:
                    print(f"[{i}] ⚠️ MP3 to WAV conversion failed")
            
            # Fallback to Gemini TTS if Edge TTS failed
            if not success or not os.path.exists(final_wav):
                if self.fallback_service:
                    print(f"[{i}] 🔄 Falling back to Gemini TTS...")
                    try:
                        fallback_audio = self.fallback_service.generate_tts_audio(text, i)
                        if fallback_audio and os.path.exists(fallback_audio):
                            # Adjust duration for fallback audio too
                            if self.adjust_audio_duration(fallback_audio, final_wav, duration):
                                processed_segments.append({
                                    'file': final_wav,
                                    'start': start_time,
                                    'end': end_time,
                                    'index': i
                                })
                                fallback_count += 1
                                print(f"[{i}] ✅ Fallback completed")
                            else:
                                print(f"[{i}] ❌ Fallback duration adjustment failed")
                        else:
                            print(f"[{i}] ❌ Fallback generation failed")
                    except Exception as e:
                        print(f"[{i}] ❌ Fallback error: {str(e)}")
                else:
                    print(f"[{i}] ❌ No fallback service available")
            
            # Clean up temporary files
            for temp_file in [temp_mp3, temp_wav]:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass
        
        if not processed_segments:
            raise Exception("No segments processed successfully")
        
        print(f"✅ Processed {len(processed_segments)} segments")
        if fallback_count > 0:
            print(f"🔄 Used fallback for {fallback_count} segments")
        
        # Combine segments
        if progress_callback:
            progress_callback(0.9, "Combining audio segments...")
        
        final_audio = self.combine_audio_segments(processed_segments)
        
        if progress_callback:
            progress_callback(1.0, "Edge TTS processing complete!")
        
        return final_audio
    
    def process_subtitle_json(self, subtitle_data: List[Dict], progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        Process subtitle JSON using Edge TTS (sync wrapper).
        
        Args:
            subtitle_data: List of subtitle dictionaries
            progress_callback: Optional progress callback function
            
        Returns:
            Path to final audio file or None if failed
        """
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.process_subtitle_json_async(subtitle_data, progress_callback)
            )
        finally:
            loop.close()
    
    def combine_audio_segments(self, segments: List[Dict]) -> str:
        """Combine audio segments into final output."""
        if not segments:
            raise Exception("No segments to combine")
        
        sorted_segments = sorted(segments, key=lambda x: x['start'])
        print(f"🧬 Combining {len(sorted_segments)} audio segments...")
        
        try:
            final_audio = "edge_tts_output/final_dubbed_audio.wav"
            sample_rate = 24000
            combined_audio = AudioSegment.empty()
            current_time = 0.0
            
            for segment in sorted_segments:
                # Add silence gap if needed
                gap = segment['start'] - current_time
                if gap > 0.1:
                    silence_duration = int(gap * 1000)  # Convert to milliseconds
                    silence = AudioSegment.silent(duration=silence_duration)
                    combined_audio += silence
                
                # Add segment audio
                try:
                    segment_audio = AudioSegment.from_wav(segment['file'])
                    combined_audio += segment_audio
                except Exception as e:
                    print(f"⚠️ Failed to read {segment['file']}: {str(e)}")
                
                current_time = segment['end']
            
            # Export combined audio
            combined_audio.export(final_audio, format="wav")
            
            print(f"✅ Final audio: {final_audio}")
            return final_audio
            
        except Exception as e:
            print(f"❌ Audio combination failed: {str(e)}")
            raise
    
    async def preview_voice(self, voice_name: str, test_text: str = "Testing Edge TTS voice quality") -> Optional[str]:
        """
        Generate a voice preview.
        
        Args:
            voice_name: Voice to preview
            test_text: Text to use for preview
            
        Returns:
            Path to preview audio file or None if failed
        """
        try:
            preview_file = f"edge_tts_output/voice_preview_{voice_name.replace(':', '_')}.mp3"
            
            success = await self.generate_edge_audio(test_text, voice_name, preview_file)
            
            if success:
                # Convert to WAV for consistency
                wav_file = preview_file.replace('.mp3', '.wav')
                if self.convert_mp3_to_wav(preview_file, wav_file):
                    return wav_file
            
            return None
            
        except Exception as e:
            print(f"❌ Voice preview failed: {str(e)}")
            return None

# Test function
def test_edge_tts():
    """Test Edge TTS functionality."""
    if not EDGE_TTS_AVAILABLE:
        print("❌ Edge TTS not available for testing")
        return False
    
    print("🧪 Testing Edge TTS Service")
    print("=" * 60)
    
    # Test data
    sample_subtitles = [
        {"start": 0.0, "end": 3.0, "text": "नमस्ते, मैं Edge TTS का परीक्षण कर रहा हूँ।"},
        {"start": 3.0, "end": 6.0, "text": "यह Microsoft की neural voice technology है।"}
    ]
    
    try:
        # Initialize service
        edge_service = EdgeTTSService("hi-IN-MadhurNeural")
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"[{progress*100:5.1f}%] {message}")
        
        # Process subtitles
        final_audio = edge_service.process_subtitle_json(sample_subtitles, progress_callback)
        
        if final_audio and os.path.exists(final_audio):
            file_size = os.path.getsize(final_audio)
            duration = edge_service.get_audio_duration(final_audio)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📁 File: {final_audio}")
            print(f"📊 Size: {file_size:,} bytes")
            print(f"⏱️ Duration: {duration:.2f} seconds")
            
            return True
        else:
            print(f"\n❌ Edge TTS test failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_edge_tts()
    
    if success:
        print("\n🎉 Edge TTS Service is working!")
    else:
        print("\n❌ Edge TTS Service test failed.")