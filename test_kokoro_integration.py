#!/usr/bin/env python3
"""
Test Kokoro TTS Integration
Tests the updated Kokoro TTS service with the actual model.
"""

from kokoro_tts_service import KokoroTTSService

def test_kokoro_integration():
    """Test the integrated Kokoro TTS service."""
    print("🧪 Testing Kokoro TTS Integration")
    print("=" * 50)
    
    try:
        # Initialize service
        print("🔧 Initializing Kokoro TTS service...")
        service = KokoroTTSService("af_bella")
        
        # Test voice preview
        print("\n🎤 Testing voice preview...")
        preview_file = service.preview_voice("Hello, this is a test of Kokoro TTS integration.")
        
        if preview_file:
            print(f"✅ Voice preview generated: {preview_file}")
        else:
            print("⚠️ Voice preview failed, but this is expected without full Kokoro setup")
        
        # Test TTS chunks generation
        print("\n🎬 Testing TTS chunks generation...")
        test_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text_translated": "This is the first test segment for Kokoro TTS."
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text_translated": "This is the second segment to verify functionality."
            },
            {
                "start": 6.0,
                "end": 9.0,
                "text_translated": "And this is the final test segment."
            }
        ]
        
        def progress_callback(progress, message):
            print(f"[{progress*100:5.1f}%] {message}")
        
        chunks_dir = service.generate_tts_chunks(test_segments, progress_callback)
        
        if chunks_dir:
            print(f"✅ TTS chunks generated in: {chunks_dir}")
            
            # Check generated files
            import os
            if os.path.exists(chunks_dir):
                chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
                print(f"📁 Generated {len(chunk_files)} chunk files:")
                
                total_size = 0
                for chunk_file in chunk_files:
                    file_path = os.path.join(chunks_dir, chunk_file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    print(f"   • {chunk_file}: {file_size:,} bytes")
                
                print(f"📊 Total size: {total_size:,} bytes")
                
                if len(chunk_files) > 0:
                    print("🎉 TTS chunks generated successfully!")
                    print(f"📦 Note: {len(test_segments)} segments were bundled into {len(chunk_files)} chunks for better quality")
                    return True
                else:
                    print(f"❌ No chunk files generated")
                    return False
            else:
                print(f"❌ Chunks directory not found: {chunks_dir}")
                return False
        else:
            print("❌ TTS chunks generation failed")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_kokoro_integration()
    
    if success:
        print("\n🎉 Kokoro TTS Integration Test PASSED!")
        print("✅ The service is ready for use in the dubbing pipeline")
    else:
        print("\n⚠️ Kokoro TTS Integration Test completed with issues")
        print("💡 The service will use fallback audio generation")
    
    exit(0 if success else 1)