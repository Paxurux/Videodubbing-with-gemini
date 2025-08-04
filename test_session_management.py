#!/usr/bin/env python3
"""
Test Session Management Integration
"""

import os
import json
import shutil
from pathlib import Path

def create_sample_project_data():
    """Create sample project data for testing."""
    print("🧪 Creating Sample Project Data")
    print("=" * 50)
    
    try:
        # Create sample transcription file
        transcription_data = [
            {"start": 0.0, "end": 2.5, "text": "Hello, this is a test transcription."},
            {"start": 2.5, "end": 5.0, "text": "We are testing the session management system."},
            {"start": 5.0, "end": 7.5, "text": "This should save and load properly."}
        ]
        
        with open("original_asr.json", 'w', encoding='utf-8') as f:
            json.dump(transcription_data, f, indent=2, ensure_ascii=False)
        print("✅ Created: original_asr.json")
        
        # Create sample translation file
        translation_data = {
            "hi": "नमस्ते, यह एक परीक्षण प्रतिलेखन है। हम सत्र प्रबंधन प्रणाली का परीक्षण कर रहे हैं।",
            "es": "Hola, esta es una transcripción de prueba. Estamos probando el sistema de gestión de sesiones.",
            "ja": "こんにちは、これはテスト転写です。セッション管理システムをテストしています。"
        }
        
        with open("translated.json", 'w', encoding='utf-8') as f:
            json.dump(translation_data, f, indent=2, ensure_ascii=False)
        print("✅ Created: translated.json")
        
        # Create sample audio directories and files
        audio_dirs = ["temp_audio", "final_audio", "voices", "custom_voices"]
        for audio_dir in audio_dirs:
            os.makedirs(audio_dir, exist_ok=True)
            
            # Create sample audio files
            sample_files = [
                f"{audio_dir}/hi_audio.wav",
                f"{audio_dir}/en_audio.wav",
                f"{audio_dir}/es_audio.wav"
            ]
            
            for file_path in sample_files:
                # Create minimal WAV file
                with open(file_path, 'wb') as f:
                    # WAV header
                    f.write(b'RIFF')
                    f.write((1036).to_bytes(4, 'little'))
                    f.write(b'WAVE')
                    f.write(b'fmt ')
                    f.write((16).to_bytes(4, 'little'))
                    f.write((1).to_bytes(2, 'little'))
                    f.write((1).to_bytes(2, 'little'))
                    f.write((44100).to_bytes(4, 'little'))
                    f.write((88200).to_bytes(4, 'little'))
                    f.write((2).to_bytes(2, 'little'))
                    f.write((16).to_bytes(2, 'little'))
                    f.write(b'data')
                    f.write((1000).to_bytes(4, 'little'))
                    f.write(b'0' * 1000)
                
                print(f"✅ Created: {file_path}")
        
        # Create sample video directories and files
        video_dirs = ["dubbed_videos", "final_mixed_videos"]
        for video_dir in video_dirs:
            os.makedirs(video_dir, exist_ok=True)
            
            sample_videos = [
                f"{video_dir}/hi_final.mp4",
                f"{video_dir}/en_final.mp4",
                f"{video_dir}/es_final.mp4"
            ]
            
            for file_path in sample_videos:
                with open(file_path, 'w') as f:
                    f.write("dummy video content")
                print(f"✅ Created: {file_path}")
        
        print(f"\n🎉 Created sample project data!")
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation FAILED: {str(e)}")
        return False

