#!/usr/bin/env python3
"""
Project Session Manager
Manages saving and loading of complete dubbing project sessions with all state data.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import glob

class ProjectSessionManager:
    """Manages project sessions for the dubbing pipeline."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions_dir = "sessions"
        self.ensure_sessions_directory()
    
    def ensure_sessions_directory(self):
        """Ensure the sessions directory exists."""
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def generate_auto_session_name(self, video_filename: str = None) -> str:
        """Generate an automatic session name based on video filename and timestamp."""
        if video_filename:
            # Extract base name without extension
            base_name = Path(video_filename).stem
            # Clean the name for use as directory name
            clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_name = clean_name.replace(' ', '_')
        else:
            clean_name = "dubbing_project"
        
        # Add timestamp to make it unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{clean_name}_{timestamp}"
    
    def get_all_sessions(self) -> List[str]:
        """Get list of all available session names."""
        try:
            if not os.path.exists(self.sessions_dir):
                return []
            
            sessions = []
            for item in os.listdir(self.sessions_dir):
                session_path = os.path.join(self.sessions_dir, item)
                if os.path.isdir(session_path):
                    # Check if it has a metadata.json file
                    metadata_path = os.path.join(session_path, "metadata.json")
                    if os.path.exists(metadata_path):
                        sessions.append(item)
            
            return sorted(sessions, reverse=True)  # Most recent first
            
        except Exception as e:
            print(f"Error getting sessions: {str(e)}")
            return []
    
    def create_session_structure(self, session_name: str) -> str:
        """Create the directory structure for a session."""
        session_path = os.path.join(self.sessions_dir, session_name)
        
        # Create main session directory
        os.makedirs(session_path, exist_ok=True)
        
        # Create subdirectories
        subdirs = [
            "transcriptions",
            "translations", 
            "voices",
            "audio",
            "final_videos",
            "custom_voices",
            "mixed_videos"
        ]
        
        for subdir in subdirs:
            os.makedirs(os.path.join(session_path, subdir), exist_ok=True)
        
        return session_path
    
    def save_session(self, session_name: str, session_data: Dict[str, Any]) -> bool:
        """Save a complete session with all data."""
        try:
            # Create session structure
            session_path = self.create_session_structure(session_name)
            
            # Add metadata
            session_data["session_name"] = session_name
            session_data["created_at"] = datetime.now().isoformat()
            session_data["last_updated"] = datetime.now().isoformat()
            
            # Save metadata.json
            metadata_path = os.path.join(session_path, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Copy files to session directories
            self.copy_session_files(session_name, session_data)
            
            print(f"✅ Session saved: {session_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving session {session_name}: {str(e)}")
            return False
    
    def copy_session_files(self, session_name: str, session_data: Dict[str, Any]):
        """Copy relevant files to the session directory."""
        session_path = os.path.join(self.sessions_dir, session_name)
        
        try:
            # Copy original video if specified
            if "original_video_path" in session_data and session_data["original_video_path"]:
                if os.path.exists(session_data["original_video_path"]):
                    video_dest = os.path.join(session_path, "original_video.mp4")
                    shutil.copy2(session_data["original_video_path"], video_dest)
            
            # Copy transcription files
            if "transcription_files" in session_data:
                for file_path in session_data["transcription_files"]:
                    if os.path.exists(file_path):
                        dest_path = os.path.join(session_path, "transcriptions", os.path.basename(file_path))
                        shutil.copy2(file_path, dest_path)
            
            # Copy audio files
            if "audio_paths" in session_data:
                for lang, audio_path in session_data["audio_paths"].items():
                    if os.path.exists(audio_path):
                        dest_path = os.path.join(session_path, "audio", f"{lang}_audio.wav")
                        shutil.copy2(audio_path, dest_path)
            
            # Copy custom voice files
            if os.path.exists("custom_voices"):
                for file in os.listdir("custom_voices"):
                    if file.endswith(('.wav', '.mp3', '.m4a')):
                        src_path = os.path.join("custom_voices", file)
                        dest_path = os.path.join(session_path, "custom_voices", file)
                        shutil.copy2(src_path, dest_path)
            
            # Copy final videos
            if "final_videos" in session_data:
                for lang, video_path in session_data["final_videos"].items():
                    if os.path.exists(video_path):
                        dest_path = os.path.join(session_path, "final_videos", f"{lang}_final.mp4")
                        shutil.copy2(video_path, dest_path)
            
            # Copy mixed videos
            if os.path.exists("final_mixed_videos"):
                for file in os.listdir("final_mixed_videos"):
                    if file.endswith('.mp4'):
                        src_path = os.path.join("final_mixed_videos", file)
                        dest_path = os.path.join(session_path, "mixed_videos", file)
                        shutil.copy2(src_path, dest_path)
                        
        except Exception as e:
            print(f"⚠️ Warning: Some files could not be copied to session: {str(e)}")
    
    def load_session(self, session_name: str) -> Optional[Dict[str, Any]]:
        """Load a session and return its data."""
        try:
            session_path = os.path.join(self.sessions_dir, session_name)
            metadata_path = os.path.join(session_path, "metadata.json")
            
            if not os.path.exists(metadata_path):
                print(f"❌ Session metadata not found: {session_name}")
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Update last accessed time
            session_data["last_accessed"] = datetime.now().isoformat()
            
            # Update file paths to point to session directory
            self.update_session_file_paths(session_name, session_data)
            
            print(f"✅ Session loaded: {session_name}")
            return session_data
            
        except Exception as e:
            print(f"❌ Error loading session {session_name}: {str(e)}")
            return None
    
    def update_session_file_paths(self, session_name: str, session_data: Dict[str, Any]):
        """Update file paths in session data to point to session directory."""
        session_path = os.path.join(self.sessions_dir, session_name)
        
        # Update original video path
        original_video = os.path.join(session_path, "original_video.mp4")
        if os.path.exists(original_video):
            session_data["original_video_path"] = original_video
        
        # Update audio paths
        if "audio_paths" in session_data:
            for lang in session_data["audio_paths"]:
                audio_file = os.path.join(session_path, "audio", f"{lang}_audio.wav")
                if os.path.exists(audio_file):
                    session_data["audio_paths"][lang] = audio_file
        
        # Update final video paths
        if "final_videos" in session_data:
            for lang in session_data["final_videos"]:
                video_file = os.path.join(session_path, "final_videos", f"{lang}_final.mp4")
                if os.path.exists(video_file):
                    session_data["final_videos"][lang] = video_file
    
    def delete_session(self, session_name: str) -> bool:
        """Delete a session and all its files."""
        try:
            session_path = os.path.join(self.sessions_dir, session_name)
            
            if os.path.exists(session_path):
                shutil.rmtree(session_path)
                print(f"✅ Session deleted: {session_name}")
                return True
            else:
                print(f"❌ Session not found: {session_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting session {session_name}: {str(e)}")
            return False
    
    def get_session_info(self, session_name: str) -> Optional[Dict[str, Any]]:
        """Get basic information about a session without loading all data."""
        try:
            session_path = os.path.join(self.sessions_dir, session_name)
            metadata_path = os.path.join(session_path, "metadata.json")
            
            if not os.path.exists(metadata_path):
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Extract basic info
            info = {
                "session_name": session_name,
                "video_name": session_data.get("video_name", "Unknown"),
                "languages": session_data.get("languages", []),
                "created_at": session_data.get("created_at", "Unknown"),
                "last_updated": session_data.get("last_updated", "Unknown"),
                "has_transcription": bool(session_data.get("transcription_text")),
                "has_translations": bool(session_data.get("translations")),
                "has_audio": bool(session_data.get("audio_paths")),
                "has_videos": bool(session_data.get("final_videos")),
                "voice_assignments": session_data.get("voices", {}),
                "file_count": self.count_session_files(session_path)
            }
            
            return info
            
        except Exception as e:
            print(f"❌ Error getting session info {session_name}: {str(e)}")
            return None
    
    def count_session_files(self, session_path: str) -> int:
        """Count the number of files in a session directory."""
        try:
            file_count = 0
            for root, dirs, files in os.walk(session_path):
                file_count += len(files)
            return file_count
        except:
            return 0
    
    def export_session(self, session_name: str, export_path: str) -> bool:
        """Export a session as a ZIP file."""
        try:
            import zipfile
            
            session_path = os.path.join(self.sessions_dir, session_name)
            
            if not os.path.exists(session_path):
                print(f"❌ Session not found: {session_name}")
                return False
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(session_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, session_path)
                        zipf.write(file_path, arcname)
            
            print(f"✅ Session exported: {export_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting session {session_name}: {str(e)}")
            return False
    
    def import_session(self, zip_path: str, session_name: str = None) -> bool:
        """Import a session from a ZIP file."""
        try:
            import zipfile
            
            if not os.path.exists(zip_path):
                print(f"❌ ZIP file not found: {zip_path}")
                return False
            
            if not session_name:
                session_name = Path(zip_path).stem
            
            session_path = os.path.join(self.sessions_dir, session_name)
            
            # Create session directory
            os.makedirs(session_path, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(session_path)
            
            print(f"✅ Session imported: {session_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error importing session: {str(e)}")
            return False

# Test the session manager
if __name__ == "__main__":
    print("🧪 Testing Project Session Manager")
    print("=" * 50)
    
    manager = ProjectSessionManager()
    
    # Test session creation
    test_session_data = {
        "video_name": "test_video.mp4",
        "languages": ["en", "hi", "es"],
        "transcription_text": "This is a test transcription.",
        "translations": {
            "hi": "यह एक परीक्षण प्रतिलेखन है।",
            "es": "Esta es una transcripción de prueba."
        },
        "voices": {
            "hi": "gemini_hi_deep",
            "es": "edge_es_bright"
        },
        "audio_paths": {
            "hi": "temp_audio/hi_audio.wav",
            "es": "temp_audio/es_audio.wav"
        }
    }
    
    # Test save session
    test_session_name = manager.generate_auto_session_name("test_video.mp4")
    success = manager.save_session(test_session_name, test_session_data)
    print(f"✅ Save session test: {success}")
    
    # Test get all sessions
    sessions = manager.get_all_sessions()
    print(f"✅ Found {len(sessions)} sessions: {sessions[:3]}")
    
    # Test session info
    if sessions:
        info = manager.get_session_info(sessions[0])
        if info:
            print(f"✅ Session info: {info['video_name']} with {len(info['languages'])} languages")
    
    print("\n🎉 Project Session Manager test complete!")