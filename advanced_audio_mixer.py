#!/usr/bin/env python3
"""
Advanced Audio Mixer
Handles professional audio mixing including original audio, background music, and volume controls.
"""

import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import shutil

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
    from moviepy.audio.fx import volumex
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not available, using FFmpeg for audio mixing")

class AdvancedAudioMixer:
    """Professional audio mixing service for dubbed videos."""
    
    def __init__(self):
        """Initialize the audio mixer."""
        self.temp_dir = "temp_audio_mixing"
        self.output_dir = "final_mixed_videos"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_original_audio(self, video_path: str) -> Optional[str]:
        """Extract original audio from video file."""
        try:
            if not os.path.exists(video_path):
                print(f"Video file not found: {video_path}")
                return None
            
            # Create temporary file for extracted audio
            temp_audio = os.path.join(self.temp_dir, "original_audio.wav")
            
            if MOVIEPY_AVAILABLE:
                # Use MoviePy to extract audio
                video = VideoFileClip(video_path)
                if video.audio is not None:
                    video.audio.write_audiofile(temp_audio, verbose=False, logger=None)
                    video.close()
                    return temp_audio
                else:
                    print("No audio track found in video")
                    video.close()
                    return None
            else:
                # Use FFmpeg to extract audio
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-vn",  # No video
                    "-acodec", "pcm_s16le",  # PCM 16-bit
                    "-ar", "44100",  # Sample rate
                    "-ac", "2",  # Stereo
                    "-y",  # Overwrite
                    temp_audio
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(temp_audio):
                    return temp_audio
                else:
                    print(f"FFmpeg audio extraction failed: {result.stderr}")
                    return None
                    
        except Exception as e:
            print(f"Error extracting original audio: {str(e)}")
            return None
    
    def prepare_background_music(self, music_path: str, target_duration: float) -> Optional[str]:
        """Prepare background music to match target duration."""
        try:
            if not os.path.exists(music_path):
                print(f"Music file not found: {music_path}")
                return None
            
            temp_music = os.path.join(self.temp_dir, "background_music.wav")
            
            if MOVIEPY_AVAILABLE:
                # Use MoviePy to process music
                music = AudioFileClip(music_path)
                
                if music.duration < target_duration:
                    # Loop music to match duration
                    loops_needed = int(target_duration / music.duration) + 1
                    music_clips = [music] * loops_needed
                    music = concatenate_audioclips(music_clips)
                
                # Trim to exact duration
                music = music.subclip(0, target_duration)
                
                # Add fade in/out
                music = music.fadein(1.0).fadeout(1.0)
                
                music.write_audiofile(temp_music, verbose=False, logger=None)
                music.close()
                
                return temp_music
            else:
                # Use FFmpeg to process music
                cmd = [
                    "ffmpeg",
                    "-stream_loop", "-1",  # Loop indefinitely
                    "-i", music_path,
                    "-t", str(target_duration),  # Duration
                    "-af", "afade=in:st=0:d=1,afade=out:st={}:d=1".format(target_duration - 1),  # Fade in/out
                    "-y",
                    temp_music
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(temp_music):
                    return temp_music
                else:
                    print(f"FFmpeg music processing failed: {result.stderr}")
                    return None
                    
        except Exception as e:
            print(f"Error preparing background music: {str(e)}")
            return None
    
    def mix_audio_tracks(self, voice_audio: str, original_audio: Optional[str] = None, 
                        background_music: Optional[str] = None, voice_volume: float = 1.0,
                        music_volume: float = 0.3, original_volume: float = 0.4) -> Optional[str]:
        """Mix multiple audio tracks with volume controls."""
        try:
            if not os.path.exists(voice_audio):
                print(f"Voice audio not found: {voice_audio}")
                return None
            
            mixed_audio = os.path.join(self.temp_dir, "mixed_audio.wav")
            
            if MOVIEPY_AVAILABLE:
                # Use MoviePy for mixing
                audio_clips = []
                
                # Add voice audio (primary)
                voice = AudioFileClip(voice_audio)
                if voice_volume != 1.0:
                    voice = voice.fx(volumex, voice_volume)
                audio_clips.append(voice)
                
                # Add original audio if requested
                if original_audio and os.path.exists(original_audio):
                    original = AudioFileClip(original_audio)
                    if original_volume != 1.0:
                        original = original.fx(volumex, original_volume)
                    # Match duration to voice
                    if original.duration > voice.duration:
                        original = original.subclip(0, voice.duration)
                    elif original.duration < voice.duration:
                        # Loop original audio if needed
                        loops = int(voice.duration / original.duration) + 1
                        original_clips = [original] * loops
                        original = concatenate_audioclips(original_clips).subclip(0, voice.duration)
                    audio_clips.append(original)
                
                # Add background music if provided
                if background_music and os.path.exists(background_music):
                    music = AudioFileClip(background_music)
                    if music_volume != 1.0:
                        music = music.fx(volumex, music_volume)
                    # Match duration to voice
                    if music.duration > voice.duration:
                        music = music.subclip(0, voice.duration)
                    audio_clips.append(music)
                
                # Composite all audio clips
                if len(audio_clips) > 1:
                    final_audio = CompositeAudioClip(audio_clips)
                else:
                    final_audio = audio_clips[0]
                
                final_audio.write_audiofile(mixed_audio, verbose=False, logger=None)
                
                # Close all clips
                for clip in audio_clips:
                    clip.close()
                final_audio.close()
                
                return mixed_audio
            else:
                # Use FFmpeg for mixing
                inputs = ["-i", voice_audio]
                filter_complex = f"[0:a]volume={voice_volume}[voice]"
                mix_inputs = "[voice]"
                
                input_count = 1
                
                # Add original audio
                if original_audio and os.path.exists(original_audio):
                    inputs.extend(["-i", original_audio])
                    filter_complex += f";[{input_count}:a]volume={original_volume}[orig]"
                    mix_inputs += "[orig]"
                    input_count += 1
                
                # Add background music
                if background_music and os.path.exists(background_music):
                    inputs.extend(["-i", background_music])
                    filter_complex += f";[{input_count}:a]volume={music_volume}[music]"
                    mix_inputs += "[music]"
                    input_count += 1
                
                # Create mix command
                if input_count > 1:
                    filter_complex += f";{mix_inputs}amix=inputs={input_count}:duration=first[out]"
                    map_output = "[out]"
                else:
                    map_output = "[voice]"
                
                cmd = [
                    "ffmpeg"
                ] + inputs + [
                    "-filter_complex", filter_complex,
                    "-map", map_output,
                    "-y",
                    mixed_audio
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(mixed_audio):
                    return mixed_audio
                else:
                    print(f"FFmpeg audio mixing failed: {result.stderr}")
                    return None
                    
        except Exception as e:
            print(f"Error mixing audio tracks: {str(e)}")
            return None
    
    def create_mixed_video(self, original_video: str, mixed_audio: str, output_path: str) -> bool:
        """Create final video with mixed audio."""
        try:
            if not os.path.exists(original_video) or not os.path.exists(mixed_audio):
                print(f"Missing files: video={os.path.exists(original_video)}, audio={os.path.exists(mixed_audio)}")
                return False
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if MOVIEPY_AVAILABLE:
                # Use MoviePy
                video = VideoFileClip(original_video)
                audio = AudioFileClip(mixed_audio)
                
                # Set audio to video
                final_video = video.set_audio(audio)
                
                final_video.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile="temp_mixed_audio.m4a",
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                
                # Clean up
                video.close()
                audio.close()
                final_video.close()
                
                return True
            else:
                # Use FFmpeg
                cmd = [
                    "ffmpeg",
                    "-i", original_video,  # Input video
                    "-i", mixed_audio,     # Input audio
                    "-c:v", "copy",        # Copy video stream
                    "-c:a", "aac",         # Encode audio as AAC
                    "-map", "0:v:0",       # Map video from first input
                    "-map", "1:a:0",       # Map audio from second input
                    "-shortest",           # End when shortest stream ends
                    "-y",                  # Overwrite output file
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                return result.returncode == 0
                
        except Exception as e:
            print(f"Error creating mixed video: {str(e)}")
            return False
    
    def process_all_videos_with_mixing(self, original_video: str, dubbed_videos: List[Dict[str, str]],
                                     use_original_audio: bool = False, background_music: Optional[str] = None,
                                     voice_volume: float = 1.0, music_volume: float = 0.3,
                                     original_volume: float = 0.4, progress_callback=None) -> List[Dict[str, str]]:
        """Process all dubbed videos with advanced audio mixing."""
        if not dubbed_videos:
            return []
        
        mixed_videos = []
        
        # Extract original audio if needed
        original_audio_path = None
        if use_original_audio:
            original_audio_path = self.extract_original_audio(original_video)
            if not original_audio_path:
                print("⚠️ Could not extract original audio, proceeding without it")
        
        # Get video duration for music preparation
        video_duration = self.get_video_duration(original_video)
        
        # Prepare background music if provided
        prepared_music = None
        if background_music and os.path.exists(background_music) and video_duration > 0:
            prepared_music = self.prepare_background_music(background_music, video_duration)
            if not prepared_music:
                print("⚠️ Could not prepare background music, proceeding without it")
        
        total_videos = len(dubbed_videos)
        
        for i, video_info in enumerate(dubbed_videos):
            if progress_callback:
                progress = (i + 1) / total_videos
                progress_callback(progress, f"Mixing audio for {video_info['display_name']} ({i+1}/{total_videos})")
            
            try:
                # Find the corresponding audio file
                voice_audio = self.find_voice_audio_for_video(video_info)
                
                if not voice_audio:
                    print(f"⚠️ No voice audio found for {video_info['display_name']}")
                    continue
                
                # Mix audio tracks
                mixed_audio = self.mix_audio_tracks(
                    voice_audio=voice_audio,
                    original_audio=original_audio_path,
                    background_music=prepared_music,
                    voice_volume=voice_volume,
                    music_volume=music_volume,
                    original_volume=original_volume
                )
                
                if not mixed_audio:
                    print(f"⚠️ Audio mixing failed for {video_info['display_name']}")
                    continue
                
                # Create output filename
                base_name = Path(video_info['file_path']).stem
                output_filename = f"{base_name}_mixed.mp4"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # Create final video with mixed audio
                success = self.create_mixed_video(original_video, mixed_audio, output_path)
                
                if success and os.path.exists(output_path):
                    mixed_videos.append({
                        "file_path": output_path,
                        "voice_id": video_info['voice_id'],
                        "display_name": f"{video_info['display_name']} (Mixed)",
                        "engine": video_info['engine'],
                        "language": video_info['language'],
                        "original_video": video_info['file_path'],
                        "has_original_audio": use_original_audio,
                        "has_background_music": background_music is not None,
                        "voice_volume": voice_volume,
                        "music_volume": music_volume,
                        "original_volume": original_volume
                    })
                    print(f"✅ Created mixed video: {output_filename}")
                else:
                    print(f"❌ Failed to create mixed video for {video_info['display_name']}")
                    
            except Exception as e:
                print(f"❌ Error processing {video_info['display_name']}: {str(e)}")
                continue
        
        return mixed_videos
    
    def find_voice_audio_for_video(self, video_info: Dict[str, str]) -> Optional[str]:
        """Find the corresponding voice audio file for a video."""
        # Search patterns for audio files
        search_patterns = [
            f"temp_audio/combined_{video_info['engine']}_tts.wav",
            f"final_audio/{video_info['engine']}_tts_video_ready.wav",
            f"voices/{video_info['voice_id']}_*.wav",
            f"custom_voices/{video_info['voice_id']}_*.wav"
        ]
        
        for pattern in search_patterns:
            import glob
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        
        # Fallback: look for any audio file with the voice_id
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(('.wav', '.mp3', '.m4a')) and video_info['voice_id'] in file:
                    return os.path.join(root, file)
        
        return None
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            if MOVIEPY_AVAILABLE:
                video = VideoFileClip(video_path)
                duration = video.duration
                video.close()
                return duration
            else:
                # Use FFprobe
                cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    video_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    import json
                    info = json.loads(result.stdout)
                    return float(info.get("format", {}).get("duration", 0))
                
        except Exception as e:
            print(f"Error getting video duration: {str(e)}")
        
        return 0.0
    
    def create_export_zip(self, videos: List[Dict[str, str]], zip_name: str = "final_export.zip") -> Optional[str]:
        """Create a ZIP file containing all final videos."""
        try:
            zip_path = os.path.join(self.output_dir, zip_name)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for video in videos:
                    if os.path.exists(video['file_path']):
                        # Add video to zip with just the filename
                        arcname = os.path.basename(video['file_path'])
                        zipf.write(video['file_path'], arcname)
                        
                        # Add a text file with video info
                        info_text = f"""Video: {arcname}
Display Name: {video['display_name']}
Voice ID: {video['voice_id']}
Engine: {video['engine']}
Language: {video['language']}
Has Original Audio: {video.get('has_original_audio', False)}
Has Background Music: {video.get('has_background_music', False)}
Voice Volume: {video.get('voice_volume', 1.0)}
Music Volume: {video.get('music_volume', 0.3)}
Original Volume: {video.get('original_volume', 0.4)}
"""
                        info_filename = f"{Path(arcname).stem}_info.txt"
                        zipf.writestr(info_filename, info_text)
            
            if os.path.exists(zip_path):
                print(f"✅ Created export ZIP: {zip_path}")
                return zip_path
            else:
                print("❌ Failed to create export ZIP")
                return None
                
        except Exception as e:
            print(f"❌ Error creating export ZIP: {str(e)}")
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir, exist_ok=True)
                print("✅ Cleaned up temporary files")
        except Exception as e:
            print(f"⚠️ Error cleaning up temp files: {str(e)}")

# Test the mixer
if __name__ == "__main__":
    print("🧪 Testing Advanced Audio Mixer")
    print("=" * 50)
    
    mixer = AdvancedAudioMixer()
    
    # Test directory creation
    mixer.ensure_directories()
    print(f"✅ Directories created: {mixer.temp_dir}, {mixer.output_dir}")
    
    # Test video duration (will fail gracefully without actual video)
    duration = mixer.get_video_duration("nonexistent.mp4")
    print(f"✅ Video duration function works (returned {duration})")
    
    print("\n🎉 Advanced Audio Mixer test complete!")