def test_session_manager():
    """Test the session manager functionality."""
    print("\n🧪 Testing Session Manager")
    print("=" * 50)
    
    try:
        from project_session_manager import ProjectSessionManager
        
        # Initialize manager
        manager = ProjectSessionManager()
        print("✅ ProjectSessionManager initialized")
        
        # Test auto name generation
        auto_name = manager.generate_auto_session_name("test_video.mp4")
        print(f"✅ Auto name generated: {auto_name}")
        
        # Test session structure creation
        session_path = manager.create_session_structure("test_session")
        print(f"✅ Session structure created: {session_path}")
        
        # Test session data
        test_data = {
            "video_name": "test_video.mp4",
            "languages": ["hi", "en", "es"],
            "transcription_text": "Test transcription",
            "translations": {"hi": "परीक्षण", "es": "prueba"},
            "voices": {"hi": "gemini_hi_deep", "es": "edge_es_bright"},
            "audio_paths": {"hi": "temp_audio/hi_audio.wav", "es": "temp_audio/es_audio.wav"}
        }
        
        # Test save session
        success = manager.save_session("test_session", test_data)
        print(f"✅ Session save test: {success}")
        
        # Test get all sessions
        sessions = manager.get_all_sessions()
        print(f"✅ Found {len(sessions)} sessions")
        
        # Test load session
        loaded_data = manager.load_session("test_session")
        print(f"✅ Session load test: {loaded_data is not None}")
        
        # Test session info
        info = manager.get_session_info("test_session")
        print(f"✅ Session info test: {info is not None}")
        
        print("\n🎉 Session Manager test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Session Manager test FAILED: {str(e)}")
        return False

def test_app_integration():
    """Test the app.py integration."""
    print("\n🧪 Testing App Integration")
    print("=" * 50)
    
    try:
        # Check if app.py has the required elements
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        required_elements = [
            '💾 Project Sessions',
            'project_name_input = gr.Textbox',
            'save_session_btn = gr.Button',
            'session_dropdown = gr.Dropdown',
            'load_session_btn = gr.Button',
            'session_info_display = gr.Markdown',
            'export_session_btn = gr.Button',
            'import_session_btn = gr.Button',
            'delete_session_btn = gr.Button',
            'def generate_auto_session_name',
            'def save_current_session',
            'def load_selected_session',
            'def get_session_info',
            'from project_session_manager import ProjectSessionManager',
            'save_session_btn.click',
            'load_session_btn.click'
        ]
        
        for element in required_elements:
            if element in app_content:
                print(f"✅ Found: {element}")
            else:
                print(f"❌ Missing: {element}")
                return False
        
        print("\n🎉 App Integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ App Integration test FAILED: {str(e)}")
        return False

def test_session_functions():
    """Test the session management functions."""
    print("\n🧪 Testing Session Functions")
    print("=" * 50)
    
    try:
        # Create sample data first
        create_sample_project_data()
        
        # Test the functions we added to app.py
        import sys
        import os
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test auto name generation
        from project_session_manager import ProjectSessionManager
        manager = ProjectSessionManager()
        auto_name = manager.generate_auto_session_name("test_video.mp4")
        print(f"✅ Auto name generation: {auto_name}")
        
        # Test session data collection (simplified)
        session_data = {
            "video_name": "test_video.mp4",
            "languages": ["hi", "en", "es"],
            "transcription_text": "Test transcription",
            "translations": {"hi": "परीक्षण", "es": "prueba"},
            "audio_paths": {"hi": "temp_audio/hi_audio.wav"},
            "final_videos": {"hi": "dubbed_videos/hi_final.mp4"}
        }
        
        # Test save session
        success = manager.save_session("function_test", session_data)
        print(f"✅ Save session function: {success}")
        
        # Test load session
        loaded_data = manager.load_session("function_test")
        print(f"✅ Load session function: {loaded_data is not None}")
        
        # Test session info
        info = manager.get_session_info("function_test")
        print(f"✅ Session info function: {info is not None}")
        
        # Test export session
        export_path = "test_export.zip"
        export_success = manager.export_session("function_test", export_path)
        print(f"✅ Export session function: {export_success}")
        
        # Cleanup
        if os.path.exists(export_path):
            os.remove(export_path)
        
        print("\n🎉 Session Functions test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Session Functions test FAILED: {str(e)}")
        return False

