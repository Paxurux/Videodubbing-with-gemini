#!/usr/bin/env python3
"""
Single-Request TTS Implementation
Converts JSON subtitles to formatted prompt and generates all audio in one API call.
"""

import json
import os
import wave
import time
import requests
import base64
import struct
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable

class SingleRequestTTS:
    """
    Single-request TTS service that converts JSON subtitles to formatted prompt
    and generates all dialogue in one Gemini TTS API call.
    """
    
    def __init__(self, api_key: str, voice_name: str = "Kore"):
        """Initialize with API key and voice configuration."""
        self.api_key = api_key
        self.voice_name = voice_name
        self.model = "gemini-2.5-flash-preview-tts"
        
        # Create output directories
        os.makedirs("single_request_output", exist_ok=True)
        
        print(f"🎙️ Single-Request TTS initialized")
        print(f"🔑 API Key: {api_key[:20]}...")
        print(f"🎤 Voice: {voice_name}")
        print(f"🤖 Model: {self.model}")
    
    def format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS format."""
        try:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        except:
            return "00:00"
    
    def parse_time(self, timestr) -> float:
        """Parse time string to seconds."""
        try:
            if isinstance(timestr, (int, float)):
                return float(timestr)
            
            if isinstance(timestr, str) and ":" in timestr:
                # Handle HH:MM:SS.mmm format
                if timestr.count(':') == 2:
                    dt = datetime.strptime(timestr, "%H:%M:%S.%f")
                    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
                # Handle MM:SS format
                elif timestr.count(':') == 1:
                    parts = timestr.split(':')
                    return int(parts[0]) * 60 + float(parts[1])
            
            return float(timestr)
        except:
            return 0.0
    
    def json_to_prompt(self, subtitle_data: List[Dict], instructions: str = "") -> str:
        """
        Convert JSON subtitle data to formatted Gemini TTS prompt.
        
        Args:
            subtitle_data: List of subtitle dictionaries with start, end, text, and optionally speaker
            instructions: Optional voice instructions (e.g., "Speak with excitement")
        
        Returns:
            Formatted prompt string for Gemini TTS
        """
        
        print(f"📝 Converting {len(subtitle_data)} subtitles to prompt format")
        
        # Base prompt with voice instructions
        base_instructions = f"""Read the following lines in natural Hindi using voice '{self.voice_name}'. 
