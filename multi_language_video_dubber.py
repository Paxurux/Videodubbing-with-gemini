#!/usr/bin/env python3
"""
Multi-Language Video Dubber
Automatically combines generated audio files with source video to create dubbed versions.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import traceback
import time

class MultiLanguageVideoDubber:
    """Creates dubbed video versions for each generated voice."""
    
    def __init__(self):
        """Initialize the video dubber."""
        self.voices_dir = Path("voices")
        self.final_dubbed_dir = Path("final_dubbed")
        self.final_dubbed_dir.mkdir(exist_ok=True)
        
        self.voice_assignments_file = "voice_assignments.json"
        
        # Video file extensions to search for
        self.video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
        
    def find_source_video(self) -> Optional[str]:
        """Find the source video file."""
        try:
            # Look for video files in current directory
            for ext in self.video_extensions:
                video_files = list(Path(".").glob(f"*{ext}"))
                if video_files:
                    # Return the first video file found
                    video_file = video_files[0]
                    print(f"✅ Found source video: {video_file}")
                    return str(video_file)
            
            # Look in common video directories
            video_dirs = ["input_video", "videos", "media"]
            for video_dir in video_dirs:
                video_path = Path(video_dir)
                if video_path.exists():
                    for ext in self.video_extensions:
                        video_files = list(video_path.glob(f"*{ext}"))
                        if video_files:
                            video_file = video_files[0]
                            print(f"✅ Found source video in {video_dir}: {video_file}")
                            return str(video_file)
            
            print("⚠️ No source video found")
            return None
            
        except Exception as e:
            print(f"❌ Error finding source video: {str(e)}")
            return None
    
    def get_video_name_from_path(self, video_path: str) -> str:
        """Extract video name from path."""
        try:
            return Path(video_path).stem
        except:
            return "demo"
    
    def get_generated_audio_files(self) -> Dict[str, str]:
        """Get all generated audio files from voices directory."""
        audio_files = {}
        
        if not self.voices_dir.exists():
            print("⚠️ Voices directory not found")
            return audio_files
        
        try:
            # Load voice assignments to map files to languages
            voice_assignments = self.load_voice_assignments()
            
            # Scan for audio files
            for audio_file in self.voices_dir.glob("*.wav"):
                filename = audio_file.stem
                
                # Try to match with voice assignments
                for lang_code, assignment in voice_assignments.items():
                    voice_name = assignment.get("voice", "")
                    if voice_name in filename:
                        audio_files[lang_code] = str(audio_file)
                        print(f"✅ Found audio for {lang_code}: {audio_file.name}")
                        break
                else:
                    # If no match found, use filename as key
                    audio_files[filename] = str(audio_file)
                    print(f"✅ Found audio file: {audio_file.name}")
            
            return audio_files
            
        except Exception as e:
            print(f"❌ Error scanning audio files: {str(e)}")
            return {}
    
    def load_voice_assignments(self) -> Dict[str, Dict[str, str]]:
        """Load voice assignments from JSON file."""
        try:
            if os.path.exists(self.voice_assignments_file):
                with open(self.voice_assignments_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Error loading voice assignments: {str(e)}")
            return {}
    
    def check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration using ffprobe."""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return None
        except Exception as e:
            print(f"⚠️ Error getting video duration: {str(e)}")
            return None
    
    def get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Get audio duration using ffprobe."""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return None
        except Exception as e:
            print(f"⚠️ Error getting audio duration: {str(e)}")
            return None
    
    def merge_audio_video(self, video_path: str, audio_path: str, output_path: str, 
                         overwrite: bool = False) -> bool:
        """Merge audio and video using ffmpeg."""
        try:
            # Check if output file exists and overwrite is disabled
            if os.path.exists(output_path) and not overwrite:
                print(f"⚠️ Output file exists, skipping: {output_path}")
                return True
            
            print(f"🎬 Merging video: {Path(video_path).name}")
            print(f"🎤 With audio: {Path(audio_path).name}")
            print(f"📁 Output: {Path(output_path).name}")
            
            # Get durations for validation
            video_duration = self.get_video_duration(video_path)
            audio_duration = self.get_audio_duration(audio_path)
            
            if video_duration and audio_duration:
                print(f"📊 Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s")
                
                # Warn if durations are very different
                duration_diff = abs(video_duration - audio_duration)
                if duration_diff > 5:  # More than 5 seconds difference
                    print(f"⚠️ Duration mismatch: {duration_diff:.2f}s difference")
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', video_path,      # Input video
                '-i', audio_path,      # Input audio
                '-c:v', 'copy',        # Copy video codec (no re-encoding)
                '-map', '0:v:0',       # Map video from first input
                '-map', '1:a:0',       # Map audio from second input
                '-shortest',           # Use shortest duration
                '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
                '-fflags', '+genpts',  # Generate presentation timestamps
                output_path
            ]
            
            # Add overwrite flag if needed
            if overwrite:
                cmd.insert(-1, '-y')
            
            # Execute ffmpeg command
            print(f"🔧 Running ffmpeg command...")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Verify output file was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✅ Successfully created: {Path(output_path).name} ({file_size:,} bytes)")
                    return True
                else:
                    print(f"❌ Output file not created: {output_path}")
                    return False
            else:
                print(f"❌ ffmpeg failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ ffmpeg timeout while processing: {output_path}")
            return False
        except Exception as e:
            print(f"❌ Error merging audio/video: {str(e)}")
            traceback.print_exc()
            return False
    
    def create_dubbed_video(self, lang_code: str, audio_path: str, video_path: str, 
                           video_name: str, voice_name: str, overwrite: bool = False) -> Optional[str]:
        """Create a dubbed video for a specific language."""
        try:
            # Create output filename with strict naming convention
            output_filename = f"{voice_name}_{video_name}.mp4"
            output_path = self.final_dubbed_dir / output_filename
            
            print(f"\\n🎯 Creating dubbed video for {lang_code}")
            print(f"   Voice: {voice_name}")
            print(f"   Output: {output_filename}")
            
            # Merge audio and video
            success = self.merge_audio_video(
                video_path, audio_path, str(output_path), overwrite
            )
            
            if success:
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error creating dubbed video for {lang_code}: {str(e)}")
            traceback.print_exc()
            return None
    
    def create_all_dubbed_videos(self, overwrite: bool = False, progress_callback=None) -> Dict[str, str]:
        """Create dubbed videos for all available audio files."""
        try:
            print("🎬 Starting multi-language video dubbing process...")
            
            # Check ffmpeg availability
            if not self.check_ffmpeg_available():
                print("❌ ffmpeg not available. Please install ffmpeg to create dubbed videos.")
                return {}
            
            # Find source video
            source_video = self.find_source_video()
            if not source_video:
                print("❌ No source video found. Please ensure a video file is available.")
                return {}
            
            # Get video name
            video_name = self.get_video_name_from_path(source_video)
            
            # Get generated audio files
            audio_files = self.get_generated_audio_files()
            if not audio_files:
                print("❌ No generated audio files found. Please generate voices first.")
                return {}
            
            # Load voice assignments for voice names
            voice_assignments = self.load_voice_assignments()
            
            print(f"📊 Processing {len(audio_files)} audio files")
            print(f"🎥 Source video: {Path(source_video).name}")
            print(f"📁 Output directory: {self.final_dubbed_dir}")
            
            dubbed_videos = {}
            successful_dubs = 0
            
            # Process each audio file
            for i, (lang_code, audio_path) in enumerate(audio_files.items()):
                if progress_callback:
                    progress = (i + 1) / len(audio_files)
                    progress_callback(progress, f"Creating dubbed video for {lang_code} ({i+1}/{len(audio_files)})")
                
                try:
                    # Get voice name from assignments or filename
                    voice_name = "unknown_voice"
                    if lang_code in voice_assignments:
                        voice_name = voice_assignments[lang_code].get("voice", lang_code)
                    else:
                        # Extract voice name from filename
                        audio_filename = Path(audio_path).stem
                        # Remove video name from filename to get voice name
                        if f"_{video_name}" in audio_filename:
                            voice_name = audio_filename.replace(f"_{video_name}", "")
                        else:
                            voice_name = audio_filename
                    
                    # Create dubbed video
                    dubbed_video_path = self.create_dubbed_video(
                        lang_code, audio_path, source_video, video_name, voice_name, overwrite
                    )
                    
                    if dubbed_video_path:
                        dubbed_videos[lang_code] = dubbed_video_path
                        successful_dubs += 1
                        print(f"✅ [{i+1}/{len(audio_files)}] {lang_code}: {Path(dubbed_video_path).name}")
                    else:
                        print(f"❌ [{i+1}/{len(audio_files)}] {lang_code}: Failed to create dubbed video")
                
                except Exception as e:
                    print(f"❌ [{i+1}/{len(audio_files)}] {lang_code}: {str(e)}")
                    continue
                
                # Small delay between processing
                time.sleep(0.1)
            
            print(f"\\n📊 Video dubbing complete!")
            print(f"✅ Successfully created: {successful_dubs}/{len(audio_files)} dubbed videos")
            print(f"📁 Videos saved in: {self.final_dubbed_dir}")
            
            return dubbed_videos
            
        except Exception as e:
            print(f"❌ Error in bulk video dubbing: {str(e)}")
            traceback.print_exc()
            return {}
    
    def recreate_dubbed_video(self, lang_code: str, overwrite: bool = True) -> Optional[str]:
        """Recreate a dubbed video for a specific language."""
        try:
            # Find source video
            source_video = self.find_source_video()
            if not source_video:
                print(f"❌ No source video found for {lang_code}")
                return None
            
            # Get audio files
            audio_files = self.get_generated_audio_files()
            if lang_code not in audio_files:
                print(f"❌ No audio file found for {lang_code}")
                return None
            
            # Get video name and voice name
            video_name = self.get_video_name_from_path(source_video)
            voice_assignments = self.load_voice_assignments()
            
            voice_name = "unknown_voice"
            if lang_code in voice_assignments:
                voice_name = voice_assignments[lang_code].get("voice", lang_code)
            
            # Create dubbed video
            audio_path = audio_files[lang_code]
            dubbed_video_path = self.create_dubbed_video(
                lang_code, audio_path, source_video, video_name, voice_name, overwrite
            )
            
            if dubbed_video_path:
                print(f"✅ Recreated dubbed video for {lang_code}: {Path(dubbed_video_path).name}")
                return dubbed_video_path
            else:
                print(f"❌ Failed to recreate dubbed video for {lang_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error recreating dubbed video for {lang_code}: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_dubbed_videos_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of created dubbed videos."""
        summary = {}
        
        if not self.final_dubbed_dir.exists():
            return summary
        
        try:
            # Load voice assignments for reference
            voice_assignments = self.load_voice_assignments()
            
            # Scan dubbed video files
            for video_file in self.final_dubbed_dir.glob("*.mp4"):
                filename = video_file.stem
                
                # Try to extract language code and voice name
                for lang_code, assignment in voice_assignments.items():
                    voice_name = assignment.get("voice", "")
                    if voice_name in filename:
                        summary[lang_code] = {
                            "file_path": str(video_file),
                            "file_size": video_file.stat().st_size,
                            "voice_name": voice_name,
                            "engine": assignment.get("engine", "unknown"),
                            "filename": video_file.name,
                            "duration": self.get_video_duration(str(video_file))
                        }
                        break
                else:
                    # If no match found, use filename
                    summary[filename] = {
                        "file_path": str(video_file),
                        "file_size": video_file.stat().st_size,
                        "voice_name": "unknown",
                        "engine": "unknown",
                        "filename": video_file.name,
                        "duration": self.get_video_duration(str(video_file))
                    }
            
            return summary
            
        except Exception as e:
            print(f"❌ Error getting dubbed videos summary: {str(e)}")
            return {}
    
    def delete_dubbed_video(self, lang_code: str) -> bool:
        """Delete a dubbed video for a specific language."""
        try:
            summary = self.get_dubbed_videos_summary()
            if lang_code not in summary:
                print(f"❌ No dubbed video found for {lang_code}")
                return False
            
            video_path = summary[lang_code]["file_path"]
            os.remove(video_path)
            print(f"✅ Deleted dubbed video for {lang_code}: {Path(video_path).name}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting dubbed video for {lang_code}: {str(e)}")
            return False

def test_multi_language_video_dubber():
    """Test the multi-language video dubber."""
    print("🧪 Testing Multi-Language Video Dubber")
    print("=" * 60)
    
    try:
        # Initialize dubber
        dubber = MultiLanguageVideoDubber()
        
        # Test ffmpeg availability
        ffmpeg_available = dubber.check_ffmpeg_available()
        print(f"ffmpeg available: {ffmpeg_available}")
        
        # Test finding source video
        source_video = dubber.find_source_video()
        if source_video:
            print(f"✅ Found source video: {source_video}")
        else:
            print("⚠️ No source video found for testing")
        
        # Test getting audio files
        audio_files = dubber.get_generated_audio_files()
        print(f"✅ Found {len(audio_files)} audio files")
        
        if audio_files:
            print("Audio files:", list(audio_files.keys()))
        
        # Test getting dubbed videos summary
        summary = dubber.get_dubbed_videos_summary()
        print(f"✅ Found {len(summary)} existing dubbed videos")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multi_language_video_dubber()
    
    if success:
        print("\\n🎉 Multi-Language Video Dubber test PASSED!")
    else:
        print("\\n❌ Multi-Language Video Dubber test FAILED!")
    
    exit(0 if success else 1)