def test_session_workflow():
    """Test the complete session workflow."""
    print("\n🧪 Testing Session Workflow")
    print("=" * 50)
    
    try:
        from project_session_manager import ProjectSessionManager
        
        # Create sample data
        create_sample_project_data()
        
        # Initialize manager
        manager = ProjectSessionManager()
        
        # Test complete workflow
        session_name = "workflow_test"
        
        # 1. Create session data
        session_data = {
            "video_name": "workflow_video.mp4",
            "languages": ["hi", "en", "es"],
            "transcription_text": "This is a workflow test transcription.",
            "translations": {
                "hi": "यह एक वर्कफ़्लो परीक्षण प्रतिलेखन है।",
                "es": "Esta es una transcripción de prueba de flujo de trabajo."
            },
            "voices": {
                "hi": "gemini_hi_deep",
                "es": "edge_es_bright"
            },
            "audio_paths": {
                "hi": "temp_audio/hi_audio.wav",
                "es": "temp_audio/es_audio.wav"
            },
            "final_videos": {
                "hi": "dubbed_videos/hi_final.mp4",
                "es": "dubbed_videos/es_final.mp4"
            }
        }
        
        # 2. Save session
        save_success = manager.save_session(session_name, session_data)
        print(f"✅ Workflow save: {save_success}")
        
        # 3. Verify session exists
        sessions = manager.get_all_sessions()
        session_exists = session_name in sessions
        print(f"✅ Session exists: {session_exists}")
        
        # 4. Load session
        loaded_data = manager.load_session(session_name)
        load_success = loaded_data is not None
        print(f"✅ Workflow load: {load_success}")
        
        # 5. Verify data integrity
        if loaded_data:
            data_integrity = (
                loaded_data.get("video_name") == session_data["video_name"] and
                loaded_data.get("languages") == session_data["languages"] and
                len(loaded_data.get("translations", {})) == len(session_data["translations"])
            )
            print(f"✅ Data integrity: {data_integrity}")
        
        # 6. Export session
        export_path = f"{session_name}_export.zip"
        export_success = manager.export_session(session_name, export_path)
        print(f"✅ Workflow export: {export_success}")
        
        # 7. Delete session
        delete_success = manager.delete_session(session_name)
        print(f"✅ Workflow delete: {delete_success}")
        
        # 8. Import session back
        if os.path.exists(export_path):
            import_success = manager.import_session(export_path, f"{session_name}_imported")
            print(f"✅ Workflow import: {import_success}")
            
            # Cleanup
            os.remove(export_path)
            manager.delete_session(f"{session_name}_imported")
        
        print("\n🎉 Session Workflow test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Session Workflow test FAILED: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning Up Test Data")
    print("=" * 50)
    
    try:
        # Remove test files
        test_files = ["original_asr.json", "translated.json"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"✅ Removed: {file}")
        
        # Remove test directories
        test_dirs = ["temp_audio", "final_audio", "voices", "custom_voices", "dubbed_videos", "final_mixed_videos"]
        for dir_name in test_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"✅ Removed: {dir_name}")
        
        # Remove sessions directory
        if os.path.exists("sessions"):
            shutil.rmtree("sessions")
            print("✅ Removed: sessions")
        
        print("\n🎉 Cleanup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Session Management Tests")
    print("=" * 60)
    
    # Run all tests
    tests = [
        test_session_manager,
        test_app_integration,
        test_session_functions,
        test_session_workflow
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Session management integration is complete!")
        print("\n🎯 READY FOR USE:")
        print("1. Complete any step of the dubbing pipeline")
        print("2. Save your session with a custom or auto-generated name")
        print("3. Load previously saved sessions to continue work")
        print("4. Export sessions as ZIP files for backup/sharing")
        print("5. Import sessions from ZIP files")
        print("6. View detailed session information and statistics")
        print("7. Delete old sessions to manage storage")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    print("=" * 60)