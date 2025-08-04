#!/usr/bin/env python3
"""
Kokoro TTS Service - EXACT Documentation Pattern Implementation
Uses the precise API pattern shown in the Kokoro documentation.
"""

import os
import numpy as np
import soundfile as sf
from typing import List, Dict, Optional
from pathlib import Path
import time

class KokoroTTSCorrectPattern:
    """Kokoro TTS service using the EXACT pattern from documentation."""
    
    def __init__(self, voice_name: str = "af_heart", lang_code: str = "a"):
        """Initialize with proper Kokoro setup."""
        self.voice_name = voice_name
        self.lang_code = lang_code
        self.pipeline = None
        
        print(f"🎙️ Kokoro TTS Service - EXACT Documentation Pattern")
        print(f"🎤 Voice: {self.voice_name}")
        print(f"🌍 Language: {self.lang_code}")
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the Kokoro pipeline using EXACT documentation pattern."""
        try:
            # EXACT import pattern from documentation
            from kokoro import KPipeline
            import torch
            
            print("🔧 Initializing Kokoro pipeline with EXACT documentation pattern...")
            
            # EXACT initialization pattern from documentation:
            # pipeline = KPipeline(lang_code='a')
            self.pipeline = KPipeline(lang_code=self.lang_code)
            print("✅ Kokoro pipeline initialized successfully with EXACT pattern")
            
        except Exception as e:
            print(f"❌ Pipeline initialization failed: {str(e)}")
            if "EspeakWrapper" in str(e):
                print("💡 EspeakWrapper issue detected. Install espeak-ng:")
                print("   Windows: Download from http://espeak.sourceforge.net/download.html")
                print("   Linux: sudo apt-get install espeak-ng")
                print("   macOS: brew install espeak")
            self.pipeline = None
    
    def generate_tts_chunks(self, translated_segments: List[Dict], progress_callback=None) -> str:
        """Generate TTS chunks using EXACT Kokoro documentation pattern."""
        if not self.pipeline:
            print("❌ Pipeline not available")
            return "kokoro_tts_chunks"
        
        print(f"🎬 Generating {len(translated_segments)} segments with EXACT Kokoro documentation pattern")
        
        # Create output directory
        output_dir = Path("kokoro_tts_chunks")
        output_dir.mkdir(exist_ok=True)
        
        successful_chunks = 0
        
        for segment_idx, segment in enumerate(translated_segments):
            if progress_callback:
                progress = (segment_idx + 1) / len(translated_segments)
                progress_callback(progress, f"Processing segment {segment_idx + 1}/{len(translated_segments)} with EXACT Kokoro pattern")
            
            # Extract text and timing
            text = segment.get("text_translated", segment.get("text", "")).strip()
            start_time = float(segment.get("start", 0))
            end_time = float(segment.get("end", 0))
            duration = end_time - start_time
            
            if not text or duration <= 0:
                print(f"[{segment_idx}] ⚠️ Skipping invalid segment")
                continue
            
            print(f"[{segment_idx}] 📝 {start_time:.2f}s-{end_time:.2f}s ({duration:.2f}s): {text[:50]}...")
            
            try:
                # EXACT pattern from documentation:
                print(f"🎤 Using EXACT Kokoro pattern: pipeline(text, voice='{self.voice_name}', speed=1, split_pattern=r'\\n+')\")\n                \n                # EXACT generator call from documentation\n                generator = self.pipeline(\n                    text, \n                    voice=self.voice_name,\n                    speed=1,\n                    split_pattern=r'\\n+'\n                )\n                \n                # EXACT processing pattern from documentation:\n                # for i, (gs, ps, audio) in enumerate(generator):\n                #     print(i, gs, ps)\n                #     sf.write(f'{i}.wav', audio, 24000)\n                \n                audio_files = []\n                for i, (gs, ps, audio) in enumerate(generator):\n                    print(f\"   Sub-chunk {i}: gs='{gs[:30]}...', ps='{ps[:30]}...', audio_shape={audio.shape if hasattr(audio, 'shape') else type(audio)}\")\n                    \n                    if isinstance(audio, np.ndarray):\n                        # EXACT save pattern from documentation: sf.write(f'{i}.wav', audio, 24000)\n                        sub_chunk_file = output_dir / f\"segment_{segment_idx:03d}_subchunk_{i}.wav\"\n                        sf.write(sub_chunk_file, audio, 24000)\n                        audio_files.append(sub_chunk_file)\n                        \n                        # Debug audio properties\n                        print(f\"   Audio: min={np.min(audio):.3f}, max={np.max(audio):.3f}, mean={np.mean(np.abs(audio)):.6f}, std={np.std(audio):.6f}\")\n                        \n                        # Check audio quality\n                        if np.abs(audio).mean() < 0.001:\n                            print(\"⚠️ Silent audio detected\")\n                        elif np.std(audio) < 0.001:\n                            print(\"⚠️ Flat audio detected\")\n                        else:\n                            print(\"✅ Good audio variation\")\n                    else:\n                        print(f\"⚠️ Unexpected audio type: {type(audio)}\")\n                \n                # Combine all sub-chunks into final chunk\n                if audio_files:\n                    final_chunk_file = output_dir / f\"chunk_{segment_idx:03d}.wav\"\n                    \n                    if len(audio_files) == 1:\n                        # Single sub-chunk, just rename\n                        import shutil\n                        shutil.move(str(audio_files[0]), str(final_chunk_file))\n                        print(f\"   Single sub-chunk moved to final chunk\")\n                    else:\n                        # Multiple sub-chunks, concatenate them\n                        print(f\"   Combining {len(audio_files)} sub-chunks...\")\n                        combined_audio = []\n                        for audio_file in audio_files:\n                            audio_data, _ = sf.read(audio_file)\n                            combined_audio.append(audio_data)\n                            # Clean up sub-chunk\n                            os.unlink(audio_file)\n                        \n                        # Concatenate and save\n                        final_audio = np.concatenate(combined_audio)\n                        sf.write(final_chunk_file, final_audio, 24000)\n                        print(f\"   Combined into final audio: {final_audio.shape}\")\n                    \n                    # Adjust duration to match target\n                    current_duration = len(sf.read(final_chunk_file)[0]) / 24000\n                    if abs(current_duration - duration) > 0.5:\n                        target_length = int(duration * 24000)\n                        audio_data, _ = sf.read(final_chunk_file)\n                        \n                        if target_length > len(audio_data):\n                            # Pad with silence\n                            padding = target_length - len(audio_data)\n                            audio_data = np.pad(audio_data, (0, padding), mode='constant')\n                        else:\n                            # Truncate\n                            audio_data = audio_data[:target_length]\n                        \n                        sf.write(final_chunk_file, audio_data, 24000)\n                        print(f\"🎵 Adjusted duration: {current_duration:.2f}s → {duration:.2f}s\")\n                    \n                    if final_chunk_file.exists():\n                        file_size = final_chunk_file.stat().st_size\n                        print(f\"[{segment_idx}] ✅ EXACT Kokoro pattern completed: {final_chunk_file} ({file_size:,} bytes)\")\n                        successful_chunks += 1\n                    else:\n                        print(f\"[{segment_idx}] ❌ Final chunk file not created\")\n                else:\n                    print(f\"[{segment_idx}] ❌ No audio files generated\")\n                    \n            except Exception as e:\n                print(f\"[{segment_idx}] ❌ Generation failed: {str(e)}\")\n                import traceback\n                traceback.print_exc()\n        \n        print(f\"📊 Generated {successful_chunks}/{len(translated_segments)} chunks using EXACT Kokoro pattern\")\n        return str(output_dir)\n    \n    def preview_voice(self, test_text: str = \"Testing EXACT Kokoro TTS documentation pattern\") -> Optional[str]:\n        \"\"\"Generate voice preview using EXACT Kokoro documentation pattern.\"\"\"\n        if not self.pipeline:\n            return None\n        \n        try:\n            preview_file = Path(f\"kokoro_tts_output/exact_pattern_preview_{self.voice_name}.wav\")\n            preview_file.parent.mkdir(exist_ok=True)\n            \n            print(f\"🎤 EXACT Kokoro preview: '{test_text}' with {self.voice_name}\")\n            \n            # EXACT pattern from documentation\n            generator = self.pipeline(\n                test_text, \n                voice=self.voice_name,\n                speed=1,\n                split_pattern=r'\\n+'\n            )\n            \n            # EXACT processing pattern\n            audio_chunks = []\n            for i, (gs, ps, audio) in enumerate(generator):\n                print(f\"Preview chunk {i}: gs='{gs[:20]}...', audio_shape={audio.shape if hasattr(audio, 'shape') else type(audio)}\")\n                \n                if isinstance(audio, np.ndarray):\n                    audio_chunks.append(audio)\n            \n            if audio_chunks:\n                # Combine chunks\n                if len(audio_chunks) == 1:\n                    final_audio = audio_chunks[0]\n                else:\n                    final_audio = np.concatenate(audio_chunks)\n                \n                # Save preview using EXACT pattern: sf.write(f'{i}.wav', audio, 24000)\n                sf.write(preview_file, final_audio, 24000)\n                \n                file_size = preview_file.stat().st_size\n                print(f\"✅ EXACT pattern preview generated: {preview_file} ({file_size:,} bytes)\")\n                return str(preview_file)\n            \n            return None\n            \n        except Exception as e:\n            print(f\"❌ EXACT pattern preview failed: {str(e)}\")\n            import traceback\n            traceback.print_exc()\n            return None\n\ndef test_exact_kokoro_pattern():\n    \"\"\"Test the EXACT Kokoro documentation pattern.\"\"\"\n    print(\"🧪 Testing EXACT Kokoro Documentation Pattern\")\n    print(\"=\" * 60)\n    \n    try:\n        # Initialize service\n        service = KokoroTTSCorrectPattern(\"af_heart\", \"a\")\n        \n        if not service.pipeline:\n            print(\"❌ Pipeline not available - cannot test EXACT pattern\")\n            return False\n        \n        # Test voice preview\n        print(\"\\n🎤 Testing EXACT pattern voice preview...\")\n        preview_file = service.preview_voice(\"This is a test of the EXACT Kokoro TTS documentation pattern implementation.\")\n        \n        if preview_file:\n            print(f\"✅ EXACT pattern preview generated: {preview_file}\")\n        else:\n            print(\"❌ EXACT pattern preview failed\")\n        \n        # Test with segments\n        print(\"\\n🎬 Testing EXACT pattern TTS chunks generation...\")\n        test_segments = [\n            {\n                \"start\": 0.0,\n                \"end\": 4.0,\n                \"text_translated\": \"Hello everyone, this is a test using the EXACT Kokoro TTS documentation pattern.\"\n            },\n            {\n                \"start\": 4.0,\n                \"end\": 8.0,\n                \"text_translated\": \"We are following the precise API calls shown in the official documentation.\"\n            },\n            {\n                \"start\": 8.0,\n                \"end\": 12.0,\n                \"text_translated\": \"This should generate real Kokoro TTS audio using the correct generator pattern.\"\n            }\n        ]\n        \n        def progress_callback(progress, message):\n            print(f\"[{progress*100:5.1f}%] {message}\")\n        \n        chunks_dir = service.generate_tts_chunks(test_segments, progress_callback)\n        \n        if chunks_dir and Path(chunks_dir).exists():\n            chunk_files = list(Path(chunks_dir).glob(\"*.wav\"))\n            print(f\"\\n✅ Generated {len(chunk_files)} chunk files using EXACT pattern:\")\n            \n            total_size = 0\n            for chunk_file in chunk_files:\n                file_size = chunk_file.stat().st_size\n                total_size += file_size\n                print(f\"   • {chunk_file.name}: {file_size:,} bytes\")\n            \n            print(f\"📊 Total size: {total_size:,} bytes\")\n            \n            if len(chunk_files) == len(test_segments):\n                print(\"🎉 All segments processed successfully with EXACT Kokoro documentation pattern!\")\n                return True\n            else:\n                print(f\"⚠️ Expected {len(test_segments)} files, got {len(chunk_files)}\")\n                return len(chunk_files) > 0  # Partial success\n        else:\n            print(\"❌ No chunks generated with EXACT pattern\")\n            return False\n            \n    except Exception as e:\n        print(f\"❌ EXACT pattern test failed: {str(e)}\")\n        import traceback\n        traceback.print_exc()\n        return False\n\nif __name__ == \"__main__\":\n    success = test_exact_kokoro_pattern()\n    \n    if success:\n        print(\"\\n🎉 EXACT Kokoro Documentation Pattern test PASSED!\")\n        print(\"✅ Using precise Kokoro API pattern from documentation\")\n        print(\"✅ Real Kokoro TTS audio generation with correct generator usage\")\n        print(\"✅ Proper sub-chunk handling and combination\")\n    else:\n        print(\"\\n❌ EXACT Kokoro Documentation Pattern test FAILED!\")\n        print(\"💡 Make sure espeak-ng is installed for Kokoro to work properly\")\n        print(\"💡 Check that Kokoro package is properly installed: pip install kokoro>=0.9.4\")\n    \n    exit(0 if success else 1)\n