Match the timing accurately from timestamps. Use appropriate pauses and pacing to fit the specified duration.
Speak clearly and naturally with proper emotional expression."""
        
        if instructions:
            base_instructions += f"\n\nAdditional instructions: {instructions}"
        
        prompt_lines = [base_instructions, ""]
        
        # Convert each subtitle to prompt format
        for i, segment in enumerate(subtitle_data):
            start_time = self.parse_time(segment.get("start", 0))
            end_time = self.parse_time(segment.get("end", 0))
            text = segment.get("text", "").strip()
            speaker = segment.get("speaker", "")
            
            if not text:
                continue
            
            # Format timing
            start_formatted = self.format_time(start_time)
            end_formatted = self.format_time(end_time)
            duration = end_time - start_time
            
            # Create prompt line
            if speaker:
                prompt_line = f"[{start_formatted} - {end_formatted}] {speaker}: {text}"
            else:
                prompt_line = f"[{start_formatted} - {end_formatted}] {text}"
            
            # Add duration hint for very short or long segments
            if duration < 1.0:
                prompt_line += " (speak quickly)"
            elif duration > 5.0:
                prompt_line += " (speak slowly with pauses)"
            
            prompt_lines.append(prompt_line)
            
            print(f"  [{i:02d}] {start_formatted}-{end_formatted} ({duration:.1f}s): {text[:50]}...")
        
        final_prompt = "\n".join(prompt_lines)
        
        print(f"✅ Generated prompt with {len(prompt_lines)-2} dialogue lines")
        print(f"📊 Total prompt length: {len(final_prompt)} characters")
        
        return final_prompt
    
    def generate_single_request_tts(self, prompt: str, output_filename: str = "final_dubbed_audio.wav") -> Optional[str]:
        """
        Generate TTS audio from formatted prompt in single API request.
        
        Args:
            prompt: Formatted prompt string
            output_filename: Output audio file name
            
        Returns:
            Path to generated audio file or None if failed
        """
        
        print(f"🎤 Generating TTS with single request...")
        print(f"📝 Prompt length: {len(prompt)} characters")
        
        try:
            # REST API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            
            # Request payload
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
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
            
            print(f"📤 Making single TTS request...")
            start_time = time.time()
            
            # Make request with longer timeout for large prompts
            response = requests.post(
                url, 
                headers={"Content-Type": "application/json"}, 
                json=payload, 
                timeout=60  # Longer timeout for single large request
            )
            
            request_time = time.time() - start_time
            print(f"📥 Response received in {request_time:.2f}s - Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract audio data
                if ('candidates' in result and result['candidates'] and 
                    'content' in result['candidates'][0] and 
                    'parts' in result['candidates'][0]['content']):
                    
                    parts = result['candidates'][0]['content']['parts']
                    
                    if parts and 'inlineData' in parts[0] and 'data' in parts[0]['inlineData']:
                        audio_b64 = parts[0]['inlineData']['data']
                        mime_type = parts[0]['inlineData'].get('mimeType', 'unknown')
                        
                        print(f"🎵 MIME Type: {mime_type}")
                        print(f"📊 Base64 length: {len(audio_b64):,} characters")
                        
                        if audio_b64:
                            # Decode audio data
                            audio_data = base64.b64decode(audio_b64)
                            print(f"📊 Decoded audio: {len(audio_data):,} bytes")
                            
                            if len(audio_data) > 1000:
                                output_path = os.path.join("single_request_output", output_filename)
                                
                                # Save as WAV file
                                if self.save_wave_file(output_path, audio_data):
                                    # Verify audio quality
                                    if self.verify_audio_quality(output_path):
                                        file_size = os.path.getsize(output_path)
                                        duration = self.get_audio_duration(output_path)
                                        print(f"✅ Generated single-request TTS: {output_path}")
                                        print(f"📊 File size: {file_size:,} bytes")
                                        print(f"⏱️ Duration: {duration:.2f} seconds")
                                        return output_path
                                    else:
                                        print(f"⚠️ Generated audio appears to be silent")
                                else:
                                    print(f"❌ Failed to save audio file")
                            else:
                                print(f"⚠️ Audio data too small: {len(audio_data)} bytes")
                        else:
                            print(f"❌ No audio data in response")
                    else:
                        print(f"❌ Invalid response structure")
                        print(f"Response keys: {list(result.keys())}")
                else:
                    print(f"❌ No candidates in response")
                    
            elif response.status_code == 429:
                print(f"⏳ Rate limited - single request approach may help reduce this")
                return None
            else:
                error_text = response.text[:300] if response.text else "No error details"
                print(f"❌ API error {response.status_code}: {error_text}")
                
        except Exception as e:
            print(f"❌ Single request failed: {str(e)}")
        
        return None
    
    def save_wave_file(self, filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bool:
        """Save PCM data as WAV file."""
        try:
            print(f"💾 Saving audio: {len(pcm_data)} bytes to {filename}")
            
            # Check if already WAV format
            if pcm_data.startswith(b'RIFF'):
                print("✅ Audio data is already WAV format")
                with open(filename, "wb") as f:
                    f.write(pcm_data)
                return True
            
            # Save as WAV with confirmed working parameters
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm_data)
            
            print(f"✅ Saved as {channels}ch, {sample_width*8}bit, {rate}Hz WAV")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save WAV file: {str(e)}")
            return False
    
    def verify_audio_quality(self, audio_file: str) -> bool:
        """Verify audio file has actual content and good quality."""
        try:
            with wave.open(audio_file, 'rb') as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                frames = wf.getnframes()
                duration = frames / float(framerate) if framerate > 0 else 0
                
                print(f"🔍 Audio verification:")
                print(f"   Format: {channels}ch, {sample_width*8}bit, {framerate}Hz")
                print(f"   Duration: {duration:.2f} seconds")
                print(f"   Frames: {frames:,}")
                
                if frames == 0:
                    print(f"   ❌ No audio frames")
                    return False
                
                # Read sample data for amplitude analysis
                sample_count = min(5000, frames)  # Check more samples for longer audio
                audio_data = wf.readframes(sample_count)
                
                if sample_width == 2:  # 16-bit
                    samples = struct.unpack(f'<{len(audio_data)//2}h', audio_data)
                    
                    if samples:
                        max_amplitude = max(abs(s) for s in samples)
                        avg_amplitude = sum(abs(s) for s in samples) / len(samples)
                        zero_count = sum(1 for s in samples if abs(s) < 10)
                        zero_percent = (zero_count / len(samples)) * 100
                        
                        print(f"   📈 Max amplitude: {max_amplitude:,} (out of 32,767)")
                        print(f"   📊 Avg amplitude: {avg_amplitude:.1f}")
                        print(f"   🔇 Near-zero samples: {zero_percent:.1f}%")
                        
                        # Quality assessment
                        if max_amplitude > 100:
                            print(f"   ✅ Audio has good amplitude")
                            
                            # Check for RMS if pydub is available
                            try:
                                from pydub import AudioSegment
                                audio = AudioSegment.from_wav(audio_file)
                                rms = audio.rms
                                print(f"   📊 RMS level: {rms}")
                                
                                if rms > 50:
                                    print(f"   ✅ Audio quality verified (RMS: {rms})")
                                    return True
                                else:
                                    print(f"   ⚠️ Low RMS level: {rms}")
                                    return max_amplitude > 200  # Higher threshold if RMS is low
                                    
                            except ImportError:
                                print(f"   ℹ️ pydub not available for RMS check")
                                return True  # Trust amplitude check
                            
                        elif max_amplitude > 50:
                            print(f"   ⚠️ Audio has moderate amplitude")
                            return True
                        else:
                            print(f"   ❌ Audio appears silent (max amplitude: {max_amplitude})")
                            return False
                    else:
                        print(f"   ❌ No samples found")
                        return False
                else:
                    print(f"   ⚠️ Unsupported sample width: {sample_width}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Verification failed: {str(e)}")
            return False
    
    def get_audio_duration(self, audio_file: str) -> float:
        """Get audio file duration in seconds."""
        try:
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except:
            return 0.0
    
    def process_subtitles_single_request(self, subtitle_data: List[Dict], 
                                       instructions: str = "", 
                                       progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        Main function: Process subtitles using single-request approach.
        
        Args:
            subtitle_data: List of subtitle dictionaries
            instructions: Optional voice instructions
            progress_callback: Optional progress callback function
            
        Returns:
            Path to generated audio file or None if failed
        """
        
        print(f"🎬 Processing {len(subtitle_data)} subtitles with single-request TTS")
        
        if progress_callback:
            progress_callback(0.1, "Converting subtitles to prompt format...")
        
        # Step 1: Convert JSON to prompt
        prompt = self.json_to_prompt(subtitle_data, instructions)
        
        if progress_callback:
            progress_callback(0.3, "Sending single TTS request to Gemini...")
        
        # Step 2: Generate TTS with single request
        audio_file = self.generate_single_request_tts(prompt)
        
        if audio_file:
            if progress_callback:
                progress_callback(1.0, "Single-request TTS complete!")
            
            print(f"🎉 Single-request TTS completed successfully!")
            return audio_file
        else:
            if progress_callback:
                progress_callback(0.5, "Single request failed, falling back to individual segments...")
            
            print(f"⚠️ Single request failed, falling back to individual processing...")
            return self.fallback_to_individual_processing(subtitle_data, progress_callback)
    
    def fallback_to_individual_processing(self, subtitle_data: List[Dict], 
                                        progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Fallback to individual segment processing if single request fails."""
        
        print(f"🔄 Falling back to individual segment processing...")
        
        try:
            # Import and use the confirmed working TTS service
            from final_working_tts import FinalWorkingTTS
            
            fallback_service = FinalWorkingTTS(self.api_key, self.voice_name)
            return fallback_service.process_subtitle_json(subtitle_data, progress_callback)
            
        except Exception as e:
            print(f"❌ Fallback processing failed: {str(e)}")
            return None

# Test function
def test_single_request_tts():
    """Test the single-request TTS implementation."""
    
    print("🧪 Testing Single-Request TTS")
    print("=" * 60)
    
    # Sample subtitle data
    sample_subtitles = [
        {
            "start": 0.0,
            "end": 4.0,
            "speaker": "Luffy",
            "text": "मैं किंग ऑफ द पाइरेट्स बनूंगा!"
        },
        {
            "start": 4.0,
            "end": 7.0,
            "speaker": "Zoro", 
            "text": "मैं तुम्हारे साथ रहूंगा।"
        },
        {
            "start": 7.0,
            "end": 11.0,
            "speaker": "Nami",
            "text": "इस बार खजाना मेरा है!"
        }
    ]
    
    try:
        # Initialize service
        tts_service = SingleRequestTTS()
        
        # Progress callback
        def progress_callback(progress: float, message: str):
            print(f"[{progress*100:5.1f}%] {message}")
        
        # Test single-request processing
        final_audio = tts_service.process_subtitles_single_request(
            sample_subtitles, 
            "Speak with excitement and energy, matching the anime character personalities",
            progress_callback
        )
        
        # Validate result
        if final_audio and os.path.exists(final_audio):
            file_size = os.path.getsize(final_audio)
            duration = tts_service.get_audio_duration(final_audio)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📁 File: {final_audio}")
            print(f"📊 Size: {file_size:,} bytes")
            print(f"⏱️ Duration: {duration:.2f} seconds")
            
            # Expected duration should be around 11 seconds (0-11s range)
            if file_size > 50000 and duration > 8.0:
                print("✅ Single-request TTS appears to be working correctly!")
                
                # Show prompt that was generated
                prompt = tts_service.json_to_prompt(sample_subtitles, "Test instructions")
                print(f"\n📝 Generated prompt preview:")
                print("=" * 40)
                print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
                print("=" * 40)
                
                return True
            else:
                print("⚠️ Audio file may be too small or short")
                return False
        else:
            print(f"❌ Single-request TTS failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_single_request_tts()
    
    if success:
        print("\n🎉 Single-Request TTS is working!")
        print("🚀 Ready for integration with main dubbing pipeline!")
    else:
        print("\n❌ Single-Request TTS test failed.")
        print("🔄 Will fall back to individual segment processing.")