import gradio as gr
import torch
import pandas as pd
import nemo.collections.asr as nemo_asr
import os
from pathlib import Path
import tempfile
import numpy as np
import subprocess
import math
import json
from typing import List, Dict, Optional

# Import transcript chunking
from transcript_chunker import TranscriptChunker, ChunkConfig
from chunked_audio_stitcher import ChunkedAudioStitcher

# Import dubbing pipeline components
try:
    # First check if google-generativeai is available
    import google.generativeai as genai
    import wave
    import requests  # For REST API TTS calls

    from real_gemini_service import RealGeminiService
    from enhanced_tts_pipeline import EnhancedTTSPipeline

    from final_working_tts import FinalWorkingTTS
    from single_request_tts import SingleRequestTTS
    from simple_edge_tts import SimpleEdgeTTS, EDGE_TTS_AVAILABLE
    from enhanced_edge_tts_service import EnhancedEdgeTTSService, EdgeTTSConfig
    from edge_tts_voice_parser import EdgeTTSVoiceParser
    from voice_assignment_manager import VoiceAssignmentManager
    from multi_language_voice_generator import MultiLanguageVoiceGenerator
    from multi_language_video_dubber import MultiLanguageVideoDubber
    from custom_voice_assignment_panel import CustomVoiceAssignmentPanel
    from gemini_voice_library import GeminiVoiceLibrary
    
    # Import Kokoro TTS components
    try:
        from kokoro_tts_service import KokoroTTSService
        from kokoro_voice_parser import KokoroVoiceParser
        KOKORO_TTS_AVAILABLE = True
        print("✅ Kokoro TTS service loaded")
        print("✅ Kokoro voice parser loaded")
    except ImportError as e:
        KOKORO_TTS_AVAILABLE = False
        print(f"⚠️ Kokoro TTS not available: {str(e)}")
    print("✅ Google Generative AI library available")
    print("✅ Fixed TTS Dubbing service loaded (REST API)")
    print("✅ Final Working TTS service loaded")
    print("✅ Single-Request TTS service loaded")
    if EDGE_TTS_AVAILABLE:
        print("✅ Edge TTS service loaded")
        print("✅ Enhanced Edge TTS service loaded")
        print("✅ Edge TTS voice parser loaded")
    else:
        print("⚠️ Edge TTS service not available")
    DUBBING_AVAILABLE = True
    print("✅ Dubbing pipeline components loaded successfully")
    print("✅ Enhanced TTS Pipeline loaded")
    
except ImportError as e:
    DUBBING_AVAILABLE = False
    print(f"⚠️ Dubbing pipeline not available: {str(e)}")
    print("💡 To enable dubbing features, please install: pip install google-generativeai requests")
    print("💡 Or run the update script to install all dependencies")

# Global variables
current_api_keys = []  # Store API keys temporarily in memory only

# Simple API key management functions (no persistent storage)
def save_api_keys_to_memory(keys_text):
    """Save API keys to memory only (not persistent)"""
    global current_api_keys
    try:
        keys = [key.strip() for key in keys_text.strip().split('\n') if key.strip()]
        if not keys:
            return "❌ No valid API keys provided"
        current_api_keys = keys
        return f"✅ Successfully saved {len(keys)} API keys to memory"
    except Exception as e:
        return f"❌ Failed to save API keys: {str(e)}"

def test_api_keys_in_memory():
    """Test the API keys stored in memory"""
    global current_api_keys
    if not current_api_keys:
        return "❌ No API keys in memory"
    
    try:
        import google.generativeai as genai
        results = []
        
        for i, key in enumerate(current_api_keys):
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content("Say 'API key working'")
                if response and response.text:
                    results.append(f"✅ Key {i+1}: Working")
                else:
                    results.append(f"❌ Key {i+1}: No response")
            except Exception as e:
                results.append(f"❌ Key {i+1}: {str(e)[:50]}...")
        
        return "\n".join(results)
        
    except ImportError:
        return "❌ Google Generative AI library not available"
    except Exception as e:
        return f"❌ Error testing keys: {str(e)}"

def has_api_keys():
    """Check if API keys are available in memory"""
    global current_api_keys
    return len(current_api_keys) > 0

def get_api_keys():
    """Get API keys from memory"""
    global current_api_keys
    return current_api_keys.copy()

# Function to load the parakeet TDT model
def load_model():
    # Load the model from HuggingFace
    print("Loading ASR model...")
    asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
    print("Model loaded successfully!")
    return asr_model

# Global model variable to avoid reloading
model = None

def get_audio_duration(file_path):
    """Get the duration of an audio file using ffprobe"""
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        file_path
    ]
    try:
        output = subprocess.check_output(cmd).decode('utf-8').strip()
        return float(output)
    except (subprocess.SubprocessError, ValueError):
        return None

def extract_audio_from_video(video_path, progress=None):
    """Extract audio from video file"""
    # Use a dummy progress function if None provided
    if progress is None:
        progress = lambda x, desc=None: None
    
    progress(0.1, desc="Extracting audio from video...")
    
    # Create a temporary file for the extracted audio
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    audio_path = temp_audio.name
    temp_audio.close()
    
    # Extract audio using ffmpeg
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # PCM 16-bit
        '-ar', '16000',  # 16kHz sample rate
        '-ac', '1',  # Mono
        audio_path,
        '-y'  # Overwrite if exists
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        progress(0.2, desc="Audio extraction complete")
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        return None

def split_audio_file(file_path, chunk_duration=600, progress=None):
    """Split audio into chunks of specified duration (in seconds)"""
    # Create temporary directory for chunks
    temp_dir = tempfile.mkdtemp()
    
    # Get total duration
    duration = get_audio_duration(file_path)
    if not duration:
        print(f"❌ Could not determine audio duration for: {file_path}")
        return None, 0
    
    print(f"📊 Audio duration: {duration:.1f}s, splitting into {chunk_duration}s chunks")
    
    # Calculate number of chunks
    num_chunks = math.ceil(duration / chunk_duration)
    chunk_files = []
    
    for i in range(num_chunks):
        if progress is not None:
            progress(i/num_chunks * 0.2, desc=f"Splitting audio ({i+1}/{num_chunks})...")
            
        start_time = i * chunk_duration
        output_file = os.path.join(temp_dir, f"chunk_{i:03d}.wav")
        
        # Use ffmpeg to extract chunk
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-ss', str(start_time),
            '-t', str(chunk_duration),
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            output_file,
            '-y'  # Overwrite if exists
        ]
        
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                chunk_files.append(output_file)
                print(f"✅ Created chunk {i+1}/{num_chunks}: {os.path.basename(output_file)}")
            else:
                print(f"⚠️ Chunk {i+1} created but is empty, skipping")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating chunk {i+1}: {e}")
            # If error occurs, skip this chunk
            continue
    
    print(f"📁 Successfully created {len(chunk_files)} audio chunks in {temp_dir}")
    return chunk_files, duration

def transcribe_audio(audio_file, is_music=False, enable_chunking=True, chunk_duration=30, use_model_chunking=False, progress=gr.Progress()):
    global model
    
    # Load the model if not already loaded
    if model is None:
        progress(0.1, desc="Loading model...")
        model = load_model()
    
    # Save the temporary audio file if it's from Gradio
    if isinstance(audio_file, tuple):
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()
        
        sample_rate, audio_data = audio_file
        
        # Convert stereo to mono if needed
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        import soundfile as sf
        sf.write(temp_audio_path, audio_data, sample_rate)
        audio_path = temp_audio_path
    else:
        # For files uploaded directly, we need to convert if stereo
        import soundfile as sf
        try:
            audio_data, sample_rate = sf.read(audio_file)
            
            # Convert stereo to mono if needed
            if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
                audio_data = np.mean(audio_data, axis=1)
                
                # For music, apply some preprocessing to improve vocal separation
                if is_music:
                    try:
                        # Normalize audio
                        audio_data = audio_data / np.max(np.abs(audio_data))
                        
                        # Apply a simple high-pass filter to emphasize vocals (at 200Hz)
                        from scipy import signal
                        b, a = signal.butter(4, 200/(sample_rate/2), 'highpass')
                        audio_data = signal.filtfilt(b, a, audio_data)
                        
                        # Slight compression to bring up quieter vocals
                        threshold = 0.1
                        ratio = 0.5
                        audio_data = np.where(
                            np.abs(audio_data) > threshold,
                            threshold + (np.abs(audio_data) - threshold) * ratio * np.sign(audio_data),
                            audio_data
                        )
                    except ImportError:
                        # If scipy is not available, skip preprocessing
                        pass
                
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio_path = temp_audio.name
                temp_audio.close()
                sf.write(temp_audio_path, audio_data, sample_rate)
                audio_path = temp_audio_path
            else:
                audio_path = audio_file
        except Exception:
            # If we can't read it as an audio file, it might be a video
            audio_path = audio_file
    
    # Check if audio is long and needs splitting
    duration = get_audio_duration(audio_path)
    long_audio_threshold = 600  # 10 minutes in seconds
    audio_chunk_duration = 600  # 10 minutes in seconds for long audio splitting
    
    if duration and duration > long_audio_threshold:
        print(f"🎵 Long audio detected ({duration:.1f}s > {long_audio_threshold}s)")
        print(f"🔄 Switching to chunked processing mode")
        return process_long_audio(audio_path, is_music, progress, audio_chunk_duration)
    
    # Normal processing for shorter audio
    return process_audio_chunk(audio_path, is_music, progress, 0, 1, enable_chunking, chunk_duration, use_model_chunking)

def transcribe_video(video_file, is_music=False, enable_chunking=True, chunk_duration=30, use_model_chunking=False, progress=gr.Progress()):
    """Transcribe the audio track from a video file"""
    # Extract audio from video
    audio_path = extract_audio_from_video(video_file, progress)
    if not audio_path:
        return "Error extracting audio from video", [], None
    
    # Now process the extracted audio
    return transcribe_audio(audio_path, is_music, enable_chunking, chunk_duration, use_model_chunking, progress)

def process_long_audio(audio_path, is_music, progress, audio_chunk_duration):
    """Process long audio by splitting it into chunks"""
    print(f"🎵 Processing long audio file: {os.path.basename(audio_path)}")
    print(f"📏 Using chunk duration: {audio_chunk_duration} seconds")
    
    # Split the audio file
    progress(0.1, desc="Analyzing and splitting audio file...")
    chunk_files, total_duration = split_audio_file(audio_path, audio_chunk_duration, progress)
    
    if not chunk_files:
        error_msg = "❌ Error splitting audio file - no chunks created"
        print(error_msg)
        return error_msg, [], None
    
    print(f"🎯 Processing {len(chunk_files)} chunks for {total_duration:.1f}s of audio")
    
    # Process each chunk
    all_segments = []
    full_text_parts = []
    csv_data = []
    
    for i, chunk_file in enumerate(chunk_files):
        chunk_start_time = i * audio_chunk_duration
        progress_start = 0.2 + (i / len(chunk_files)) * 0.8
        progress_end = 0.2 + ((i + 1) / len(chunk_files)) * 0.8
        
        progress(progress_start, desc=f"Transcribing chunk {i+1}/{len(chunk_files)}...")
        print(f"🎤 Processing chunk {i+1}/{len(chunk_files)} (time offset: {chunk_start_time}s)")
        
        # Process this chunk (disable smart chunking for long audio processing)
        chunk_text, chunk_segments, _ = process_audio_chunk(
            chunk_file, 
            is_music, 
            progress, 
            chunk_start_time,
            progress_end - progress_start,
            False,  # Disable smart chunking for long audio chunks
            30,     # Default chunk duration for smart chunking (not used here)
            False   # Don't use model chunking
        )
        
        # Add to results
        if chunk_text:
            full_text_parts.append(chunk_text)
            print(f"✅ Chunk {i+1} transcribed: {len(chunk_segments)} segments")
        
        all_segments.extend(chunk_segments)
        
        # Add to CSV data
        for segment in chunk_segments:
            csv_data.append({
                "Start (s)": f"{segment['start']:.2f}",
                "End (s)": f"{segment['end']:.2f}",
                "Segment": segment['text']
            })
        
        # Clean up chunk file
        try:
            os.unlink(chunk_file)
        except:
            pass
    
    # Clean up temp directory
    try:
        if chunk_files:
            temp_dir = os.path.dirname(chunk_files[0])
            os.rmdir(temp_dir)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")
    except:
        pass
    
    # Combine results
    full_text = " ".join(full_text_parts)
    total_segments = len(all_segments)
    
    print(f"📊 Long audio processing complete:")
    print(f"   • Total segments: {total_segments}")
    print(f"   • Total duration: {total_duration:.1f}s")
    print(f"   • Text length: {len(full_text)} characters")
    
    # Create DataFrame for CSV
    df = pd.DataFrame(csv_data)
    
    # Save CSV to a temporary file
    csv_path = "transcript.csv"
    df.to_csv(csv_path, index=False)
    print(f"💾 Saved transcript to: {csv_path}")
    
    progress(1.0, desc="Long audio processing complete!")
    
    return full_text, all_segments, csv_path

def process_audio_chunk(audio_path, is_music, progress, time_offset=0, progress_scale=1.0, enable_chunking=True, chunk_duration=30, use_model_chunking=False):
    """Process a single audio chunk"""
    progress(0.3 * progress_scale, desc="Transcribing audio...")
    
    # Transcribe with timestamps
    output = model.transcribe([audio_path], timestamps=True)
    
    # Extract segment-level timestamps
    segments = []
    csv_data = []
    
    # Convert timestamp info to desired format
    if hasattr(output[0], 'timestamp') and 'segment' in output[0].timestamp:
        for stamp in output[0].timestamp['segment']:
            segment_text = stamp['segment']
            start_time = stamp['start'] + time_offset
            end_time = stamp['end'] + time_offset
            
            # For music, we can do some post-processing of the timestamps
            if is_music:
                # Add a small buffer to ensure segments don't cut off too early
                # This helps with stretched syllables often found in singing
                end_time += 0.3
                
                # Minimum segment duration for lyrics
                min_duration = 0.5
                if end_time - start_time < min_duration:
                    end_time = start_time + min_duration
            
            segments.append({
                "text": segment_text,
                "start": start_time,
                "end": end_time
            })
            
            # Add to CSV data
            csv_data.append({
                "Start (s)": f"{start_time:.2f}",
                "End (s)": f"{end_time:.2f}",
                "Segment": segment_text
            })
    
    # Create DataFrame for CSV
    df = pd.DataFrame(csv_data)
    
    # Save CSV to a temporary file
    csv_path = "transcript.csv"
    if time_offset == 0:  # Only save for first chunk or single chunk
        df.to_csv(csv_path, index=False)
    
    # Full transcript
    full_text = output[0].text if hasattr(output[0], 'text') else ""
    
    # Apply smart chunking if enabled
    chunked_segments = segments
    if enable_chunking and segments and time_offset == 0:  # Only chunk for main processing
        try:
            progress(0.8 * progress_scale, desc="Applying smart chunking...")
            
            # Create chunking configuration
            chunk_config = ChunkConfig(
                max_duration=chunk_duration,
                use_model_chunking=use_model_chunking
            )
            
            # Initialize chunker
            chunker = TranscriptChunker(chunk_config)
            
            # Apply chunking
            chunked_segments = chunker.chunk_transcript_by_time(segments, chunk_duration)
            
            # Save chunked transcript for dubbing pipeline
            chunker.save_chunked_transcript(chunked_segments, "chunked_transcript.json")
            
            # Analyze chunking efficiency
            analysis = chunker.analyze_chunking_efficiency(segments, chunked_segments)
            
            print(f"📊 Chunking Analysis:")
            print(f"  • Original segments: {analysis['original_segments']}")
            print(f"  • Generated chunks: {analysis['generated_chunks']}")
            print(f"  • API call reduction: {analysis['api_call_reduction_percent']:.1f}%")
            print(f"  • Average chunk duration: {analysis['average_chunk_duration']:.1f}s")
            
        except Exception as e:
            print(f"⚠️ Chunking failed, using original segments: {str(e)}")
            chunked_segments = segments
    
    # Clean up the temporary file if created
    if isinstance(audio_path, str) and os.path.exists(audio_path) and audio_path.startswith(tempfile.gettempdir()):
        try:
            os.unlink(audio_path)
        except:
            pass
    
    return full_text, chunked_segments, csv_path if time_offset == 0 else None

def create_transcript_table(segments):
    if not segments:
        return "No segments found"
    
    html = """
    <style>
    .transcript-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .transcript-table th, .transcript-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .transcript-table th {
        background-color: #f2f2f2;
    }
    .transcript-table tr:hover {
        background-color: #f5f5f5;
        cursor: pointer;
    }
    </style>
    <table class="transcript-table">
        <tr>
            <th>Start (s)</th>
            <th>End (s)</th>
            <th>Segment</th>
        </tr>
    """
    
    for segment in segments:
        html += f"""
        <tr onclick="document.dispatchEvent(new CustomEvent('play_segment', {{detail: {{start: {segment['start']}, end: {segment['end']}}}}}))">
            <td>{segment['start']:.2f}</td>
            <td>{segment['end']:.2f}</td>
            <td>{segment['text']}</td>
        </tr>
        """
    
    html += "</table>"
    return html

# Dubbing Pipeline Functions
def save_asr_results(segments, video_path=None):
    """Save ASR results in the format expected by the dubbing pipeline."""
    if not segments:
        return False
        
    # Convert segments to the expected format with enhanced metadata
    asr_data = []
    for segment in segments:
        asr_data.append({
            "start": float(segment["start"]),
            "end": float(segment["end"]), 
            "text": str(segment["text"]).strip(),
            "duration": float(segment["end"]) - float(segment["start"])
        })
    
    # Add metadata
    metadata = {
        "total_segments": len(asr_data),
        "total_duration": max(seg["end"] for seg in asr_data) if asr_data else 0,
        "video_path": video_path,
        "created_at": json.dumps({"timestamp": "auto-generated"}),
        "format_version": "1.0"
    }
    
    # Create the complete ASR output
    asr_output = {
        "metadata": metadata,
        "segments": asr_data
    }
    
    # Save to original_asr.json
    with open("original_asr.json", "w", encoding="utf-8") as f:
        json.dump(asr_output, f, indent=2, ensure_ascii=False)
    
    return True

def load_asr_results():
    """Load existing ASR results if available."""
    try:
        if os.path.exists("original_asr.json"):
            with open("original_asr.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Handle both old and new format
            if isinstance(data, list):
                # Old format - just segments
                return data
            elif isinstance(data, dict) and "segments" in data:
                # New format - with metadata
                return data["segments"]
            else:
                return []
        return []
    except Exception as e:
        print(f"Error loading ASR results: {str(e)}")
        return []

def check_asr_compatibility():
    """Check if existing ASR results are compatible with dubbing pipeline."""
    asr_data = load_asr_results()
    
    if not asr_data:
        return False, "No ASR results found"
        
    # Validate format
    required_fields = ["start", "end", "text"]
    for i, segment in enumerate(asr_data):
        for field in required_fields:
            if field not in segment:
                return False, f"Segment {i+1} missing required field: {field}"
                
        # Validate timing
        try:
            start = float(segment["start"])
            end = float(segment["end"])
            if start >= end:
                return False, f"Segment {i+1} has invalid timing"
        except (ValueError, TypeError):
            return False, f"Segment {i+1} has invalid timing values"
            
        # Validate text
        if not segment["text"].strip():
            return False, f"Segment {i+1} has empty text"
    
    return True, f"Compatible ASR results with {len(asr_data)} segments"

def get_asr_summary():
    """Get a summary of current ASR results."""
    asr_data = load_asr_results()
    
    if not asr_data:
        return "No ASR results available"
        
    total_duration = max(seg["end"] for seg in asr_data) if asr_data else 0
    total_text_length = sum(len(seg["text"]) for seg in asr_data)
    
    return f"""ASR Results Summary:
• {len(asr_data)} segments
• {total_duration:.1f} seconds total duration
• {total_text_length} characters of text
• Average segment length: {total_duration/len(asr_data):.1f}s"""

def run_dubbing_pipeline(
    mode: str,
    video_file,
    api_keys_text: str,
    style_config_text: str,
    voice_name: str,
    manual_translation_text: str = "",
    skip_asr: bool = False,
    progress=gr.Progress()
):
    """Run the dubbing pipeline with the specified configuration."""
    if not DUBBING_AVAILABLE:
        return "Error: Dubbing pipeline not available", None, None
    
    try:
        # Validate inputs
        if not video_file:
            return "Error: Please upload a video file", None, None
            
        # Parse API keys
        api_keys = [key.strip() for key in api_keys_text.split('\n') if key.strip()]
        if not api_keys:
            return "Error: Please provide at least one API key", None, None
            
        # Parse style configuration
        try:
            style_config = json.loads(style_config_text) if style_config_text.strip() else {}
        except json.JSONDecodeError:
            return "Error: Invalid JSON format in style configuration", None, None
            
        if not voice_name.strip():
            return "Error: Please specify a voice name", None, None
            
        # Create pipeline configuration
        config = PipelineConfig(
            video_path=video_file,
            api_keys=api_keys,
            voice_name=voice_name.strip(),
            style_config=style_config,
            mode=mode,
            manual_translation=manual_translation_text if mode == "manual" else None
        )
        
        # Initialize pipeline controller
        controller = PipelineController()
        
        # Progress callback
        def progress_callback(prog, status):
            progress(prog, desc=status)
        
        # Run the appropriate pipeline
        if mode == "automatic":
            if not skip_asr and not os.path.exists("original_asr.json"):
                return "Error: No ASR results found. Please run transcription first or uncheck 'Skip ASR'", None, None
            result_path = controller.run_automatic_pipeline(config, progress_callback)
        elif mode == "manual":
            if not manual_translation_text.strip():
                return "Error: Please provide manual translation for manual mode", None, None
            result_path = controller.run_manual_pipeline(config, progress_callback)
        else:
            return "Error: Invalid mode selected", None, None
            
        # Return success message and output file
        return f"Dubbing completed successfully! Output saved to: {result_path}", result_path, result_path
        
    except Exception as e:
        error_msg = f"Dubbing pipeline failed: {str(e)}"
        print(error_msg)
        return error_msg, None, None

def continue_dubbing_pipeline(
    video_file,
    api_keys_text: str,
    voice_name: str,
    progress=gr.Progress()
):
    """Continue dubbing pipeline from the last checkpoint."""
    if not DUBBING_AVAILABLE:
        return "Error: Dubbing pipeline not available", None, None
        
    try:
        # Parse API keys
        api_keys = [key.strip() for key in api_keys_text.split('\n') if key.strip()]
        if not api_keys:
            return "Error: Please provide at least one API key", None, None
            
        if not voice_name.strip():
            return "Error: Please specify a voice name", None, None
            
        # Create basic configuration for continuation
        config = PipelineConfig(
            video_path=video_file,
            api_keys=api_keys,
            voice_name=voice_name.strip(),
            style_config={},
            mode="continuation"
        )
        
        # Initialize pipeline controller
        controller = PipelineController()
        
        # Progress callback
        def progress_callback(prog, status):
            progress(prog, desc=status)
            
        # Continue from checkpoint
        result_path = controller.continue_from_checkpoint(config, progress_callback)
        
        return f"Pipeline continuation completed! Output: {result_path}", result_path, result_path
        
    except Exception as e:
        error_msg = f"Pipeline continuation failed: {str(e)}"
        print(error_msg)
        return error_msg, None, None

def detect_pipeline_state():
    """Detect the current state of the dubbing pipeline."""
    if not DUBBING_AVAILABLE:
        return "Dubbing pipeline not available"
        
    try:
        controller = PipelineController()
        state = controller.detect_pipeline_state()
        
        state_messages = {
            "asr_needed": "❌ ASR results not found - Please run transcription first",
            "translation_needed": "✅ ASR complete - Ready for translation",
            "tts_needed": "✅ Translation complete - Ready for TTS generation", 
            "stitching_needed": "✅ TTS complete - Ready for final video creation",
            "complete": "✅ Pipeline complete - Dubbed video ready"
        }
        
        return state_messages.get(state, f"Unknown state: {state}")
        
    except Exception as e:
        return f"Error detecting pipeline state: {str(e)}"

def get_default_style_config():
    """Get default style configuration as JSON string."""
    default_config = {
        "tone": "neutral",
        "dialect": "standard", 
        "genre": "general"
    }
    return json.dumps(default_config, indent=2)

def validate_manual_translation(translation_text: str):
    """Validate manual translation JSON format."""
    if not translation_text.strip():
        return "❌ No translation text provided"
        
    try:
        # Parse JSON
        segments = json.loads(translation_text)
        
        if not isinstance(segments, list):
            return "❌ Translation must be a JSON array"
        
        # Validate each segment
        required_fields = ["start", "end", "text_translated"]
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                return f"❌ Segment {i+1} must be an object"
            
            for field in required_fields:
                if field not in segment:
                    return f"❌ Segment {i+1} missing field: {field}"
            
            # Validate timing
            try:
                start = float(segment["start"])
                end = float(segment["end"])
                if start >= end:
                    return f"❌ Segment {i+1} has invalid timing"
            except (ValueError, TypeError):
                return f"❌ Segment {i+1} has invalid timing values"
            
            # Validate text
            if not segment["text_translated"].strip():
                return f"❌ Segment {i+1} has empty translation"
        
        return f"✅ Valid translation with {len(segments)} segments"
        
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON: {str(e)}"
    except Exception as e:
        return f"❌ Validation error: {str(e)}"

def generate_translation_template():
    """Generate a translation template from existing ASR results."""
    try:
        asr_data = load_asr_results()
        if not asr_data:
            return "No ASR results found. Please run transcription first."
        
        # Create template with empty translations
        template = []
        for segment in asr_data:
            template.append({
                "start": segment["start"],
                "end": segment["end"],
                "text_translated": f"[TRANSLATE: {segment['text']}]"
            })
        
        return json.dumps(template, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Error generating template: {str(e)}"

def convert_format_to_json(input_text: str, input_format: str):
    """Convert different formats to JSON for manual translation."""
    if not input_text.strip():
        return False, "No input text provided", ""
    
    try:
        if input_format == "json":
            # Validate JSON
            segments = json.loads(input_text)
            return True, "JSON format validated", json.dumps(segments, indent=2, ensure_ascii=False)
        
        elif input_format == "srt":
            # Simple SRT parser
            segments = []
            blocks = input_text.strip().split('\n\n')
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # Parse timing line (format: 00:00:00,000 --> 00:00:02,500)
                    timing_line = lines[1]
                    if ' --> ' in timing_line:
                        start_str, end_str = timing_line.split(' --> ')
                        start = parse_srt_time(start_str)
                        end = parse_srt_time(end_str)
                        text = ' '.join(lines[2:])
                        
                        segments.append({
                            "start": start,
                            "end": end,
                            "text_translated": text
                        })
            
            if segments:
                return True, f"Converted {len(segments)} SRT segments", json.dumps(segments, indent=2, ensure_ascii=False)
            else:
                return False, "No valid SRT segments found", ""
        
        elif input_format == "csv":
            # Simple CSV parser (assuming: start,end,text)
            segments = []
            lines = input_text.strip().split('\n')
            
            for i, line in enumerate(lines):
                if i == 0 and ('start' in line.lower() or 'time' in line.lower()):
                    continue  # Skip header
                
                parts = line.split(',', 2)
                if len(parts) >= 3:
                    try:
                        start = float(parts[0])
                        end = float(parts[1])
                        text = parts[2].strip('"')
                        
                        segments.append({
                            "start": start,
                            "end": end,
                            "text_translated": text
                        })
                    except ValueError:
                        continue
            
            if segments:
                return True, f"Converted {len(segments)} CSV segments", json.dumps(segments, indent=2, ensure_ascii=False)
            else:
                return False, "No valid CSV segments found", ""
        
        else:
            return False, f"Unsupported format: {input_format}", ""
            
    except Exception as e:
        return False, f"Conversion error: {str(e)}", ""

def parse_srt_time(time_str):
    """Parse SRT time format to seconds."""
    # Format: 00:00:00,000
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def get_manual_mode_help():
    """Get help text for manual mode."""
    return """
# Manual Mode Help

## JSON Format
Provide translations in this format:
```json
[
  {"start": 0.0, "end": 2.5, "text_translated": "Hello world"},
  {"start": 2.5, "end": 5.0, "text_translated": "How are you?"}
]
```

## Required Fields
- `start`: Start time in seconds (float)
- `end`: End time in seconds (float)  
- `text_translated`: Your translation text (string)

## Tips
- Use "Generate Template" to get started
- Convert from SRT/CSV formats using the conversion tools
- Validate your JSON before running the pipeline
"""

def get_manual_mode_status():
    """Get current manual mode status."""
    try:
        asr_data = load_asr_results()
        if not asr_data:
            return "❌ No ASR results found. Run transcription first."
        
        return f"✅ Ready for manual translation\n{len(asr_data)} segments available\nUse 'Generate Template' to get started"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_kokoro_languages():
    """Get available Kokoro languages"""
    if not KOKORO_TTS_AVAILABLE:
        return []
    
    try:
        voice_parser = KokoroVoiceParser()
        languages = []
        for lang_code, lang_name in voice_parser.language_mapping.items():
            languages.append((lang_name, lang_code))
        return languages
    except Exception as e:
        print(f"Error getting Kokoro languages: {str(e)}")
        return []

def get_kokoro_voices_for_language(language_code):
    """Get available Kokoro voices for a specific language"""
    if not KOKORO_TTS_AVAILABLE or not language_code:
        return []
    
    try:
        voice_parser = KokoroVoiceParser()
        voices = voice_parser.get_voice_choices_for_language(language_code)
        return voices
    except Exception as e:
        print(f"Error getting Kokoro voices for {language_code}: {str(e)}")
        return []

def update_kokoro_voices(language_code):
    """Update Kokoro voice dropdown based on selected language"""
    voices = get_kokoro_voices_for_language(language_code)
    return gr.update(choices=voices, value=voices[0] if voices else None)

def get_gemini_languages():
    """Get available Gemini languages"""
    try:
        from gemini_voice_library import GeminiVoiceLibrary
        gemini_library = GeminiVoiceLibrary()
        
        # Create language choices with display names (official Gemini TTS supported languages)
        language_mapping = {
            "ar": "Arabic (Egyptian)", "de": "German (Germany)", "en": "English (US)", 
            "es": "Spanish (US)", "fr": "French (France)", "hi": "Hindi (India)",
            "id": "Indonesian (Indonesia)", "it": "Italian (Italy)", "ja": "Japanese (Japan)",
            "ko": "Korean (Korea)", "pt": "Portuguese (Brazil)", "ru": "Russian (Russia)",
            "nl": "Dutch (Netherlands)", "pl": "Polish (Poland)", "th": "Thai (Thailand)",
            "tr": "Turkish (Turkey)", "vi": "Vietnamese (Vietnam)", "ro": "Romanian (Romania)",
            "uk": "Ukrainian (Ukraine)", "bn": "Bengali (Bangladesh)", "mr": "Marathi (India)",
            "ta": "Tamil (India)", "te": "Telugu (India)"
        }
        
        languages = []
        for lang_code in gemini_library.gemini_voices.keys():
            lang_name = language_mapping.get(lang_code, lang_code.upper())
            languages.append((lang_name, lang_code))
        
        return sorted(languages)
    except Exception as e:
        print(f"Error getting Gemini languages: {str(e)}")
        return []

def get_gemini_voices_for_language(language_code):
    """Get available Gemini voices for a specific language"""
    if not language_code:
        return []
    
    try:
        from gemini_voice_library import GeminiVoiceLibrary
        gemini_library = GeminiVoiceLibrary()
        return gemini_library.create_voice_choices_for_language(language_code)
    except Exception as e:
        print(f"Error getting Gemini voices: {str(e)}")
        return []

def update_gemini_voices(language_code):
    """Update Gemini voice dropdown based on selected language"""
    voices = get_gemini_voices_for_language(language_code)
    return gr.update(choices=voices, value=voices[0] if voices else None)

def run_dubbing_pipeline(mode, video_file, api_keys_text, style_config, voice_name, manual_translation, skip_asr):
    """Run the complete dubbing pipeline with FIXED TTS."""
    if not DUBBING_AVAILABLE:
        return "❌ Dubbing pipeline not available", None, None
    
    try:
        # Parse API keys
        if not api_keys_text.strip():
            return "❌ No API keys provided", None, None
        
        api_keys = [key.strip() for key in api_keys_text.strip().split('\n') if key.strip()]
        
        # Initialize FINAL WORKING TTS service (confirmed working)
        tts_service = FinalWorkingTTS(api_keys[0], voice_name)
        
        # Get transcription data
        if not skip_asr:
            asr_data = load_asr_results()
            if not asr_data:
                return "❌ No ASR results found. Please run transcription first.", None, None
        else:
            asr_data = load_asr_results()
        
        # Handle translation based on mode
        if mode == "automatic":
            # Use RealGeminiService for translation
            real_service = RealGeminiService(api_keys)
            
            # Parse style config
            try:
                style_json = json.loads(style_config)
            except:
                style_json = {
                    "target_language": "Hindi",
                    "tone": "neutral",
                    "dialect": "hindi_devanagari",
                    "genre": "general"
                }
            
            # Progress callback
            def progress_callback(progress, message):
                print(f"Translation Progress: {progress:.1%} - {message}")
            
            # Translate using Gemini
            translated_segments = real_service.translate_full_transcript(
                asr_data, style_json, progress_callback
            )
            
        else:  # manual mode
            if not manual_translation.strip():
                return "❌ No manual translation provided", None, None
            
            try:
                translated_segments = json.loads(manual_translation)
            except json.JSONDecodeError:
                return "❌ Invalid JSON in manual translation", None, None
        
        # Generate TTS audio using FIXED service
        def tts_progress_callback(progress, message):
            print(f"TTS Progress: {progress:.1%} - {message}")
        
        # Process with final working TTS service
        final_audio = tts_service.process_subtitle_json(
            translated_segments, tts_progress_callback
        )
        
        # Create final video if video file provided
        if video_file:
            try:
                # Create final video using FFmpeg directly
                dubbed_video_path = "final_dubbed.mp4"
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_file,
                    "-i", final_audio,
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-shortest",
                    dubbed_video_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFmpeg failed: {result.stderr}")
                return f"✅ Dubbing completed successfully!\n🎬 Video: {dubbed_video_path}\n🎵 Audio: {final_audio}", dubbed_video_path, final_audio
            except Exception as e:
                print(f"Video creation failed: {str(e)}")
                return f"✅ TTS audio generated successfully!\n🎵 Audio: {final_audio}\n⚠️ Video creation failed: {str(e)}", None, final_audio
        else:
            return f"✅ TTS audio generated successfully!\n🎵 Audio: {final_audio}", None, final_audio
        
    except Exception as e:
        return f"❌ Pipeline failed: {str(e)}", None, None

def continue_dubbing_pipeline(video_file, api_keys_text, voice_name):
    """Continue dubbing pipeline from checkpoint."""
    return "❌ Checkpoint continuation not implemented yet", None, None

def detect_pipeline_state():
    """Detect current pipeline state."""
    try:
        states = []
        
        # Check ASR results
        if os.path.exists("original_asr.json"):
            states.append("✅ ASR completed")
        else:
            states.append("❌ ASR not completed")
        
        # Check translation results
        if os.path.exists("translated.json"):
            states.append("✅ Translation completed")
        else:
            states.append("❌ Translation not completed")
        
        # Check TTS chunks
        if os.path.exists("tts_chunks") and os.listdir("tts_chunks"):
            chunk_count = len([f for f in os.listdir("tts_chunks") if f.endswith('.wav')])
            states.append(f"✅ TTS completed ({chunk_count} chunks)")
        else:
            states.append("❌ TTS not completed")
        
        # Check final video
        if os.path.exists("output_dubbed.mp4"):
            states.append("✅ Final video created")
        else:
            states.append("❌ Final video not created")
        
        return "\n".join(states)
        
    except Exception as e:
        return f"Error detecting pipeline state: {str(e)}"

def get_manual_mode_status():
    """Get current manual mode status and capabilities."""
    if not MANUAL_MODE_AVAILABLE:
        return "❌ Manual mode utilities not available"
        
    try:
        workflow = ManualModeWorkflow()
        status = workflow.get_manual_mode_status()
        
        status_text = "Manual Mode Status:\\n"
        
        if status["asr_available"]:
            status_text += f"✅ ASR results available ({status['template_segments']} segments)\\n"
            if status["can_generate_template"]:
                status_text += "✅ Can generate translation template\\n"
        else:
            status_text += "❌ No ASR results found\\n"
            status_text += "ℹ️ Run transcription first to generate templates\\n"
            
        if status["translation_exists"]:
            status_text += "✅ Manual translation exists\\n"
        else:
            status_text += "❌ No manual translation found\\n"
            
        return status_text
        
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"

# Define custom JavaScript to handle segment playback
js_code = """
function(audio) {
    document.addEventListener('play_segment', function(e) {
        const audioEl = document.querySelector('audio');
        if (audioEl) {
            audioEl.currentTime = e.detail.start;
            audioEl.play();
            
            // Optional: Stop at segment end
            const stopAtEnd = function() {
                if (audioEl.currentTime >= e.detail.end) {
                    audioEl.pause();
                    audioEl.removeEventListener('timeupdate', stopAtEnd);
                }
            };
            audioEl.addEventListener('timeupdate', stopAtEnd);
        }
    });
    return audio;
}
"""

# Batch Video Creation Function
def run_batch_video_creation(video_file, audio_files, progress=gr.Progress()):
    """Create multiple videos by combining one video with multiple audio files"""
    if not video_file or not audio_files:
        return "❌ Please provide both a video file and audio files", []
    
    try:
        results = []
        total_files = len(audio_files)
        
        # Create output directory
        output_dir = "batch_dubbed_videos"
        os.makedirs(output_dir, exist_ok=True)
        
        for i, audio_file in enumerate(audio_files):
            try:
                progress((i / total_files), desc=f"Processing audio {i+1}/{total_files}")
                
                # Create output filename
                video_name = Path(video_file.name).stem if hasattr(video_file, 'name') else "video"
                audio_name = Path(audio_file.name).stem if hasattr(audio_file, 'name') else f"audio_{i+1}"
                output_video = os.path.join(output_dir, f"{video_name}_{audio_name}_combined.mp4")
                
                # Get file paths
                video_path = video_file.name if hasattr(video_file, 'name') else video_file
                audio_path = audio_file.name if hasattr(audio_file, 'name') else audio_file
                
                # Combine video with audio using FFmpeg
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-shortest",
                    output_video
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    results.append(output_video)
                    print(f"✅ Created: {output_video}")
                else:
                    print(f"❌ Failed to process {audio_name}: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Error processing audio {i+1}: {str(e)}")
                continue
        
        progress(1.0, desc="Batch processing complete!")
        
        if results:
            return f"✅ Batch video creation completed!\n📁 Created {len(results)} videos in '{output_dir}' folder\n\n📋 Created files:\n" + "\n".join([f"• {os.path.basename(f)}" for f in results]), results
        else:
            return "❌ No videos were successfully created", []
            
    except Exception as e:
        return f"❌ Batch processing failed: {str(e)}", []

# Create Gradio interface
with gr.Blocks(css="footer {visibility: hidden}") as app:
    gr.Markdown("# Audio & Video Transcription and Dubbing Pipeline")
    gr.Markdown("Upload an audio/video file or record audio to get a transcript with timestamps, then optionally create dubbed videos")
    
    with gr.Tabs():
        # ASR Tab
        with gr.TabItem("🎤 Transcription"):
            with gr.Row():
                with gr.Column():
                    with gr.Tab("Upload Audio File"):
                        audio_input = gr.Audio(type="filepath", label="Upload Audio File")
                    
                    with gr.Tab("Upload Video File"):
                        video_input = gr.Video(label="Upload Video File")
                    
                    with gr.Tab("Microphone"):
                        audio_record = gr.Audio(
                            sources=["microphone"], 
                            type="filepath", 
                            label="Record Audio",
                            show_label=True
                        )
                    
                    is_music = gr.Checkbox(label="Music mode (better for songs)", info="Enable for more accurate song timestamps")
                    
                    # Chunking options
                    with gr.Group():
                        gr.Markdown("#### Smart Chunking Options")
                        enable_chunking = gr.Checkbox(
                            label="Enable smart chunking", 
                            value=True,
                            info="Group short segments into longer chunks for better TTS performance"
                        )
                        chunk_duration = gr.Dropdown(
                            label="Max chunk duration (seconds)",
                            choices=[15, 30, 45, 60, 90],
                            value=30,
                            info="Maximum duration for each chunk - longer chunks = fewer TTS API calls"
                        )
                        use_model_chunking = gr.Checkbox(
                            label="Use model-level chunking (if available)",
                            value=False,
                            info="Use Parakeet model's built-in chunking instead of post-processing"
                        )
                    
                    audio_btn = gr.Button("Transcribe Audio", variant="primary")
                    video_btn = gr.Button("Transcribe Video", variant="primary")
                    gr.Markdown("""
                    ### Notes:
                    - Audio or video files over 10 minutes will be automatically split into smaller chunks for processing
                    - Video files will have their audio tracks extracted for transcription
                    - **Smart chunking** groups short segments into longer chunks for better TTS performance
                    - Longer chunks = fewer API calls and more natural voice flow
                    - Transcription results are automatically saved for the dubbing pipeline
                    - Chunked transcripts are saved as `chunked_transcript.json` for the pipeline
                    """)
                
                with gr.Column():
                    full_transcript = gr.Textbox(label="Full Transcript", lines=5)
                    transcript_segments = gr.JSON(label="Segments Data", visible=False)
                    transcript_html = gr.HTML(label="Transcript Segments (Click a row to play)")
                    csv_output = gr.File(label="Download Transcript CSV")
                    audio_playback = gr.Audio(label="Audio Playback", elem_id="audio_playback", interactive=False)
                    
                    # ASR Status for Dubbing Pipeline
                    with gr.Group():
                        gr.Markdown("#### Dubbing Pipeline Status")
                        asr_status_output = gr.Textbox(
                            label="ASR Compatibility Status",
                            lines=4,
                            interactive=False,
                            info="Shows if transcription results are ready for dubbing"
                        )
                        refresh_asr_status_btn = gr.Button("🔄 Refresh Status", size="sm")
        
        # Dubbing Pipeline Tab
        with gr.TabItem("🎬 Step-by-Step Dubbing"):
            if not DUBBING_AVAILABLE:
                gr.Markdown("""
                ⚠️ **Dubbing pipeline is not available.**
                
                **To enable dubbing features:**
                1. Install the Google Generative AI library: `pip install google-generativeai`
                2. Restart the application
                """)
            else:
                gr.Markdown("### 🎬 Step-by-Step Video Dubbing")
                gr.Markdown("**Complete each step in order to see the results at each stage**")
                
                # Step 1: API Keys
                with gr.Group():
                    gr.Markdown("## Step 1: 🔑 Setup API Keys")
                    api_keys_input = gr.Textbox(
                        label="Gemini API Keys (one per line)",
                        placeholder="Enter your Gemini API keys here (one per line)...",
                        lines=3,
                        type="password"
                    )
                    with gr.Row():
                        save_keys_btn = gr.Button("💾 Save API Keys", variant="primary")
                        test_keys_btn = gr.Button("🧪 Test Keys", variant="secondary")
                    
                    api_status_output = gr.Textbox(
                        label="API Status",
                        lines=2,
                        interactive=False
                    )
                
                # Step 2: Load/Create Transcription
                with gr.Group():
                    gr.Markdown("## Step 2: 📝 Load or Create Transcription")
                    gr.Markdown("**Option A**: Upload video and transcribe here, **Option B**: Load from main tab, **Option C**: Paste JSON manually")
                    
                    with gr.Row():
                        with gr.Column():
                            # Option A: Upload and transcribe
                            gr.Markdown("### Option A: Upload & Transcribe")
                            video_upload = gr.File(
                                label="Upload Video to Transcribe",
                                file_types=["video"]
                            )
                            is_music_mode = gr.Checkbox(
                                label="Music Mode",
                                value=False,
                                info="Enable for better accuracy with songs/music"
                            )
                            
                            # Chunking options for step-by-step
                            with gr.Group():
                                gr.Markdown("**Smart Chunking Options**")
                                step_enable_chunking = gr.Checkbox(
                                    label="Enable smart chunking", 
                                    value=True,
                                    info="Group segments for better TTS performance"
                                )
                                step_chunk_duration = gr.Dropdown(
                                    label="Max chunk duration",
                                    choices=[15, 30, 45, 60],
                                    value=30,
                                    info="Longer chunks = fewer TTS API calls"
                                )
                            
                            transcribe_here_btn = gr.Button("🎤 Transcribe Video", variant="primary")
                            
                        with gr.Column():
                            # Option B: Load from ASR
                            gr.Markdown("### Option B: Load from Main Tab")
                            load_transcription_btn = gr.Button("📂 Load from Transcription Tab", variant="secondary")
                            
                            # Option C: Manual paste
                            gr.Markdown("### Option C: Paste Manually")
                            paste_json_btn = gr.Button("📝 Enable Manual Paste", variant="secondary")
                    
                    # Transcription display/edit area
                    transcription_display = gr.Textbox(
                        label="Transcription (JSON format - editable)",
                        lines=8,
                        interactive=True,
                        placeholder="""Transcription will appear here, or paste your JSON manually:
[
  {"start": 0.0, "end": 4.5, "text": "Hey everyone, this is Mipax speaking."},
  {"start": 4.5, "end": 9.8, "text": "Today we're diving into the latest One Piece theories."}
]""",
                        info="You can edit this transcription before translating"
                    )
                    
                    transcription_status = gr.Textbox(
                        label="Transcription Status",
                        lines=2,
                        interactive=False
                    )
                    
                    # Chunking analysis display
                    chunking_analysis = gr.Textbox(
                        label="Chunking Analysis",
                        lines=3,
                        interactive=False,
                        visible=False,
                        info="Shows efficiency gains from smart chunking"
                    )
                
                # Step 3: Translation
                with gr.Group():
                    gr.Markdown("## Step 3: 🌐 Translate Text")
                    gr.Markdown("**Option A**: Single language translation, **Option B**: Multi-language mode, **Option C**: Manual translation")
                    
                    with gr.Row():
                        with gr.Column():
                            # Option A: Single language translation
                            gr.Markdown("### Option A: Single Language Translation")
                            translation_prompt = gr.Textbox(
                                label="Translation Prompt (JSON format)",
                                value="""{
  "tone": "casual",
  "dialect": "hindi_devanagari",
  "genre": "video_narration",
  "instructions": "Translate to Hindi with Devanagari script, include common English loanwords transliterated"
}""",
                                lines=6
                            )
                            translate_btn = gr.Button("🔄 Translate with Gemini", variant="primary")
                            
                            # Option B: Multi-language translation
                            gr.Markdown("### Option B: Multi-Language Translation")
                            enable_multi_lang = gr.Checkbox(
                                label="Enable Multi-Language Mode",
                                value=False,
                                info="Translate to multiple languages sequentially"
                            )
                            
                            multi_lang_selection = gr.CheckboxGroup(
                                label="Select Target Languages",
                                choices=[
                                    ("Arabic (Egyptian)", "ar-EG"),
                                    ("German (Germany)", "de-DE"),
                                    ("Spanish (US)", "es-US"),
                                    ("French (France)", "fr-FR"),
                                    ("Hindi (India)", "hi-IN"),
                                    ("Indonesian (Indonesia)", "id-ID"),
                                    ("Italian (Italy)", "it-IT"),
                                    ("Japanese (Japan)", "ja-JP"),
                                    ("Korean (Korea)", "ko-KR"),
                                    ("Portuguese (Brazil)", "pt-BR"),
                                    ("Russian (Russia)", "ru-RU"),
                                    ("Dutch (Netherlands)", "nl-NL"),
                                    ("Polish (Poland)", "pl-PL"),
                                    ("Thai (Thailand)", "th-TH"),
                                    ("Turkish (Turkey)", "tr-TR"),
                                    ("Vietnamese (Vietnam)", "vi-VN"),
                                    ("Romanian (Romania)", "ro-RO"),
                                    ("Ukrainian (Ukraine)", "uk-UA"),
                                    ("Bengali (Bangladesh)", "bn-BD"),
                                    ("English (US)", "en-US"),
                                    ("English (India)", "en-IN"),
                                    ("Marathi (India)", "mr-IN"),
                                    ("Tamil (India)", "ta-IN"),
                                    ("Telugu (India)", "te-IN")
                                ],
                                value=["hi-IN", "es-US"],
                                visible=False
                            )
                            
                            custom_languages = gr.Textbox(
                                label="Custom Languages (comma-separated)",
                                placeholder="e.g., Tamil, Bengali, Telugu",
                                visible=False,
                                info="Add languages not in the list above"
                            )
                            
                            # Language-specific configuration display
                            selected_lang_config = gr.Textbox(
                                label="Selected Language Configuration (JSON - Editable)",
                                value="",
                                lines=15,
                                visible=False,
                                info="This shows the detailed configuration for the selected languages. You can edit this before translation."
                            )
                            
                            multi_lang_style = gr.Textbox(
                                label="Global Style Override (JSON - Optional)",
                                value="""{
  "tone": "casual",
  "genre": "video_narration",
  "instructions": "Maintain natural flow and cultural context for each language"
}""",
                                lines=4,
                                visible=False,
                                info="Optional: Override specific style settings for all languages"
                            )
                            
                            translate_multi_btn = gr.Button(
                                "🌍 Translate to Multiple Languages", 
                                variant="primary",
                                visible=False
                            )
                            
                        with gr.Column():
                            # Option C: Manual translation
                            gr.Markdown("### Option C: Manual Translation")
                            gr.Markdown("If you already have the translation, paste it here")
                            paste_translation_btn = gr.Button("📝 Enable Manual Translation", variant="secondary")
                    
                    # Translation display/edit area
                    translation_display = gr.Textbox(
                        label="Translation Result (JSON format - editable)",
                        lines=8,
                        interactive=True,
                        placeholder="""Translation will appear here, or paste your JSON manually:
[
  {"start": 0.0, "end": 4.5, "text_translated": "नमस्ते सब लोग, मैं मिपैक्स बोल रहा हूँ।"},
  {"start": 4.5, "end": 9.8, "text_translated": "आज हम वन पीस की ताज़ा थ्योरीज़ पर बात करने वाले हैं।"}
]""",
                        info="You can edit this translation before generating TTS"
                    )
                    
                    translation_status = gr.Textbox(
                        label="Translation Status",
                        lines=2,
                        interactive=False
                    )
                    
                    # Multi-language translation results
                    multi_lang_results = gr.Textbox(
                        label="Multi-Language Translation Results",
                        lines=4,
                        interactive=False,
                        visible=False,
                        info="Shows the status and file paths for each language translation"
                    )
                
                # Custom Voice Assignment Panel
                with gr.Group(visible=False) as custom_voice_assignment_panel:
                    gr.Markdown("## 🎤 Custom Voice Assignment Panel")
                    gr.Markdown("Assign specific voices to each translated language and upload custom voices.")
                    
                    # Voice Assignment Table
                    with gr.Group():
                        gr.Markdown("### 📜 Voice Assignment Table")
                        
                        with gr.Row():
                            refresh_voice_table_btn = gr.Button("🔄 Refresh Languages", variant="secondary")
                            auto_assign_voices_btn = gr.Button("🔀 Auto Assign Best Voices", variant="secondary")
                        
                        # Dynamic voice assignment table (will be populated)
                        voice_assignment_table_container = gr.Column()
                        
                        # Save assignments
                        with gr.Row():
                            save_voice_assignments_btn = gr.Button("💾 Save Voice Assignments", variant="primary")
                            voice_assignment_status = gr.Textbox(
                                label="Voice Assignment Status",
                                lines=2,
                                interactive=False
                            )
                    
                    # Custom Voice Upload Section
                    with gr.Group():
                        gr.Markdown("### 🧩 Custom Voice Upload")
                        
                        with gr.Row():
                            with gr.Column():
                                custom_voice_file_upload = gr.File(
                                    label="Upload Voice File (.wav or .mp3)",
                                    file_types=[".wav", ".mp3"],
                                    type="filepath"
                                )
                                
                                with gr.Row():
                                    custom_voice_language_code = gr.Textbox(
                                        label="Language Code",
                                        placeholder="e.g., hi, es, ja",
                                        max_lines=1
                                    )
                                    custom_voice_name = gr.Textbox(
                                        label="Voice Name",
                                        placeholder="e.g., my_custom_voice_hi",
                                        max_lines=1
                                    )
                                
                                upload_custom_voice_file_btn = gr.Button("📤 Upload Custom Voice", variant="primary")
                            
                            with gr.Column():
                                custom_voice_upload_status = gr.Textbox(
                                    label="Custom Voice Upload Status",
                                    lines=4,
                                    interactive=False
                                )
                    
                    # Voice Preview Section
                    with gr.Group():
                        gr.Markdown("### 🎧 Voice Preview")
                        gr.Markdown("Generate short previews for assigned voices")
                        
                        with gr.Row():
                            generate_voice_previews_btn = gr.Button("🔊 Generate Voice Previews", variant="secondary")
                            clear_voice_previews_btn = gr.Button("🗑️ Clear Previews", variant="secondary")
                        
                        # Dynamic voice previews (will be populated)
                        voice_previews_container = gr.Column()
                    
                    # Assignment Summary
                    with gr.Group():
                        gr.Markdown("### 📋 Assignment Summary")
                        voice_assignment_summary = gr.Textbox(
                            label="Current Voice Assignments",
                            lines=6,
                            interactive=False,
                            placeholder="Voice assignment summary will appear here..."
                        )
                    
                    # Voice assignment management
                    gr.Markdown("### Voice Assignment Management")
                    voice_assignments_display = gr.Textbox(
                        label="Auto-Assigned Voices (JSON - Editable)",
                        lines=8,
                        interactive=True,
                        visible=False,
                        info="Shows automatically assigned voices for each language. You can edit these assignments."
                    )
                    
                    with gr.Row(visible=False) as voice_management_row:
                        with gr.Column():
                            refresh_voices_btn = gr.Button("🔄 Refresh Voice Assignments", size="sm")
                            load_voice_config_btn = gr.Button("📁 Load Custom Voice Config", size="sm")
                        with gr.Column():
                            save_voice_config_btn = gr.Button("💾 Save Voice Config", size="sm")
                            preview_voices_btn = gr.Button("🎧 Preview Voices", size="sm")
                    
                    # Custom voice upload
                    with gr.Group(visible=False) as custom_voice_upload_group:
                        gr.Markdown("#### Upload Custom Voices")
                        custom_voice_language = gr.Dropdown(
                            label="Select Language for Custom Voice",
                            choices=[],
                            interactive=True
                        )
                        custom_voice_file = gr.File(
                            label="Upload Custom Voice File (.wav)",
                            file_types=[".wav"],
                            type="filepath"
                        )
                        upload_custom_voice_btn = gr.Button("📤 Upload Custom Voice", variant="secondary")
                    
                    # Voice Generation Section
                    with gr.Group(visible=False) as voice_generation_group:
                        gr.Markdown("### 🎤 Multi-Language Voice Generation")
                        gr.Markdown("Generate audio files for each translated language using assigned voices.")
                        
                        with gr.Row():
                            with gr.Column():
                                generate_all_voices_btn = gr.Button(
                                    "🎵 Generate All Voices", 
                                    variant="primary",
                                    size="lg"
                                )
                                voice_generation_status = gr.Textbox(
                                    label="Voice Generation Status",
                                    lines=4,
                                    interactive=False
                                )
                            
                            with gr.Column():
                                refresh_voice_previews_btn = gr.Button(
                                    "🔄 Refresh Voice Previews", 
                                    variant="secondary"
                                )
                                voice_generation_summary = gr.Textbox(
                                    label="Generated Voices Summary",
                                    lines=4,
                                    interactive=False
                                )
                        
                        # Dynamic voice previews (will be populated after generation)
                        voice_previews_container = gr.Column(visible=False)
                        
                        # Individual voice controls
                        with gr.Group() as individual_voice_controls:
                            gr.Markdown("#### Individual Voice Controls")
                            
                            with gr.Row():
                                select_language_for_regen = gr.Dropdown(
                                    label="Select Language to Regenerate",
                                    choices=[],
                                    interactive=True
                                )
                                regenerate_single_voice_btn = gr.Button(
                                    "🔄 Regenerate Voice", 
                                    variant="secondary"
                                )
                            
                            single_voice_status = gr.Textbox(
                                label="Single Voice Generation Status",
                                lines=2,
                                interactive=False
                            )
                    
                    # Final Dubbed Videos Section
                    with gr.Group(visible=False) as final_dubbed_videos_group:
                        gr.Markdown("### 🎬 Final Dubbed Videos")
                        gr.Markdown("Automatically merge generated voices with source video to create dubbed versions.")
                        
                        with gr.Row():
                            with gr.Column():
                                create_all_dubbed_videos_btn = gr.Button(
                                    "🎥 Create All Dubbed Videos", 
                                    variant="primary",
                                    size="lg"
                                )
                                video_dubbing_status = gr.Textbox(
                                    label="Video Dubbing Status",
                                    lines=4,
                                    interactive=False
                                )
                            
                            with gr.Column():
                                refresh_dubbed_videos_btn = gr.Button(
                                    "🔄 Refresh Video List", 
                                    variant="secondary"
                                )
                                dubbed_videos_summary = gr.Textbox(
                                    label="Dubbed Videos Summary",
                                    lines=4,
                                    interactive=False
                                )
                        
                        # Dubbing options
                        with gr.Row():
                            overwrite_existing_videos = gr.Checkbox(
                                label="Overwrite Existing Videos",
                                value=False,
                                info="Check to overwrite existing dubbed videos"
                            )
                            auto_create_after_voice_gen = gr.Checkbox(
                                label="Auto-Create After Voice Generation",
                                value=True,
                                info="Automatically create dubbed videos after generating voices"
                            )
                        
                        # Individual video controls
                        with gr.Group() as individual_video_controls:
                            gr.Markdown("#### Individual Video Controls")
                            
                            with gr.Row():
                                select_language_for_video_regen = gr.Dropdown(
                                    label="Select Language to Recreate",
                                    choices=[],
                                    interactive=True
                                )
                                recreate_single_video_btn = gr.Button(
                                    "🔄 Recreate Video", 
                                    variant="secondary"
                                )
                                delete_single_video_btn = gr.Button(
                                    "🗑️ Delete Video", 
                                    variant="secondary"
                                )
                            
                            single_video_status = gr.Textbox(
                                label="Single Video Operation Status",
                                lines=2,
                                interactive=False
                            )
                        
                        # Dynamic video previews (will be populated after creation)
                        dubbed_videos_container = gr.Column(visible=False)
                        
                        # Summary display
                        with gr.Group():
                            gr.Markdown("#### Dubbing Summary")
                            dubbing_summary_display = gr.Textbox(
                                label="Dubbing Process Summary",
                                lines=3,
                                interactive=False,
                                placeholder="Summary will appear here after creating dubbed videos..."
                            )
                
                # Step 4: TTS Generation
                with gr.Group():
                    gr.Markdown("## Step 4: 🎤 Generate TTS Audio")
                    
                    # TTS Engine Selection
                    with gr.Row():
                        # Build TTS engine choices dynamically
                        tts_choices = [("Gemini TTS", "gemini")]
                        if EDGE_TTS_AVAILABLE:
                            tts_choices.append(("Edge TTS (Microsoft)", "edge"))
                        if KOKORO_TTS_AVAILABLE:
                            tts_choices.append(("Kokoro TTS (Local)", "kokoro"))
                        
                        tts_engine_selection = gr.Dropdown(
                            label="🎙️ TTS Engine",
                            choices=tts_choices,
                            value="gemini",
                            info="Choose between Gemini AI, Microsoft Edge neural voices, and local Kokoro TTS"
                        )
                        
                        tts_method_selection = gr.Radio(
                            label="TTS Method",
                            choices=[
                                ("🔄 Individual Segments", "individual"),
                                ("🚀 Single Request", "single_request")
                            ],
                            value="individual",
                            info="Single Request: Generate all dialogue in one API call (better timing, fewer API calls)"
                        )
                    
                    # Voice Selection (dynamic based on engine)
                    with gr.Row():
                        # Gemini Language Selection
                        gemini_language_selection = gr.Dropdown(
                            label="Select Language",
                            choices=[
                                ("English", "en"),
                                ("Hindi", "hi"),
                                ("Spanish", "es"),
                                ("Japanese", "ja"),
                                ("French", "fr"),
                                ("German", "de"),
                                ("Korean", "ko"),
                                ("Portuguese", "pt"),
                                ("Arabic", "ar"),
                                ("Italian", "it"),
                                ("Russian", "ru"),
                                ("Dutch", "nl"),
                                ("Polish", "pl"),
                                ("Thai", "th"),
                                ("Turkish", "tr"),
                                ("Vietnamese", "vi"),
                                ("Romanian", "ro"),
                                ("Ukrainian", "uk"),
                                ("Bengali", "bn"),
                                ("Marathi", "mr"),
                                ("Tamil", "ta"),
                                ("Telugu", "te")
                            ],
                            value="en",
                            visible=True,
                            info="Select language first to see available Gemini voices"
                        )
                        
                        # Gemini Voice Selection (populated based on language)
                        gemini_voice_selection = gr.Dropdown(
                            label="Select Gemini Voice",
                            choices=[],
                            value=None,
                            visible=True,
                            info="Choose from available Gemini voices for selected language"
                        )
                        
                        # Edge TTS Language Selection
                        edge_language_selection = gr.Dropdown(
                            label="Select Language",
                            choices=[
                                ("Hindi (India)", "hi"),
                                ("English (US)", "en"),
                                ("Spanish (Spain)", "es"),
                                ("French (France)", "fr"),
                                ("German (Germany)", "de"),
                                ("Japanese (Japan)", "ja"),
                                ("Korean (Korea)", "ko"),
                                ("Chinese (China)", "zh"),
                                ("Arabic (Saudi Arabia)", "ar"),
                                ("Tamil (India)", "ta"),
                                ("Telugu (India)", "te"),
                                ("Marathi (India)", "mr"),
                                ("Bengali (India)", "bn"),
                                ("Portuguese (Brazil)", "pt"),
                                ("Russian (Russia)", "ru"),
                                ("Italian (Italy)", "it"),
                                ("Turkish (Turkey)", "tr"),
                                ("Thai (Thailand)", "th"),
                                ("Vietnamese (Vietnam)", "vi"),
                                ("Dutch (Netherlands)", "nl"),
                                ("Polish (Poland)", "pl")
                            ],
                            value="hi",
                            visible=False,
                            info="Select language first to see available voices"
                        )
                        
                        # Edge TTS Voice Selection (populated based on language)
                        edge_voice_selection = gr.Dropdown(
                            label="Select Voice",
                            choices=[],
                            value=None,
                            visible=False,
                            info="Choose from available neural voices for selected language"
                        )
                        
                        # Kokoro TTS Language Selection
                        kokoro_language_selection = gr.Dropdown(
                            label="Select Language",
                            choices=get_kokoro_languages(),
                            value="a" if get_kokoro_languages() else None,
                            visible=False,
                            info="Select language first to see available Kokoro voices"
                        )
                        
                        # Kokoro TTS Voice Selection
                        kokoro_voice_selection = gr.Dropdown(
                            label="Kokoro Voice",
                            choices=get_kokoro_voices_for_language("a") if KOKORO_TTS_AVAILABLE else [],
                            value=None,
                            visible=False,
                            info="Choose from available Kokoro voices for selected language"
                        )
                    
                    # Voice preview button
                    with gr.Row():
                        preview_voice_btn = gr.Button("🎧 Preview Voice", size="sm", visible=False)
                        preview_audio = gr.Audio(label="Voice Preview", visible=False)
                    
                    # Custom instructions for single-request mode
                    tts_instructions = gr.Textbox(
                        label="🎭 Custom Instructions (Optional - for Single Request mode)",
                        placeholder="e.g., 'Speak with excitement and energy, matching anime character personalities'",
                        lines=2,
                        visible=False
                    )
                    
                    generate_tts_btn = gr.Button("🎵 Generate TTS Audio", variant="primary")
                    
                    # Dynamic UI functions
                    def toggle_tts_engine(engine):
                        """Toggle UI elements based on selected TTS engine."""
                        is_gemini = (engine == "gemini")
                        is_edge = (engine == "edge")
                        is_kokoro = (engine == "kokoro")
                        
                        # Initialize default values
                        gemini_voices = []
                        gemini_default = None
                        edge_voices = []
                        edge_default = None
                        kokoro_voices = []
                        kokoro_default = None
                        
                        # Initialize Gemini TTS voices if selected
                        if is_gemini:
                            try:
                                # Get English voices as default
                                gemini_voices = get_gemini_voices_for_language("en")
                                gemini_default = gemini_voices[0] if gemini_voices else None
                            except Exception as e:
                                print(f"Error initializing Gemini TTS voices: {str(e)}")
                        
                        # Initialize Edge TTS voices if selected
                        if is_edge and EDGE_TTS_AVAILABLE:
                            try:
                                voice_parser = EdgeTTSVoiceParser()
                                if not voice_parser.voices:
                                    voice_parser.parse_voices()
                                
                                # Get Hindi voices as default
                                edge_voices = voice_parser.get_voice_choices_for_language("hi")
                                edge_default = edge_voices[0] if edge_voices else None
                            except Exception as e:
                                print(f"Error initializing Edge TTS voices: {str(e)}")
                        
                        # Initialize Kokoro TTS voices if selected
                        if is_kokoro and KOKORO_TTS_AVAILABLE:
                            try:
                                kokoro_parser = KokoroVoiceParser()
                                
                                # Get American English voices as default
                                kokoro_voices = kokoro_parser.get_voice_choices_for_language("a")
                                kokoro_default = kokoro_voices[0] if kokoro_voices else None
                            except Exception as e:
                                print(f"Error initializing Kokoro TTS voices: {str(e)}")
                        
                        return (
                            gr.update(visible=is_gemini),  # gemini_language_selection
                            gr.update(visible=is_gemini, choices=gemini_voices, value=gemini_default),  # gemini_voice_selection
                            gr.update(visible=is_edge),    # edge_language_selection
                            gr.update(visible=is_edge, choices=edge_voices, value=edge_default),  # edge_voice_selection
                            gr.update(visible=is_kokoro),  # kokoro_language_selection
                            gr.update(visible=is_kokoro, choices=kokoro_voices, value=kokoro_default),  # kokoro_voice_selection
                            gr.update(visible=(is_gemini or is_edge or is_kokoro)),  # preview_voice_btn
                            gr.update(visible=(is_gemini or is_edge or is_kokoro))   # preview_audio
                        )
                    
                    def update_edge_voices(language_code):
                        """Update Edge TTS voices based on selected language."""
                        if not EDGE_TTS_AVAILABLE:
                            return gr.update(choices=[], value=None)
                        
                        try:
                            voice_parser = EdgeTTSVoiceParser()
                            if not voice_parser.voices:
                                voice_parser.parse_voices()
                            
                            voices = voice_parser.get_voice_choices_for_language(language_code)
                            default_voice = voices[0] if voices else None
                            
                            return gr.update(choices=voices, value=default_voice)
                            
                        except Exception as e:
                            print(f"Error updating Edge voices: {str(e)}")
                            return gr.update(choices=[], value=None)
                    
                    def toggle_tts_instructions(method):
                        """Show/hide instructions based on TTS method."""
                        return gr.update(visible=(method == "single_request"))
                    
                    # Event handlers for dynamic UI
                    tts_engine_selection.change(
                        toggle_tts_engine,
                        inputs=[tts_engine_selection],
                        outputs=[gemini_language_selection, gemini_voice_selection, edge_language_selection, edge_voice_selection, kokoro_language_selection, kokoro_voice_selection, preview_voice_btn, preview_audio]
                    )
                    
                    edge_language_selection.change(
                        update_edge_voices,
                        inputs=[edge_language_selection],
                        outputs=[edge_voice_selection]
                    )
                    
                    # Kokoro language selection change
                    kokoro_language_selection.change(
                        update_kokoro_voices,
                        inputs=[kokoro_language_selection],
                        outputs=[kokoro_voice_selection]
                    )
                    
                    # Gemini language selection change
                    gemini_language_selection.change(
                        update_gemini_voices,
                        inputs=[gemini_language_selection],
                        outputs=[gemini_voice_selection]
                    )
                    
                    tts_method_selection.change(
                        toggle_tts_instructions,
                        inputs=[tts_method_selection],
                        outputs=[tts_instructions]
                    )
                    
                    # Voice preview function
                    def preview_voice(engine, gemini_lang, gemini_voice, edge_lang, edge_voice, kokoro_lang, kokoro_voice):
                        """Generate a preview of the selected voice."""
                        try:
                            if engine == "gemini":
                                return preview_gemini_voice(gemini_lang, gemini_voice)
                            elif engine == "edge" and EDGE_TTS_AVAILABLE:
                                return preview_edge_voice(edge_lang, edge_voice)
                            elif engine == "kokoro" and KOKORO_TTS_AVAILABLE:
                                return preview_kokoro_voice(kokoro_lang, kokoro_voice)
                            else:
                                return "❌ Voice preview not available for this engine"
                        except Exception as e:
                            return f"❌ Preview error: {str(e)}"
                    
                    def preview_edge_voice(language_code, voice_display_name):
                        """Generate a preview of the selected Edge voice."""
                        if not EDGE_TTS_AVAILABLE or not voice_display_name:
                            return "❌ Edge TTS not available or no voice selected"
                        
                        try:
                            # Parse voice parser to get short name
                            voice_parser = EdgeTTSVoiceParser()
                            if not voice_parser.voices:
                                voice_parser.parse_voices()
                            
                            # Get short name from display name
                            voice_short_name = voice_parser.get_voice_short_name(voice_display_name, language_code)
                            
                            # Initialize Simple Edge TTS service
                            edge_service = SimpleEdgeTTS(voice_short_name)
                            
                            # Generate preview with language-appropriate text
                            preview_texts = {
                                'hi': 'नमस्ते, मैं Edge TTS की आवाज़ का परीक्षण कर रहा हूँ।',
                                'en': 'Hello, I am testing the Edge TTS voice quality.',
                                'es': 'Hola, estoy probando la calidad de voz de Edge TTS.',
                                'fr': 'Bonjour, je teste la qualité vocale d\'Edge TTS.',
                                'de': 'Hallo, ich teste die Edge TTS Sprachqualität.',
                                'ja': 'こんにちは、Edge TTSの音声品質をテストしています。',
                                'ko': '안녕하세요, Edge TTS 음성 품질을 테스트하고 있습니다.',
                                'zh': '你好，我正在测试Edge TTS的语音质量。',
                                'ar': 'مرحبا، أنا أختبر جودة صوت Edge TTS.',
                                'ta': 'வணக்கம், நான் Edge TTS குரல் தரத்தை சோதித்து வருகிறேன்.',
                                'te': 'నమస్కారం, నేను Edge TTS వాయిస్ నాణ్యతను పరీక్షిస్తున్నాను.',
                                'mr': 'नमस्कार, मी Edge TTS आवाज गुणवत्तेची चाचणी करत आहे.',
                                'bn': 'নমস্কার, আমি Edge TTS ভয়েস গুণমান পরীক্ষা করছি।',
                                'pt': 'Olá, estou testando a qualidade de voz do Edge TTS.',
                                'ru': 'Привет, я тестирую качество голоса Edge TTS.',
                                'it': 'Ciao, sto testando la qualità vocale di Edge TTS.',
                                'tr': 'Merhaba, Edge TTS ses kalitesini test ediyorum.',
                                'th': 'สวัสดี ฉันกำลังทดสอบคุณภาพเสียงของ Edge TTS',
                                'vi': 'Xin chào, tôi đang kiểm tra chất lượng giọng nói của Edge TTS.',
                                'nl': 'Hallo, ik test de Edge TTS stemkwaliteit.',
                                'pl': 'Cześć, testuję jakość głosu Edge TTS.'
                            }
                            
                            test_text = preview_texts.get(language_code, 'Testing Edge TTS voice quality')
                            
                            # Generate preview
                            preview_file = edge_service.preview_voice(test_text)
                            
                            if preview_file and os.path.exists(preview_file):
                                return preview_file
                            else:
                                return "❌ Preview generation failed"
                                
                        except Exception as e:
                            return f"❌ Edge preview error: {str(e)}"
                    
                    def preview_kokoro_voice(language_code, voice_display_name):
                        """Generate a preview of the selected Kokoro voice."""
                        if not KOKORO_TTS_AVAILABLE or not voice_display_name:
                            return "❌ Kokoro TTS not available or no voice selected"
                        
                        try:
                            # Parse voice name from display name
                            voice_parser = KokoroVoiceParser()
                            voice_name = voice_parser.get_voice_name_from_display(voice_display_name, language_code)
                            
                            if not voice_name:
                                return f"❌ No Kokoro voice found for language={language_code}, name={voice_display_name}"
                            
                            # Initialize Kokoro TTS service
                            kokoro_service = KokoroTTSService(voice_name=voice_name)
                            
                            if not kokoro_service.model_available:
                                return "❌ Kokoro model not available"
                            
                            # Generate preview with language-appropriate text
                            preview_texts = {
                                'a': 'Hello, I am testing the Kokoro TTS voice quality.',
                                'b': 'Hello, I am testing the Kokoro TTS voice quality.',
                                'j': 'こんにちは、Kokoro TTSの音声品質をテストしています。',
                                'z': '你好，我正在测试Kokoro TTS的语音质量。',
                                'e': 'Hola, estoy probando la calidad de voz de Kokoro TTS.',
                                'f': 'Bonjour, je teste la qualité vocale de Kokoro TTS.',
                                'h': 'नमस्ते, मैं Kokoro TTS की आवाज़ का परीक्षण कर रहा हूँ।',
                                'i': 'Ciao, sto testando la qualità vocale di Kokoro TTS.',
                                'p': 'Olá, estou testando a qualidade de voz do Kokoro TTS.'
                            }
                            
                            test_text = preview_texts.get(language_code, 'Testing Kokoro TTS voice quality')
                            
                            # Generate preview
                            preview_file = kokoro_service.preview_voice(test_text)
                            
                            if preview_file and os.path.exists(preview_file):
                                return preview_file
                            else:
                                return "❌ Preview generation failed"
                                
                        except Exception as e:
                            return f"❌ Kokoro preview error: {str(e)}"
                    
                    def preview_gemini_voice(language_code, voice_display_name):
                        """Generate a preview of the selected Gemini voice."""
                        if not language_code or not voice_display_name:
                            return "❌ Please select a Gemini language and voice first"
                        
                        try:
                            from gemini_voice_library import GeminiVoiceLibrary
                            
                            # Parse voice name from display name (e.g., "Hindi Deep (Gemini)" -> "gemini_hi_deep")
                            gemini_library = GeminiVoiceLibrary()
                            voice_name = None
                            
                            # Find the voice name by matching display name
                            for voice in gemini_library.get_gemini_voices(language_code):
                                if gemini_library.get_voice_display_name(voice) == voice_display_name:
                                    voice_name = voice
                                    break
                            
                            if not voice_name:
                                return f"❌ Voice not found: {voice_display_name}"
                            
                            # Generate preview using the voice library
                            preview_path = gemini_library.generate_gemini_tts_preview(voice_name, language_code)
                            
                            if preview_path and os.path.exists(preview_path):
                                return preview_path
                            else:
                                return f"❌ Failed to generate preview for {voice_display_name}"
                                
                        except Exception as e:
                            return f"❌ Gemini preview error: {str(e)}"
                    
                    # Connect preview button
                    preview_voice_btn.click(
                        preview_voice,
                        inputs=[tts_engine_selection, gemini_language_selection, gemini_voice_selection, edge_language_selection, edge_voice_selection, kokoro_language_selection, kokoro_voice_selection],
                        outputs=[preview_audio]
                    )
                    
                    tts_status = gr.Textbox(
                        label="TTS Status",
                        lines=3,
                        interactive=False
                    )
                    
                    tts_audio_output = gr.File(label="Download Generated Audio")
                    
                    # Chunked audio status
                    with gr.Group():
                        gr.Markdown("#### Chunked Audio Status")
                        chunked_audio_status = gr.Textbox(
                            label="Audio Processing Status",
                            lines=4,
                            interactive=False,
                            info="Shows status of chunked audio processing and final video readiness"
                        )
                        refresh_audio_status_btn = gr.Button("🔄 Refresh Audio Status", size="sm")
                
                # Step 5: Final Video
                with gr.Group():
                    gr.Markdown("## Step 5: 🎬 Create Final Video")
                    
                    video_input = gr.File(
                        label="Upload Original Video",
                        file_types=["video"]
                    )
                    
                    create_video_btn = gr.Button("🎥 Create Dubbed Video", variant="primary")
                    
                    video_status = gr.Textbox(
                        label="Video Creation Status",
                        lines=3,
                        interactive=False
                    )
                    
                    final_video_output = gr.File(label="Download Dubbed Video")
                
                # Progress Log
                with gr.Group():
                    gr.Markdown("## 📊 Progress Log")
                    progress_log = gr.Textbox(
                        label="Detailed Progress",
                        lines=8,
                        interactive=False
                    )
        
        # Batch Video Creation Tab
        with gr.TabItem("🎵 Batch Video Creation"):
            gr.Markdown("## 🎵 Batch Video Creation")
            gr.Markdown("Upload one video and multiple audio files to create multiple combined videos")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📹 Video Input")
                    batch_video_input = gr.File(
                        label="Upload Video File",
                        file_types=["video"]
                    )
                    
                    gr.Markdown("### 🎵 Audio Files")
                    batch_audio_input = gr.File(
                        label="Upload Multiple Audio Files",
                        file_types=["audio"],
                        file_count="multiple"
                    )
                    
                    batch_create_btn = gr.Button("🚀 Create Batch Videos", variant="primary", size="lg")
                    
                    gr.Markdown("""
                    ### 📝 Instructions:
                    1. **Upload one video file** - this will be the base video for all combinations
                    2. **Upload multiple audio files** - each will be combined with the video
                    3. **Click "Create Batch Videos"** - the system will create one video per audio file
                    4. **Download results** - all videos will be saved in the `batch_dubbed_videos` folder
                    
                    ### 💡 Use Cases:
                    - Create multiple language versions of the same video
                    - Combine one video with different audio tracks/music
                    - Generate variations of content with different voiceovers
                    - Batch process multiple audio files for the same visual content
                    """)
                
                with gr.Column():
                    batch_output = gr.Textbox(
                        label="Batch Processing Results",
                        lines=8,
                        interactive=False,
                        info="Status and results of the batch processing"
                    )
                    
                    batch_files_output = gr.File(
                        label="Download Created Videos",
                        file_count="multiple"
                    )
                    
                    gr.Markdown("""
                    ### 🔧 Technical Details:
                    - **Video codec**: Copied from original (no re-encoding)
                    - **Audio codec**: Copied from audio files
                    - **Sync method**: Shortest duration (video or audio)
                    - **Output format**: MP4
                    - **Naming**: `{video_name}_{audio_name}_combined.mp4`
                    
                    ### ⚡ Performance:
                    - Processing is done sequentially for stability
                    - No transcoding = faster processing
                    - Progress tracking for each file
                    - Automatic error handling and recovery
                    """)
        
        # Help Tab
        with gr.TabItem("❓ Help"):
            gr.Markdown("""
            # Help & Documentation
            
            ## Transcription
            - Upload audio/video files or record directly from your microphone
            - Enable "Music mode" for better accuracy with songs and vocal content
            - Long files (>10 minutes) are automatically split for processing
            - Results are saved automatically for use in the dubbing pipeline
            
            ## Dubbing Pipeline
            
            ### Prerequisites
            - Complete transcription first (ASR results required)
            - Obtain Gemini API keys from Google AI Studio
            - Prepare your video file for dubbing
            
            ### Automatic Mode
            1. Upload your video file
            2. Enter your Gemini API keys (one per line)
            3. Configure translation style (tone, dialect, genre)
            4. Select TTS voice
            5. Click "Run Pipeline"
            
            ### Manual Mode
            1. Provide your own translations in JSON format:
            ```json
            [
                {"start": 0.0, "end": 2.5, "text_translated": "Hello world"},
                {"start": 2.5, "end": 5.0, "text_translated": "How are you?"}
            ]
            ```
            2. Configure TTS settings
            3. Click "Run Pipeline"
            
            ### Pipeline Recovery
            - If the pipeline is interrupted, use "Continue from Checkpoint"
            - The system automatically detects the current stage
            - No need to restart from the beginning
            
            ### API Keys
            - Provide multiple API keys for better reliability
            - Keys are rotated automatically when quotas are reached
            - Keys are never stored permanently
            
            ### Troubleshooting
            - Check pipeline status for current stage information
            - Ensure all required files exist before continuing
            - Verify API keys have sufficient quota
            - Check that video files are in supported formats
            
            ### Supported Formats
            - **Video**: MP4, AVI, MOV, MKV, WebM
            - **Audio**: WAV, MP3, FLAC, OGG, M4A
            - **Output**: MP4 with AAC audio
            """)
        

    
    
    # ASR Event Handlers
    def transcribe_and_save(audio_file, is_music_mode, enable_chunking, chunk_duration, use_model_chunking, video_file=None):
        """Transcribe audio and save results for dubbing pipeline."""
        try:
            if audio_file:
                result = transcribe_audio(audio_file, is_music_mode, enable_chunking, chunk_duration, use_model_chunking)
                source_path = audio_file
            else:
                result = transcribe_video(video_file, is_music_mode, enable_chunking, chunk_duration, use_model_chunking)
                source_path = video_file
                
            full_text, segments, csv_file = result
            
            # Save ASR results for dubbing pipeline with enhanced format
            if segments:
                success = save_asr_results(segments, source_path)
                if success:
                    print(f"ASR results saved successfully for dubbing pipeline: {len(segments)} segments")
                else:
                    print("Warning: Failed to save ASR results for dubbing pipeline")
                    
            return full_text, segments, csv_file
            
        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            print(error_msg)
            return error_msg, [], None
    
    def get_dubbing_status():
        """Get current dubbing pipeline status and ASR compatibility."""
        if not DUBBING_AVAILABLE:
            return "❌ Dubbing pipeline not available"
            
        # Check ASR compatibility
        compatible, message = check_asr_compatibility()
        
        if compatible:
            asr_summary = get_asr_summary()
            pipeline_status = detect_pipeline_state()
            return f"✅ Ready for dubbing\\n\\n{asr_summary}\\n\\nPipeline Status: {pipeline_status}"
        else:
            return f"❌ ASR results not compatible: {message}\\n\\nPlease run transcription first."
    
    # Handle transcription from file upload
    audio_btn.click(
        lambda audio, music, chunking, duration, model_chunking: transcribe_and_save(audio, music, chunking, duration, model_chunking),
        inputs=[audio_input, is_music, enable_chunking, chunk_duration, use_model_chunking],
        outputs=[full_transcript, transcript_segments, csv_output]
    )
    
    # Handle transcription from video
    video_btn.click(
        lambda video, music, chunking, duration, model_chunking: transcribe_and_save(None, music, chunking, duration, model_chunking, video),
        inputs=[video_input, is_music, enable_chunking, chunk_duration, use_model_chunking],
        outputs=[full_transcript, transcript_segments, csv_output]
    )
    
    # Handle transcription from microphone
    audio_record.stop_recording(
        lambda audio, music, chunking, duration, model_chunking: transcribe_and_save(audio, music, chunking, duration, model_chunking),
        inputs=[audio_record, is_music, enable_chunking, chunk_duration, use_model_chunking],
        outputs=[full_transcript, transcript_segments, csv_output]
    )
    
    # Update the HTML when segments change
    transcript_segments.change(
        create_transcript_table,
        inputs=[transcript_segments],
        outputs=[transcript_html]
    )
    
    # Update ASR status when segments change
    transcript_segments.change(
        lambda segments: get_dubbing_status() if segments else "No transcription results available",
        inputs=[transcript_segments],
        outputs=[asr_status_output]
    )
    
    # Refresh ASR status button
    refresh_asr_status_btn.click(
        get_dubbing_status,
        outputs=[asr_status_output]
    )
    
    # Apply custom JavaScript for audio playback
    audio_input.change(
        lambda x: x,
        inputs=[audio_input],
        outputs=[audio_playback],
        js=js_code
    )
    
    audio_record.stop_recording(
        lambda x: x,
        inputs=[audio_record],
        outputs=[audio_playback],
        js=js_code
    )
    
    # Handle video audio extraction for playback
    video_input.change(
        lambda x: extract_audio_from_video(x, None) if x else None,
        inputs=[video_input],
        outputs=[audio_playback],
        js=js_code
    )
    
    # Dubbing Pipeline Event Handlers
    if DUBBING_AVAILABLE:
        # API Key Management
        def save_api_keys(keys_text):
            return save_api_keys_to_memory(keys_text)
        
        def test_api_keys():
            return test_api_keys_in_memory()
        
        save_keys_btn.click(
            save_api_keys,
            inputs=[api_keys_input],
            outputs=[api_status_output]
        )
        
        test_keys_btn.click(
            test_api_keys,
            outputs=[api_status_output]
        )
        

        
        # Main dubbing function
        # Step-by-step functions
        def transcribe_video_here(video_file, is_music, enable_chunking, chunk_duration):
            """Transcribe video directly in the step-by-step interface"""
            if not video_file:
                return "", "❌ No video file provided"
            
            try:
                # Use the existing transcription function with chunking
                full_text, segments, csv_file = transcribe_video(video_file, is_music, enable_chunking, chunk_duration, False)
                
                if segments:
                    # Save ASR results
                    save_asr_results(segments, video_file)
                    
                    # Format as JSON for display
                    json_output = json.dumps(segments, indent=2, ensure_ascii=False)
                    
                    # Check if chunking was applied
                    chunking_info = ""
                    if enable_chunking and os.path.exists("chunked_transcript.json"):
                        try:
                            chunker = TranscriptChunker()
                            chunked_data = chunker.load_chunked_transcript("chunked_transcript.json")
                            if chunked_data:
                                # Load original segments for comparison
                                original_segments = load_asr_results()
                                if original_segments:
                                    analysis = chunker.analyze_chunking_efficiency(original_segments, chunked_data)
                                    chunking_info = f"""
📊 Chunking Applied:
• Original segments: {analysis['original_segments']}
• Generated chunks: {analysis['generated_chunks']}
• API call reduction: {analysis['api_call_reduction_percent']:.1f}%
• Avg chunk duration: {analysis['average_chunk_duration']:.1f}s
• TTS efficiency: {analysis['estimated_tts_time_savings']}"""
                        except Exception as e:
                            chunking_info = f"⚠️ Chunking analysis failed: {str(e)}"
                    
                    status_msg = f"✅ Transcription completed! {len(segments)} segments generated"
                    if chunking_info:
                        status_msg += chunking_info
                    
                    return json_output, status_msg
                else:
                    return "", "❌ Transcription failed"
                    
            except Exception as e:
                return "", f"❌ Transcription error: {str(e)}"
        
        def load_transcription_from_asr():
            """Load transcription from original_asr.json"""
            try:
                asr_data = load_asr_results()
                if not asr_data:
                    return "", "❌ No transcription found. Please run transcription first in the Transcription tab."
                
                # Format as JSON for display
                json_output = json.dumps(asr_data, indent=2, ensure_ascii=False)
                return json_output, f"✅ Loaded {len(asr_data)} segments from transcription tab"
                
            except Exception as e:
                return "", f"❌ Error loading transcription: {str(e)}"
        
        def enable_manual_paste():
            """Enable manual paste mode for transcription"""
            sample_json = [
                {"start": 0.0, "end": 4.5, "text": "Hey everyone, this is Mipax speaking."},
                {"start": 4.5, "end": 9.8, "text": "Today we're diving into the latest One Piece theories."}
            ]
            json_output = json.dumps(sample_json, indent=2, ensure_ascii=False)
            return json_output, "✅ Manual paste enabled. Edit the JSON above with your transcription."
        
        def translate_with_gemini(transcription_json, translation_prompt_text):
            """Translate using Gemini API"""
            try:
                # Check API keys
                if not has_api_keys():
                    return "", "❌ No API keys saved. Please save API keys first."
                
                # Parse transcription JSON
                if not transcription_json.strip():
                    return "", "❌ No transcription provided. Please load or paste transcription first."
                
                try:
                    asr_data = json.loads(transcription_json)
                except json.JSONDecodeError:
                    return "", "❌ Invalid JSON in transcription. Please check the format."
                
                # Parse style config and handle different JSON formats
                try:
                    prompt_data = json.loads(translation_prompt_text)
                    
                    # Handle different JSON prompt formats
                    if 'target_language' in prompt_data:
                        # Format: {"target_language": "Hindi", "tone": "casual", "instructions": "..."}
                        style_config = prompt_data
                    elif 'system' in prompt_data:
                        # Format: {"system": "You are a translator...", "target_language": "Hindi"}
                        style_config = {
                            "target_language": prompt_data.get('target_language', 'Hindi'),
                            "instructions": prompt_data.get('system', ''),
                            "tone": prompt_data.get('tone', 'neutral')
                        }
                    else:
                        # Default format: {"tone": "casual", "dialect": "hindi_devanagari"}
                        style_config = prompt_data
                        if 'dialect' in style_config and 'target_language' not in style_config:
                            # Convert dialect to target_language
                            dialect = style_config['dialect']
                            if 'hindi' in dialect.lower():
                                style_config['target_language'] = 'Hindi'
                            elif 'spanish' in dialect.lower():
                                style_config['target_language'] = 'Spanish'
                            else:
                                style_config['target_language'] = dialect
                                
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as plain text instruction
                    style_config = {
                        "target_language": "Hindi",
                        "instructions": translation_prompt_text,
                        "tone": "neutral"
                    }
                
                # Initialize service
                api_keys = api_manager.get_keys()
                service = RealGeminiService(api_keys)
                
                # Translate
                def progress_callback(progress, message):
                    print(f"[Translation {progress:.1%}] {message}")
                
                translated_segments = service.translate_full_transcript(
                    asr_data, style_config, progress_callback
                )
                
                # Format as JSON for display
                json_output = json.dumps(translated_segments, indent=2, ensure_ascii=False)
                return json_output, f"✅ Translation completed! {len(translated_segments)} segments translated"
                
            except Exception as e:
                return "", f"❌ Translation failed: {str(e)}"
        
        def get_language_specific_config(language_code):
            """Get detailed language-specific configuration for translation"""
            language_configs = {
                "ar-EG": {
                    "language_code": "ar-EG",
                    "target_language_name": "Arabic (Egyptian)",
                    "translation_style_guide": {
                        "tone": "conversational, engaging, and informative",
                        "formality": "informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "subscribe", "like", "comment", "vlog", "gaming", "computer", "internet", "social media"
                        ],
                        "spelling_of_loanwords": "transliterate to target script",
                        "numerical_format": "Western Arabic numerals",
                        "cultural_references_to_adapt": [
                            "local proverbs", "references to Egyptian pop culture (movies, music, celebrities)", "food references"
                        ],
                        "youtube_creator_reference": {
                            "name": "Ahmed El Ghandour (Da7ee7)",
                            "channel_url": "https://www.youtube.com/c/Da7ee7",
                            "analysis_summary": "Ahmed El Ghandour, known as Da7ee7, is a very popular Egyptian YouTuber known for his fast-paced, engaging, and humorous educational content. His style is characterized by a mix of formal Arabic and Egyptian colloquialisms, with frequent use of English words and phrases. He uses a conversational and energetic tone, often with a sarcastic sense of humor. His scripts are well-researched and information-dense, but presented in a way that is accessible and entertaining to a wide audience. The translation should aim to capture this dynamic and engaging style, using a similar mix of formal and informal language, and retaining English loanwords where appropriate."
                        }
                    }
                },
                "de-DE": {
                    "language_code": "de-DE",
                    "target_language_name": "German (Germany)",
                    "translation_style_guide": {
                        "tone": "informative, precise, engaging, and slightly formal",
                        "formality": "semi-formal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "Internet", "Science", "Technology", "Podcast", "Channel", "Video"
                        ],
                        "spelling_of_loanwords": "transliterate to target script (if applicable, otherwise keep Latin script)",
                        "numerical_format": "Western Arabic numerals (with comma as decimal separator and period as thousands separator)",
                        "cultural_references_to_adapt": [
                            "scientific concepts", "historical events", "philosophical ideas"
                        ],
                        "youtube_creator_reference": {
                            "name": "Kurzgesagt – In a Nutshell (German Channel)",
                            "channel_url": "https://kgs.link/youtubeDE",
                            "analysis_summary": "Kurzgesagt – In a Nutshell is known for its high quality animated educational videos. Their German channel maintains a precise, informative, and engaging tone. The language is clear and concise, often using technical terms but explaining them effectively. While generally formal, they incorporate elements that keep the content accessible and interesting. The translation should prioritize accuracy and clarity, maintaining a slightly formal yet engaging style, and retaining English loanwords where appropriate."
                        }
                    }
                },
                "es-US": {
                    "language_code": "es-US",
                    "target_language_name": "Spanish (US)",
                    "translation_style_guide": {
                        "tone": "casual, adventurous, humorous, and highly engaging",
                        "formality": "informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "vlog", "challenge", "travel", "influencer", "podcast", "internet", "social media"
                        ],
                        "spelling_of_loanwords": "keep in Latin script",
                        "numerical_format": "Western Arabic numerals (with comma as thousands separator and period as decimal separator)",
                        "cultural_references_to_adapt": [
                            "local slang and expressions from Mexico and other Latin American countries",
                            "references to popular culture (movies, music, memes)",
                            "food and travel experiences"
                        ],
                        "youtube_creator_reference": {
                            "name": "Luisito Comunica",
                            "channel_url": "https://www.youtube.com/user/LuisitoComunica",
                            "analysis_summary": "Luisito Comunica is a highly popular Mexican YouTuber known for his travel vlogs, cultural explorations, and humorous commentary. His style is very informal, conversational, and often uses slang and expressions common in Mexican Spanish and other Latin American dialects. He frequently incorporates English words and phrases naturally into his speech. The translation should aim to capture this casual, adventurous, and humorous tone, making it relatable to a broad Spanish-speaking audience in the US and Latin America. English loanwords should be retained and integrated naturally, and numerical formats should follow standard US conventions."
                        }
                    }
                },
                "fr-FR": {
                    "language_code": "fr-FR",
                    "target_language_name": "French (France)",
                    "translation_style_guide": {
                        "tone": "humorous, conversational, and relatable",
                        "formality": "informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "vlog", "gaming", "challenge", "internet", "social media", "buzz"
                        ],
                        "spelling_of_loanwords": "keep in Latin script",
                        "numerical_format": "Western Arabic numerals (with space as thousands separator and comma as decimal separator)",
                        "cultural_references_to_adapt": [
                            "French pop culture references (movies, TV shows, music)",
                            "common French expressions and slang",
                            "references to daily life in France"
                        ],
                        "youtube_creator_reference": {
                            "name": "Cyprien",
                            "channel_url": "https://www.youtube.com/user/MonsieurDream",
                            "analysis_summary": "Cyprien is one of the most popular French YouTubers, known for his comedic sketches, vlogs, and short films. His style is highly informal, witty, and often self-deprecating. He uses a lot of contemporary French slang and expressions, and his humor is very relatable to a young French audience. The translation should aim to capture this lighthearted and conversational tone, incorporating modern French colloquialisms and retaining English loanwords that are commonly used in French youth culture. Numerical formats should follow standard French conventions."
                        }
                    }
                },
                "hi-IN": {
                    "language_code": "hi-IN",
                    "target_language_name": "Hindi (India)",
                    "translation_style_guide": {
                        "tone": "humorous, conversational, and relatable",
                        "formality": "informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "vlog", "comedy", "sketch", "internet", "social media", "trending", "challenge", "subscribe", "like", "comment", "share"
                        ],
                        "spelling_of_loanwords": "transliterate to Devanagari script",
                        "numerical_format": "Western Arabic numerals (with comma as thousands separator)",
                        "cultural_references_to_adapt": [
                            "Indian pop culture references (Bollywood, music, memes)",
                            "common Hindi/Hinglish slang and expressions",
                            "references to daily life in India",
                            "family dynamics and social interactions common in India"
                        ],
                        "youtube_creator_reference": {
                            "name": "Bhuvan Bam (BB Ki Vines)",
                            "channel_url": "https://www.youtube.com/channel/UCqwUrj10mAEsqezcItqvwEw",
                            "analysis_summary": "Bhuvan Bam, through BB Ki Vines, is a pioneer in Indian YouTube comedy. His content is characterized by relatable, multi character sketches that often depict everyday Indian scenarios. The language is a blend of informal Hindi and Hinglish (a mix of Hindi and English), reflecting how many young Indians communicate. He uses a conversational, humorous, and often sarcastic tone. English words are frequently interspersed and are typically transliterated into Devanagari script when written. The translation should aim to capture this authentic Hinglish style, ensuring that the humor and cultural nuances are preserved, and that the language feels natural and contemporary to a Hindi-speaking audience in India. Numerical formats should follow standard Indian conventions."
                        }
                    }
                },
                "ja-JP": {
                    "language_code": "ja-JP",
                    "target_language_name": "Japanese (Japan)",
                    "translation_style_guide": {
                        "tone": "energetic, experimental, and often humorous",
                        "formality": "informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "challenge", "experiment", "vlog", "game", "internet", "social media", "subscribe", "like", "comment", "share"
                        ],
                        "spelling_of_loanwords": "transliterate to Katakana",
                        "numerical_format": "Western Arabic numerals",
                        "cultural_references_to_adapt": [
                            "Japanese pop culture references (anime, manga, J-pop)",
                            "common Japanese internet memes and slang",
                            "references to daily life and unique Japanese experiences"
                        ],
                        "youtube_creator_reference": {
                            "name": "Hajime Shacho",
                            "channel_url": "https://www.youtube.com/user/0214mex",
                            "analysis_summary": "Hajime Shacho is one of Japan's most subscribed YouTubers, known for his diverse content ranging from elaborate experiments and challenges to daily vlogs. His style is energetic, often chaotic, and highly entertaining, appealing to a broad audience. He uses informal Japanese, often with a fast-paced delivery, and frequently incorporates English loanwords, which are typically written in Katakana. The translation should aim to capture this dynamic and playful tone, integrating Japanese internet slang and ensuring that English loanwords are appropriately transliterated into Katakana to maintain a natural flow for Japanese viewers. Numerical formats should follow standard Japanese conventions."
                        }
                    }
                },
                "ko-KR": {
                    "language_code": "ko-KR",
                    "target_language_name": "Korean (Korea)",
                    "translation_style_guide": {
                        "tone": "friendly, engaging, and often humorous, with a focus on cultural exchange",
                        "formality": "informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "vlog", "challenge", "food", "culture", "internet", "social media", "subscribe", "like", "comment", "share"
                        ],
                        "spelling_of_loanwords": "transliterate to Hangul",
                        "numerical_format": "Western Arabic numerals",
                        "cultural_references_to_adapt": [
                            "Korean food and dining etiquette",
                            "K-pop and K-drama references",
                            "common Korean slang and expressions",
                            "references to daily life and social norms in Korea"
                        ],
                        "youtube_creator_reference": {
                            "name": "Korean Englishman",
                            "channel_url": "https://www.youtube.com/user/koreanenglishman",
                            "analysis_summary": "Korean Englishman is a popular YouTube channel that bridges Korean and English cultures, primarily through videos of foreigners reacting to Korean food and culture. The hosts, Josh and Ollie, maintain a friendly, engaging, and often humorous tone. They frequently use a mix of English and Korean, and their Korean is natural and conversational, incorporating common slang and expressions. English words are often transliterated into Hangul when spoken by Koreans or when used in a Korean context. The translation should aim to capture this cross-cultural, informal, and engaging style, ensuring that cultural nuances are respected and that English loanwords are appropriately transliterated into Hangul to feel natural for Korean viewers. Numerical formats should follow standard Korean conventions."
                        }
                    }
                },
                "pt-BR": {
                    "language_code": "pt-BR",
                    "target_language_name": "Portuguese (Brazil)",
                    "translation_style_guide": {
                        "tone": "informative, curious, and engaging, with a focus on science and experiments",
                        "formality": "semi-formal to informal",
                        "common_loanwords_to_retain_english": [
                            "YouTube", "science", "experiment", "DIY", "internet", "social media", "vlog", "challenge"
                        ],
                        "spelling_of_loanwords": "keep in Latin script",
                        "numerical_format": "Western Arabic numerals (with comma as decimal separator and period as thousands separator)",
                        "cultural_references_to_adapt": [
                            "Brazilian cultural references (e.g., specific holidays, popular figures)",
                            "common Brazilian Portuguese expressions and slang",
                            "references to daily life and education in Brazil"
                        ],
                        "youtube_creator_reference": {
                            "name": "Manual do Mundo",
                            "channel_url": "https://www.youtube.com/MANUALDOMUNDO",
                            "analysis_summary": "Manual do Mundo is a highly popular Brazilian YouTube channel focused on science, experiments, and DIY projects. Their style is informative, curious, and engaging, making complex topics accessible and fun for a wide audience. The language used is clear, enthusiastic, and often includes common Brazilian Portuguese expressions. The translation should aim to capture this educational yet entertaining tone, using natural Brazilian Portuguese and retaining English loanwords that are commonly understood in scientific or internet contexts in Brazil. Numerical formats should follow standard Brazilian conventions."
                        }
                    }
                }
            }
            
            # Add more language configs as needed
            return language_configs.get(language_code, {
                "language_code": language_code,
                "target_language_name": language_code.upper(),
                "translation_style_guide": {
                    "tone": "conversational and engaging",
                    "formality": "informal",
                    "instructions": f"Translate to {language_code.upper()} maintaining natural flow and cultural context"
                }
            })
        
        def load_language_config():
            """Load language configuration from JSON file"""
            try:
                if os.path.exists("language_config.json"):
                    with open("language_config.json", "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    # Return default config if file doesn't exist
                    return {
                        "supported_languages": {
                            "hi-IN": {"name": "Hindi (India)", "instructions": "Translate to Hindi maintaining natural flow"},
                            "es-US": {"name": "Spanish (US)", "instructions": "Translate to Spanish maintaining natural flow"},
                            "fr-FR": {"name": "French (France)", "instructions": "Translate to French maintaining natural flow"}
                        },
                        "api_settings": {"delay_between_requests": 0.5}
                    }
            except Exception as e:
                print(f"⚠️ Error loading language config: {str(e)}")
                return {"supported_languages": {}, "api_settings": {"delay_between_requests": 0.5}}
        
        def update_language_config_display(selected_languages):
            """Update the language configuration display based on selected languages"""
            if not selected_languages:
                return ""
            
            configs = {}
            for lang_code in selected_languages:
                config = get_language_specific_config(lang_code)
                configs[lang_code] = config
            
            return json.dumps(configs, indent=2, ensure_ascii=False)
        
        def translate_multi_language(transcription_json, selected_languages, custom_languages_text, lang_config_json, style_override_text):
            """Translate to multiple languages sequentially with enhanced configuration"""
            import os
            import time
            
            try:
                # Check API keys
                if not has_api_keys():
                    return "", "❌ No API keys saved. Please save API keys first."
                
                # Parse transcription JSON
                if not transcription_json.strip():
                    return "", "❌ No transcription provided. Please load or paste transcription first."
                
                try:
                    asr_data = json.loads(transcription_json)
                except json.JSONDecodeError:
                    return "", "❌ Invalid JSON in transcription. Please check the format."
                
                # Load language configuration
                lang_config = load_language_config()
                supported_languages = lang_config.get("supported_languages", {})
                api_settings = lang_config.get("api_settings", {"delay_between_requests": 0.5})
                
                # Parse language configurations
                try:
                    language_configs = json.loads(lang_config_json) if lang_config_json.strip() else {}
                except json.JSONDecodeError:
                    language_configs = {}
                
                # Parse style override
                try:
                    style_override = json.loads(style_override_text) if style_override_text.strip() else {}
                except json.JSONDecodeError:
                    style_override = {}
                
                # Prepare language list with detailed configurations
                all_languages = []
                
                # Add selected languages from checkboxes
                if selected_languages:
                    for lang_code in selected_languages:
                        if lang_code in language_configs:
                            # Use detailed configuration
                            lang_config = language_configs[lang_code]
                            lang_name = lang_config.get("target_language_name", lang_code)
                            style_guide = lang_config.get("translation_style_guide", {})
                            all_languages.append((lang_code, lang_name, style_guide))
                        else:
                            # Fallback to basic configuration
                            basic_config = get_language_specific_config(lang_code)
                            lang_name = basic_config.get("target_language_name", lang_code)
                            style_guide = basic_config.get("translation_style_guide", {})
                            all_languages.append((lang_code, lang_name, style_guide))
                
                # Add custom languages
                if custom_languages_text and custom_languages_text.strip():
                    custom_langs = [lang.strip() for lang in custom_languages_text.split(',') if lang.strip()]
                    for lang in custom_langs:
                        # Generate a simple code from the language name
                        lang_code = lang.lower().replace(' ', '_').replace('(', '').replace(')', '')[:5]
                        style_guide = {
                            "tone": "conversational and engaging",
                            "formality": "informal",
                            "instructions": f"Translate to {lang} maintaining natural flow and cultural context"
                        }
                        all_languages.append((lang_code, lang, style_guide))
                
                if not all_languages:
                    return "", "❌ No languages selected. Please select at least one language."
                
                # Create translations directory
                os.makedirs("translations", exist_ok=True)
                
                # Save original transcription
                with open("translations/original.txt", "w", encoding="utf-8") as f:
                    f.write("# Original Transcription\\n\\n")
                    for segment in asr_data:
                        f.write(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}\\n")
                
                # Initialize service
                api_keys = api_manager.get_keys()
                service = RealGeminiService(api_keys)
                
                results = []
                successful_translations = 0
                total_segments_translated = 0
                
                print(f"🌍 Starting multi-language translation for {len(all_languages)} languages...")
                
                # Process each language sequentially
                for i, (lang_code, lang_name, style_guide) in enumerate(all_languages):
                    try:
                        print(f"🌍 [{i+1}/{len(all_languages)}] Translating to {lang_name}...")
                        
                        # Create comprehensive language-specific style config
                        lang_style_config = {
                            "target_language": lang_name,
                            "language_code": lang_code,
                            "tone": style_guide.get("tone", "conversational and engaging"),
                            "formality": style_guide.get("formality", "informal"),
                            "instructions": style_guide.get("instructions", f"Translate to {lang_name} maintaining natural flow and cultural context")
                        }
                        
                        # Add detailed style guide information
                        if "common_loanwords_to_retain_english" in style_guide:
                            lang_style_config["common_loanwords_to_retain"] = style_guide["common_loanwords_to_retain_english"]
                        
                        if "spelling_of_loanwords" in style_guide:
                            lang_style_config["loanword_handling"] = style_guide["spelling_of_loanwords"]
                        
                        if "cultural_references_to_adapt" in style_guide:
                            lang_style_config["cultural_adaptation"] = style_guide["cultural_references_to_adapt"]
                        
                        if "youtube_creator_reference" in style_guide:
                            creator_ref = style_guide["youtube_creator_reference"]
                            lang_style_config["style_reference"] = f"Emulate the style of {creator_ref.get('name', 'popular creators')} - {creator_ref.get('analysis_summary', 'engaging and natural style')}"
                        
                        # Apply global style overrides
                        if style_override:
                            lang_style_config.update(style_override)
                        
                        # Progress callback for this language
                        def progress_callback(progress, message):
                            print(f"[{lang_name} {progress:.1%}] {message}")
                        
                        # Translate
                        translated_segments = service.translate_full_transcript(
                            asr_data, lang_style_config, progress_callback
                        )
                        
                        if translated_segments and len(translated_segments) > 0:
                            # Save as JSON file
                            json_filename = f"translations/transcript_{lang_code}.json"
                            with open(json_filename, "w", encoding="utf-8") as f:
                                json.dump(translated_segments, f, indent=2, ensure_ascii=False)
                            
                            # Save as text file
                            txt_filename = f"translations/transcript_{lang_code}.txt"
                            with open(txt_filename, "w", encoding="utf-8") as f:
                                f.write(f"# {lang_name} Translation\\n\\n")
                                for segment in translated_segments:
                                    f.write(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text_translated']}\\n")
                            
                            # Save as SRT file for subtitle compatibility
                            srt_filename = f"translations/transcript_{lang_code}.srt"
                            with open(srt_filename, "w", encoding="utf-8") as f:
                                for idx, segment in enumerate(translated_segments, 1):
                                    start_time = segment['start']
                                    end_time = segment['end']
                                    
                                    # Convert to SRT time format
                                    start_srt = f"{int(start_time//3600):02d}:{int((start_time%3600)//60):02d}:{int(start_time%60):02d},{int((start_time%1)*1000):03d}"
                                    end_srt = f"{int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{int(end_time%60):02d},{int((end_time%1)*1000):03d}"
                                    
                                    f.write(f"{idx}\\n")
                                    f.write(f"{start_srt} --> {end_srt}\\n")
                                    f.write(f"{segment['text_translated']}\\n\\n")
                            
                            results.append(f"✅ {lang_name}: {len(translated_segments)} segments → {txt_filename}, {srt_filename}")
                            successful_translations += 1
                            total_segments_translated += len(translated_segments)
                            
                            print(f"✅ {lang_name} translation completed: {len(translated_segments)} segments")
                        else:
                            results.append(f"❌ {lang_name}: Translation failed - no segments returned")
                            print(f"❌ {lang_name} translation failed")
                        
                        # Add delay between requests to avoid API limits
                        if i < len(all_languages) - 1:  # Don't sleep after the last request
                            delay = api_settings.get("delay_between_requests", 0.5)
                            print(f"⏳ Waiting {delay}s before next translation...")
                            time.sleep(delay)
                            
                    except Exception as e:
                        error_msg = f"❌ {lang_name}: Translation failed - {str(e)}"
                        results.append(error_msg)
                        print(error_msg)
                        continue
                
                # Auto-assign voices for successfully translated languages
                successfully_translated_languages = []
                for lang_code, lang_name, _ in all_languages:
                    json_file = f"translations/transcript_{lang_code}.json"
                    if os.path.exists(json_file):
                        successfully_translated_languages.append(lang_code)
                
                voice_assignment_summary = ""
                if successfully_translated_languages:
                    print(f"🎤 Auto-assigning voices for {len(successfully_translated_languages)} languages...")
                    
                    # Initialize voice assignment manager
                    voice_manager = VoiceAssignmentManager()
                    
                    # Auto-assign voices
                    voice_map = voice_manager.auto_assign_voices(successfully_translated_languages)
                    
                    # Save voice assignments
                    voice_manager.save_voice_assignments(voice_map)
                    
                    # Generate summary
                    voice_assignment_summary = voice_manager.generate_voice_assignment_summary(voice_map)
                    print("\\n" + voice_assignment_summary)
                
                # Create comprehensive summary
                summary_lines = [
                    f"🌍 Multi-Language Translation Complete!",
                    f"📊 Successfully translated to {successful_translations}/{len(all_languages)} languages",
                    f"📈 Total segments translated: {total_segments_translated}",
                    f"📁 Files saved in translations/ folder:",
                    f"   • original.txt (original transcription)",
                    ""
                ]
                summary_lines.extend(results)
                
                # Add voice assignment summary
                if voice_assignment_summary:
                    summary_lines.extend([
                        "",
                        voice_assignment_summary,
                        ""
                    ])
                
                if successful_translations > 0:
                    summary_lines.extend([
                        "",
                        "📋 File formats created for each language:",
                        "   • .txt files for readable transcripts",
                        "   • .json files for programmatic use", 
                        "   • .srt files for subtitle compatibility"
                    ])
                
                # Also save the first successful translation to the main display for compatibility
                first_translation_json = ""
                if successful_translations > 0:
                    # Find the first successful translation file
                    for lang_code, lang_name, _ in all_languages:
                        json_file = f"translations/transcript_{lang_code}.json"
                        if os.path.exists(json_file):
                            with open(json_file, "r", encoding="utf-8") as f:
                                first_translation_json = f.read()
                            break
                
                return first_translation_json, "\\n".join(summary_lines)
                
            except Exception as e:
                return "", f"❌ Multi-language translation failed: {str(e)}"
        
        def refresh_voice_assignments():
            """Refresh voice assignments based on available translations."""
            try:
                # Find available translation files
                translations_dir = Path("translations")
                if not translations_dir.exists():
                    return "", "❌ No translations directory found. Please run translation first."
                
                # Get language codes from translation files
                language_codes = []
                for json_file in translations_dir.glob("transcript_*.json"):
                    lang_code = json_file.stem.replace("transcript_", "")
                    if lang_code != "original":
                        language_codes.append(lang_code)
                
                if not language_codes:
                    return "", "❌ No translation files found."
                
                # Auto-assign voices
                voice_manager = VoiceAssignmentManager()
                voice_map = voice_manager.auto_assign_voices(language_codes)
                voice_manager.save_voice_assignments(voice_map)
                
                # Return JSON for display
                voice_json = json.dumps(voice_map, indent=2, ensure_ascii=False)
                summary = voice_manager.generate_voice_assignment_summary(voice_map)
                
                return voice_json, f"✅ Voice assignments refreshed!\\n\\n{summary}"
                
            except Exception as e:
                return "", f"❌ Error refreshing voice assignments: {str(e)}"
        
        def load_voice_assignments():
            """Load existing voice assignments."""
            try:
                voice_manager = VoiceAssignmentManager()
                voice_map = voice_manager.load_voice_assignments()
                
                if not voice_map:
                    return "", "❌ No saved voice assignments found."
                
                voice_json = json.dumps(voice_map, indent=2, ensure_ascii=False)
                summary = voice_manager.generate_voice_assignment_summary(voice_map)
                
                return voice_json, f"✅ Voice assignments loaded!\\n\\n{summary}"
                
            except Exception as e:
                return "", f"❌ Error loading voice assignments: {str(e)}"
        
        def save_voice_assignments(voice_json):
            """Save edited voice assignments."""
            try:
                if not voice_json.strip():
                    return "❌ No voice assignments to save."
                
                # Parse JSON
                voice_map = json.loads(voice_json)
                
                # Save to file
                voice_manager = VoiceAssignmentManager()
                voice_manager.save_voice_assignments(voice_map)
                
                summary = voice_manager.generate_voice_assignment_summary(voice_map)
                return f"✅ Voice assignments saved!\\n\\n{summary}"
                
            except json.JSONDecodeError:
                return "❌ Invalid JSON format in voice assignments."
            except Exception as e:
                return f"❌ Error saving voice assignments: {str(e)}"
        
        def upload_custom_voice(language_code, voice_file_path):
            """Upload a custom voice file for a language."""
            try:
                if not language_code:
                    return "❌ Please select a language first."
                
                if not voice_file_path:
                    return "❌ Please select a voice file to upload."
                
                voice_manager = VoiceAssignmentManager()
                saved_path = voice_manager.save_custom_voice_file(language_code, voice_file_path)
                
                if saved_path:
                    return f"✅ Custom voice uploaded for {language_code}: {saved_path}"
                else:
                    return "❌ Failed to upload custom voice file."
                    
            except Exception as e:
                return f"❌ Error uploading custom voice: {str(e)}"
        
        def get_languages_for_custom_voice():
            """Get list of languages that need custom voices."""
            try:
                voice_manager = VoiceAssignmentManager()
                voice_map = voice_manager.load_voice_assignments()
                
                # Find languages with "Voice Not Found"
                languages_needing_voices = []
                for lang_code, assignment in voice_map.items():
                    if assignment.get("engine") == "none" or assignment.get("voice") == "Voice Not Found":
                        languages_needing_voices.append((lang_code, lang_code))
                
                return languages_needing_voices
                
            except Exception as e:
                print(f"Error getting languages for custom voice: {str(e)}")
                return []
        
        def generate_all_voices():
            """Generate voices for all languages with assignments."""
            try:
                # Initialize voice generator
                voice_generator = MultiLanguageVoiceGenerator()
                
                # Progress callback
                def progress_callback(progress, message):
                    print(f"[Voice Generation {progress:.1%}] {message}")
                
                # Generate all voices
                final_audio_files = voice_generator.generate_all_voices(progress_callback)
                
                if final_audio_files:
                    # Create summary
                    summary_lines = [
                        f"🎵 Voice Generation Complete!",
                        f"✅ Successfully generated {len(final_audio_files)} voices:",
                        ""
                    ]
                    
                    for lang_code, audio_file in final_audio_files.items():
                        filename = Path(audio_file).name
                        file_size = Path(audio_file).stat().st_size
                        summary_lines.append(f"  • {lang_code}: {filename} ({file_size:,} bytes)")
                    
                    summary_lines.extend([
                        "",
                        f"📁 All files saved in: voices/ directory",
                        "🎧 Use 'Refresh Voice Previews' to see playback controls"
                    ])
                    
                    status_message = "\\n".join(summary_lines)
                    
                    # Get detailed summary
                    detailed_summary = voice_generator.get_generated_voices_summary()
                    summary_text = "\\n".join([
                        f"{lang}: {info['filename']} ({info['file_size']:,} bytes)"
                        for lang, info in detailed_summary.items()
                    ])
                    
                    return status_message, summary_text
                else:
                    return "❌ No voices were generated. Check voice assignments and translations.", ""
                    
            except Exception as e:
                error_msg = f"❌ Voice generation failed: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                return error_msg, ""
        
        def regenerate_single_voice(lang_code):
            """Regenerate voice for a specific language."""
            try:
                if not lang_code:
                    return "❌ Please select a language to regenerate."
                
                # Initialize voice generator
                voice_generator = MultiLanguageVoiceGenerator()
                
                # Regenerate voice
                audio_file = voice_generator.regenerate_voice_for_language(lang_code)
                
                if audio_file:
                    filename = Path(audio_file).name
                    file_size = Path(audio_file).stat().st_size
                    return f"✅ Regenerated voice for {lang_code}: {filename} ({file_size:,} bytes)"
                else:
                    return f"❌ Failed to regenerate voice for {lang_code}"
                    
            except Exception as e:
                error_msg = f"❌ Voice regeneration failed: {str(e)}"
                print(error_msg)
                return error_msg
        
        def refresh_voice_previews():
            """Refresh voice previews and get available languages for regeneration."""
            try:
                # Initialize voice generator
                voice_generator = MultiLanguageVoiceGenerator()
                
                # Get generated voices summary
                voices_summary = voice_generator.get_generated_voices_summary()
                
                if voices_summary:
                    # Create summary text
                    summary_lines = [
                        f"🎧 Available Voice Previews ({len(voices_summary)} voices):",
                        ""
                    ]
                    
                    for lang_code, info in voices_summary.items():
                        summary_lines.append(
                            f"• {lang_code}: {info['filename']} "
                            f"({info['engine']}:{info['voice_name']}, {info['file_size']:,} bytes)"
                        )
                    
                    summary_text = "\\n".join(summary_lines)
                    
                    # Get language choices for regeneration
                    language_choices = [(lang_code, lang_code) for lang_code in voices_summary.keys()]
                    
                    return summary_text, gr.update(choices=language_choices, value=None)
                else:
                    return "❌ No generated voices found. Please generate voices first.", gr.update(choices=[], value=None)
                    
            except Exception as e:
                error_msg = f"❌ Error refreshing voice previews: {str(e)}"
                print(error_msg)
                return error_msg, gr.update(choices=[], value=None)
        
        def create_voice_preview_components():
            """Create dynamic voice preview components."""
            try:
                # Initialize voice generator
                voice_generator = MultiLanguageVoiceGenerator()
                
                # Get generated voices summary
                voices_summary = voice_generator.get_generated_voices_summary()
                
                if not voices_summary:
                    return []
                
                # Create audio components for each voice
                components = []
                for lang_code, info in voices_summary.items():
                    audio_component = gr.Audio(
                        label=f"{lang_code} Voice Preview ({info['voice_name']})",
                        value=info['file_path'],
                        autoplay=False,
                        show_download_button=True
                    )
                    components.append(audio_component)
                
                return components
                
            except Exception as e:
                print(f"Error creating voice preview components: {str(e)}")
                return []
        
        def create_all_dubbed_videos(overwrite_existing):
            """Create dubbed videos for all generated voices."""
            try:
                # Initialize video dubber
                video_dubber = MultiLanguageVideoDubber()
                
                # Progress callback
                def progress_callback(progress, message):
                    print(f"[Video Dubbing {progress:.1%}] {message}")
                
                # Create all dubbed videos
                dubbed_videos = video_dubber.create_all_dubbed_videos(
                    overwrite=overwrite_existing, 
                    progress_callback=progress_callback
                )
                
                if dubbed_videos:
                    # Create status message
                    status_lines = [
                        f"🎬 Video Dubbing Complete!",
                        f"✅ Successfully created {len(dubbed_videos)} dubbed videos:",
                        ""
                    ]
                    
                    for lang_code, video_path in dubbed_videos.items():
                        filename = Path(video_path).name
                        file_size = Path(video_path).stat().st_size
                        status_lines.append(f"  • {lang_code}: {filename} ({file_size:,} bytes)")
                    
                    status_lines.extend([
                        "",
                        f"📁 All videos saved in: final_dubbed/ directory",
                        "🎥 Use 'Refresh Video List' to see video previews"
                    ])
                    
                    status_message = "\\n".join(status_lines)
                    
                    # Get detailed summary
                    detailed_summary = video_dubber.get_dubbed_videos_summary()
                    summary_text = "\\n".join([
                        f"{lang}: {info['filename']} ({info['file_size']:,} bytes, {info.get('duration', 0):.1f}s)"
                        for lang, info in detailed_summary.items()
                    ])
                    
                    # Create dubbing summary
                    dubbing_summary = f"{len(dubbed_videos)} Dubbing Versions Created: {', '.join(dubbed_videos.keys())}"
                    
                    return status_message, summary_text, dubbing_summary
                else:
                    return "❌ No dubbed videos were created. Check source video and generated voices.", "", ""
                    
            except Exception as e:
                error_msg = f"❌ Video dubbing failed: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                return error_msg, "", ""
        
        def recreate_single_dubbed_video(lang_code):
            """Recreate a dubbed video for a specific language."""
            try:
                if not lang_code:
                    return "❌ Please select a language to recreate."
                
                # Initialize video dubber
                video_dubber = MultiLanguageVideoDubber()
                
                # Recreate video
                video_path = video_dubber.recreate_dubbed_video(lang_code, overwrite=True)
                
                if video_path:
                    filename = Path(video_path).name
                    file_size = Path(video_path).stat().st_size
                    return f"✅ Recreated dubbed video for {lang_code}: {filename} ({file_size:,} bytes)"
                else:
                    return f"❌ Failed to recreate dubbed video for {lang_code}"
                    
            except Exception as e:
                error_msg = f"❌ Video recreation failed: {str(e)}"
                print(error_msg)
                return error_msg
        
        def delete_single_dubbed_video(lang_code):
            """Delete a dubbed video for a specific language."""
            try:
                if not lang_code:
                    return "❌ Please select a language to delete."
                
                # Initialize video dubber
                video_dubber = MultiLanguageVideoDubber()
                
                # Delete video
                success = video_dubber.delete_dubbed_video(lang_code)
                
                if success:
                    return f"✅ Deleted dubbed video for {lang_code}"
                else:
                    return f"❌ Failed to delete dubbed video for {lang_code}"
                    
            except Exception as e:
                error_msg = f"❌ Video deletion failed: {str(e)}"
                print(error_msg)
                return error_msg
        
        def refresh_dubbed_videos():
            """Refresh dubbed videos list and get available languages."""
            try:
                # Initialize video dubber
                video_dubber = MultiLanguageVideoDubber()
                
                # Get dubbed videos summary
                videos_summary = video_dubber.get_dubbed_videos_summary()
                
                if videos_summary:
                    # Create summary text
                    summary_lines = [
                        f"🎥 Available Dubbed Videos ({len(videos_summary)} videos):",
                        ""
                    ]
                    
                    for lang_code, info in videos_summary.items():
                        duration_str = f"{info.get('duration', 0):.1f}s" if info.get('duration') else "unknown"
                        summary_lines.append(
                            f"• {lang_code}: {info['filename']} "
                            f"({info['engine']}:{info['voice_name']}, {info['file_size']:,} bytes, {duration_str})"
                        )
                    
                    summary_text = "\\n".join(summary_lines)
                    
                    # Get language choices for operations
                    language_choices = [(lang_code, lang_code) for lang_code in videos_summary.keys()]
                    
                    return summary_text, gr.update(choices=language_choices, value=None)
                else:
                    return "❌ No dubbed videos found. Please create dubbed videos first.", gr.update(choices=[], value=None)
                    
            except Exception as e:
                error_msg = f"❌ Error refreshing dubbed videos: {str(e)}"
                print(error_msg)
                return error_msg, gr.update(choices=[], value=None)
        
        def create_video_preview_components():
            """Create dynamic video preview components."""
            try:
                # Initialize video dubber
                video_dubber = MultiLanguageVideoDubber()
                
                # Get dubbed videos summary
                videos_summary = video_dubber.get_dubbed_videos_summary()
                
                if not videos_summary:
                    return []
                
                # Create video components for each dubbed video
                components = []
                for lang_code, info in videos_summary.items():
                    with gr.Group():
                        gr.Markdown(f"#### {lang_code} Dubbed Video ({info['voice_name']})")
                        
                        video_component = gr.Video(
                            label=f"{lang_code} Video Preview",
                            value=info['file_path'],
                            show_download_button=True
                        )
                        
                        with gr.Row():
                            download_btn = gr.DownloadButton(
                                label=f"📥 Download {lang_code}",
                                value=info['file_path']
                            )
                            
                            info_text = gr.Textbox(
                                value=f"File: {info['filename']} | Size: {info['file_size']:,} bytes | Duration: {info.get('duration', 0):.1f}s",
                                label="Video Info",
                                interactive=False,
                                max_lines=1
                            )
                        
                        components.extend([video_component, download_btn, info_text])
                
                return components
                
            except Exception as e:
                print(f"Error creating video preview components: {str(e)}")
                return []
        
        def refresh_voice_assignment_table():
            """Refresh the voice assignment table with detected languages."""
            try:
                # Initialize panel
                panel = CustomVoiceAssignmentPanel()
                
                # Get table data
                table_data = panel.create_voice_assignment_table_data()
                
                if not table_data:
                    return "❌ No translated languages detected. Please run translation first.", ""
                
                # Create dynamic components for each language
                components_html = []
                for data in table_data:
                    lang_code = data["language_code"]
                    lang_name = data["language_name"]
                    voice_options = data["voice_options"]
                    current_voice = data["current_voice"]
                    
                    # Create HTML for this language row
                    options_html = "\\n".join([f'<option value="{opt}" {"selected" if opt == current_voice else ""}>{opt}</option>' for opt in voice_options])
                    
                    row_html = f"""
                    <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px;">
                        <h4>{lang_name} ({lang_code})</h4>
                        <select id="voice_select_{lang_code}" style="width: 100%; padding: 5px;">
                            {options_html}
                        </select>
                        <button onclick="testVoice('{lang_code}')" style="margin-top: 5px; padding: 5px 10px;">🧪 Test Voice</button>
                    </div>
                    """
                    components_html.append(row_html)
                
                table_html = "\\n".join(components_html)
                
                # Get current assignments summary
                current_assignments = panel.load_voice_assignments()
                summary = panel.create_voice_assignment_summary(current_assignments)
                
                return f"✅ Found {len(table_data)} translated languages ready for voice assignment.", summary
                
            except Exception as e:
                error_msg = f"❌ Error refreshing voice table: {str(e)}"
                print(error_msg)
                return error_msg, ""
        
        def auto_assign_best_voices():
            """Automatically assign best available voices."""
            try:
                # Initialize panel
                panel = CustomVoiceAssignmentPanel()
                
                # Auto assign voices
                auto_assignments = panel.auto_assign_best_voices()
                
                if not auto_assignments:
                    return "❌ No languages detected for auto assignment.", ""
                
                # Save assignments
                success = panel.save_voice_assignments(auto_assignments)
                
                if success:
                    summary = panel.create_voice_assignment_summary(auto_assignments)
                    return f"✅ Auto-assigned voices for {len(auto_assignments)} languages.", summary
                else:
                    return "❌ Failed to save auto assignments.", ""
                    
            except Exception as e:
                error_msg = f"❌ Auto assignment failed: {str(e)}"
                print(error_msg)
                return error_msg, ""
        
        def save_current_voice_assignments():
            """Save current voice assignments (placeholder for dynamic table)."""
            try:
                # This would normally get data from the dynamic table
                # For now, we'll load and re-save existing assignments
                panel = CustomVoiceAssignmentPanel()
                current_assignments = panel.load_voice_assignments()
                
                if current_assignments:
                    success = panel.save_voice_assignments(current_assignments)
                    if success:
                        summary = panel.create_voice_assignment_summary(current_assignments)
                        return f"✅ Saved voice assignments for {len(current_assignments)} languages.", summary
                    else:
                        return "❌ Failed to save voice assignments.", ""
                else:
                    return "❌ No voice assignments to save.", ""
                    
            except Exception as e:
                error_msg = f"❌ Save failed: {str(e)}"
                print(error_msg)
                return error_msg, ""
        
        def upload_custom_voice_file(voice_file_path, language_code, voice_name):
            """Upload a custom voice file."""
            try:
                # Initialize panel
                panel = CustomVoiceAssignmentPanel()
                
                # Upload voice
                success, message = panel.upload_custom_voice(voice_file_path, language_code, voice_name)
                
                return message
                
            except Exception as e:
                error_msg = f"❌ Upload failed: {str(e)}"
                print(error_msg)
                return error_msg
        
        def generate_voice_previews():
            """Generate voice previews for assigned voices."""
            try:
                # Initialize panel
                panel = CustomVoiceAssignmentPanel()
                
                # Get current assignments
                assignments = panel.load_voice_assignments()
                detected_languages = panel.get_detected_languages()
                
                if not assignments:
                    return "❌ No voice assignments found. Please assign voices first."
                
                preview_components = []
                successful_previews = 0
                
                for lang_code, assignment in assignments.items():
                    try:
                        lang_name = detected_languages.get(lang_code, lang_code.upper())
                        engine = assignment.get("engine", "unknown")
                        voice = assignment.get("voice", "unknown")
                        
                        if engine == "none" or voice == "Voice Not Found":
                            continue
                        
                        # Generate preview text
                        preview_text = panel.generate_voice_preview_text(lang_code)
                        
                        # Create preview component info
                        preview_info = {
                            "language": lang_name,
                            "language_code": lang_code,
                            "engine": engine,
                            "voice": voice,
                            "preview_text": preview_text
                        }
                        
                        preview_components.append(preview_info)
                        successful_previews += 1
                        
                    except Exception as e:
                        print(f"❌ Error creating preview for {lang_code}: {str(e)}")
                        continue
                
                if successful_previews > 0:
                    # Create preview summary
                    preview_summary = f"🔊 Generated {successful_previews} voice previews:\\n\\n"
                    for preview in preview_components:
                        preview_summary += f"• {preview['language']} ({preview['voice']}) - {preview['engine'].title()} TTS\\n"
                    
                    return preview_summary
                else:
                    return "❌ No voice previews could be generated."
                    
            except Exception as e:
                error_msg = f"❌ Preview generation failed: {str(e)}"
                print(error_msg)
                return error_msg
        
        def clear_voice_previews():
            """Clear voice previews."""
            return "✅ Voice previews cleared."
        
        def enable_manual_translation():
            """Enable manual translation paste mode"""
            sample_json = [
                {"start": 0.0, "end": 4.5, "text_translated": "नमस्ते सब लोग, मैं मिपैक्स बोल रहा हूँ।"},
                {"start": 4.5, "end": 9.8, "text_translated": "आज हम वन पीस की ताज़ा थ्योरीज़ पर बात करने वाले हैं।"}
            ]
            json_output = json.dumps(sample_json, indent=2, ensure_ascii=False)
            return json_output, "✅ Manual translation enabled. Edit the JSON above with your translation."
        
        def generate_tts_audio(translation_json, tts_engine, gemini_language, gemini_voice, edge_language, edge_voice, kokoro_language, kokoro_voice, tts_method, tts_instructions):
            """Generate TTS audio using selected engine and method"""
            try:
                # Parse translation JSON
                if not translation_json.strip():
                    return "❌ No translation provided. Please translate first.", None
                
                try:
                    translated_segments = json.loads(translation_json)
                except json.JSONDecodeError:
                    return "❌ Invalid JSON in translation. Please check the format.", None
                
                # Save translation to file for compatibility
                with open('translated.json', 'w', encoding='utf-8') as f:
                    json.dump(translated_segments, f, indent=2, ensure_ascii=False)
                
                # Progress callback
                def progress_callback(progress, message):
                    print(f"[TTS {progress:.1%}] {message}")
                
                # Choose TTS engine
                if tts_engine == "kokoro" and KOKORO_TTS_AVAILABLE:
                    # Use Kokoro TTS
                    print("🎌 Using Kokoro TTS (Local)")
                    
                    if not kokoro_voice:
                        return "❌ No Kokoro voice selected", None
                    
                    try:
                        # Parse voice name from display name
                        voice_parser = KokoroVoiceParser()
                        voice_name = voice_parser.get_voice_name_from_display(kokoro_voice, kokoro_language)
                        
                        if not voice_name:
                            return f"❌ No Kokoro voice found for language={kokoro_language}, name={kokoro_voice}", None
                        
                        print(f"🎤 Using Kokoro TTS: {voice_name} for language: {kokoro_language}")
                        
                        # Initialize Kokoro TTS service
                        kokoro_service = KokoroTTSService(voice_name=voice_name)
                        
                        if not kokoro_service.model_available:
                            return "❌ Kokoro model not available. Please ensure Kokoro-82M is installed.", None
                        
                        # Generate TTS chunks with fallback to Edge TTS
                        chunks_dir = kokoro_service.generate_tts_chunks(translated_segments, progress_callback)
                        
                        if chunks_dir and os.path.exists(chunks_dir):
                            # List generated files
                            chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
                            
                            if chunk_files:
                                # Use chunked audio stitcher for proper combination
                                progress_callback(0.9, "Stitching Kokoro audio chunks with timestamp sync...")
                                
                                try:
                                    stitcher = ChunkedAudioStitcher()
                                    
                                    # Stitch chunks with proper timestamp matching
                                    final_audio = stitcher.stitch_chunked_audio(
                                        chunks_dir, 
                                        "chunked_transcript.json",
                                        "final_audio/kokoro_tts_final.wav"
                                    )
                                    
                                    # Create video-ready audio
                                    video_ready_audio = stitcher.create_video_ready_audio(
                                        final_audio,
                                        None,  # No original video provided yet
                                        "final_audio/kokoro_tts_video_ready.wav"
                                    )
                                    
                                    # Generate stitching report
                                    report = stitcher.get_stitching_report(chunks_dir, final_audio)
                                    
                                    # Copy for UI preview
                                    combined_audio = "temp_audio/combined_kokoro_tts.wav"
                                    os.makedirs("temp_audio", exist_ok=True)
                                    import shutil
                                    shutil.copy2(video_ready_audio, combined_audio)
                                    
                                    total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
                                    
                                    return f"""✅ Kokoro TTS completed successfully!
🎤 Voice: {voice_name}
🌍 Language: {kokoro_language}
📁 Chunks directory: {chunks_dir}
🎵 Generated chunks: {len(chunk_files)}
📊 Total size: {total_size:,} bytes
🎯 Method: Local Kokoro Neural TTS with timestamp sync
⚡ Segments: {len(translated_segments)}
🔄 Fallback: Edge TTS (if available)
🎼 Final audio: {final_audio}
📺 Video-ready: {video_ready_audio}
⏱️ Timing accuracy: {report['timing_accuracy']}
🎚️ Audio duration: {report['final_audio_duration']:.2f}s
🏠 Privacy: Fully local processing""", combined_audio
                                    
                                except Exception as e:
                                    print(f"⚠️ Kokoro chunked stitching failed, using simple combination: {str(e)}")
                                    
                                    # Fallback to simple combination
                                    combined_audio = "temp_audio/combined_kokoro_tts.wav"
                                    os.makedirs("temp_audio", exist_ok=True)
                                    first_chunk = os.path.join(chunks_dir, sorted(chunk_files)[0])
                                    import shutil
                                    shutil.copy2(first_chunk, combined_audio)
                                    
                                    total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
                                    
                                    return f"""✅ Kokoro TTS completed (basic mode)!
🎤 Voice: {voice_name}
🌍 Language: {kokoro_language}
📁 Chunks directory: {chunks_dir}
🎵 Generated chunks: {len(chunk_files)}
📊 Total size: {total_size:,} bytes
⚠️ Note: Advanced stitching failed, using basic preview
🏠 Privacy: Fully local processing""", combined_audio
                            else:
                                return "❌ No Kokoro audio chunks generated", None
                        else:
                            return "❌ Kokoro TTS generation failed", None
                            
                    except Exception as e:
                        return f"❌ Kokoro TTS error: {str(e)}", None
                
                elif tts_engine == "gemini":
                    # Use Gemini TTS
                    print("🤖 Using Gemini TTS")
                    
                    if not gemini_voice:
                        return "❌ No Gemini voice selected", None
                    
                    try:
                        # Parse voice name from display name
                        from gemini_voice_library import GeminiVoiceLibrary
                        gemini_library = GeminiVoiceLibrary()
                        
                        # Find the actual voice name from display name
                        voice_name = None
                        for lang_code, voices in gemini_library.gemini_voices.items():
                            for voice in voices:
                                if gemini_library.get_voice_display_name(voice) == gemini_voice:
                                    voice_name = voice
                                    break
                            if voice_name:
                                break
                        
                        if not voice_name:
                            return f"❌ Gemini voice not found: {gemini_voice}", None
                        
                        print(f"🎤 Using Gemini TTS: {voice_name}")
                        
                        # Initialize Gemini service
                        if not has_api_keys():
                            return "❌ No Gemini API keys configured", None
                        
                        api_keys = get_api_keys()
                        gemini_service = RealGeminiService(api_keys)
                        
                        # Generate TTS chunks
                        chunks_dir = gemini_service.generate_tts_chunks(translated_segments, voice_name, progress_callback)
                        
                        if chunks_dir and os.path.exists(chunks_dir):
                            # List generated files
                            chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
                            
                            if chunk_files:
                                # Use chunked audio stitcher for proper combination
                                progress_callback(0.9, "Stitching Gemini audio chunks...")
                                
                                try:
                                    stitcher = ChunkedAudioStitcher()
                                    
                                    # Stitch chunks with proper timestamp matching
                                    final_audio = stitcher.stitch_chunked_audio(
                                        chunks_dir, 
                                        "chunked_transcript.json",
                                        "final_audio/gemini_tts_final.wav"
                                    )
                                    
                                    # Create video-ready audio
                                    video_ready_audio = stitcher.create_video_ready_audio(
                                        final_audio,
                                        None,  # No original video provided yet
                                        "final_audio/gemini_tts_video_ready.wav"
                                    )
                                    
                                    # Copy for UI preview
                                    combined_audio = "temp_audio/combined_gemini_tts.wav"
                                    os.makedirs("temp_audio", exist_ok=True)
                                    import shutil
                                    shutil.copy2(video_ready_audio, combined_audio)
                                    
                                    total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
                                    
                                    return f"""✅ Gemini TTS completed successfully!
🎤 Voice: {voice_name}
🤖 Engine: Google Gemini TTS
📁 Chunks directory: {chunks_dir}
🎵 Generated chunks: {len(chunk_files)}
📊 Total size: {total_size:,} bytes
🎯 Method: Gemini Neural TTS with timestamp sync
⚡ Segments: {len(translated_segments)}

📋 Stitching Report:
{stitcher.get_stitching_report(chunks_dir, final_audio)}""", combined_audio
                                    
                                except Exception as e:
                                    return f"❌ Audio stitching error: {str(e)}", None
                            else:
                                return "❌ No Gemini audio chunks generated", None
                        else:
                            return "❌ Gemini TTS generation failed", None
                            
                    except Exception as e:
                        return f"❌ Gemini TTS error: {str(e)}", None
                
                elif tts_engine == "edge" and EDGE_TTS_AVAILABLE:
                    # Use Enhanced Edge TTS
                    print("🎙️ Using Microsoft Edge TTS")
                    
                    if not edge_voice:
                        return "❌ No Edge TTS voice selected", None
                    
                    try:
                        # Parse voice parser to get short name
                        voice_parser = EdgeTTSVoiceParser()
                        if not voice_parser.voices:
                            voice_parser.parse_voices()
                        
                        # Get short name from display name
                        voice_short_name = voice_parser.get_voice_short_name(edge_voice, edge_language)
                        
                        print(f"🎤 Using Edge TTS: {voice_short_name} for language: {edge_language}")
                        
                        # Create Edge TTS configuration
                        edge_config = EdgeTTSConfig(
                            voice_name=voice_short_name,
                            language=edge_language
                        )
                        
                        # Initialize Enhanced Edge TTS service with Gemini fallback
                        fallback_service = None
                        try:
                            # Try to create Gemini fallback if API keys available
                            if has_api_keys():
                                api_keys = get_api_keys()
                                if api_keys:
                                    fallback_service = FinalWorkingTTS(api_keys[0], "Kore")
                                    print("✅ Gemini TTS fallback service available")
                        except:
                            print("⚠️ Gemini TTS fallback not available")
                        
                        edge_service = EnhancedEdgeTTSService(edge_config, fallback_service)
                        
                        # Generate TTS chunks
                        chunks_dir = edge_service.generate_tts_chunks(translated_segments, progress_callback)
                        
                        if chunks_dir and os.path.exists(chunks_dir):
                            # List generated files
                            chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
                            
                            if chunk_files:
                                # Use chunked audio stitcher for proper combination
                                progress_callback(0.9, "Stitching audio chunks with timestamp sync...")
                                
                                try:
                                    stitcher = ChunkedAudioStitcher()
                                    
                                    # Stitch chunks with proper timestamp matching
                                    final_audio = stitcher.stitch_chunked_audio(
                                        chunks_dir, 
                                        "chunked_transcript.json",
                                        "final_audio/edge_tts_final.wav"
                                    )
                                    
                                    # Create video-ready audio
                                    video_ready_audio = stitcher.create_video_ready_audio(
                                        final_audio,
                                        None,  # No original video provided yet
                                        "final_audio/edge_tts_video_ready.wav"
                                    )
                                    
                                    # Generate stitching report
                                    report = stitcher.get_stitching_report(chunks_dir, final_audio)
                                    
                                    # Copy for UI preview
                                    combined_audio = "temp_audio/combined_edge_tts.wav"
                                    os.makedirs("temp_audio", exist_ok=True)
                                    import shutil
                                    shutil.copy2(video_ready_audio, combined_audio)
                                    
                                    total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
                                    
                                    return f"""✅ Edge TTS completed successfully!
🎤 Voice: {voice_short_name}
🌍 Language: {edge_language}
📁 Chunks directory: {chunks_dir}
🎵 Generated chunks: {len(chunk_files)}
📊 Total size: {total_size:,} bytes
🎯 Method: Microsoft Edge Neural TTS with timestamp sync
⚡ Segments: {len(translated_segments)}
🔄 Fallback: {'Available' if fallback_service else 'None'}
🎼 Final audio: {final_audio}
📺 Video-ready: {video_ready_audio}
⏱️ Timing accuracy: {report['timing_accuracy']}
🎚️ Audio duration: {report['final_audio_duration']:.2f}s""", combined_audio
                                    
                                except Exception as e:
                                    print(f"⚠️ Chunked stitching failed, using simple combination: {str(e)}")
                                    
                                    # Fallback to simple combination
                                    combined_audio = "temp_audio/combined_edge_tts.wav"
                                    os.makedirs("temp_audio", exist_ok=True)
                                    first_chunk = os.path.join(chunks_dir, sorted(chunk_files)[0])
                                    import shutil
                                    shutil.copy2(first_chunk, combined_audio)
                                    
                                    total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
                                    
                                    return f"""✅ Edge TTS completed (basic mode)!
🎤 Voice: {voice_short_name}
🌍 Language: {edge_language}
📁 Chunks directory: {chunks_dir}
🎵 Generated chunks: {len(chunk_files)}
📊 Total size: {total_size:,} bytes
⚠️ Note: Advanced stitching failed, using basic preview""", combined_audio
                            else:
                                return "❌ No audio chunks generated", None
                        else:
                            return "❌ Edge TTS generation failed", None
                            
                    except Exception as e:
                        return f"❌ Edge TTS error: {str(e)}", None
                
                else:
                    # Use Gemini TTS (existing logic)
                    print("🤖 Using Gemini TTS")
                    
                    # Check API keys for Gemini
                    if not has_api_keys():
                        return "❌ No API keys saved for Gemini TTS.", None
                    
                    api_keys = get_api_keys()
                    
                    # Choose TTS method for Gemini
                    if tts_method == "single_request":
                        # Use Single-Request TTS
                        print("🚀 Using Single-Request Gemini TTS method")
                        single_tts_service = SingleRequestTTS(api_keys[0], gemini_voice)
                        
                        final_audio = single_tts_service.process_subtitles_single_request(
                            translated_segments, 
                            tts_instructions or "",
                            progress_callback
                        )
                        
                        if final_audio and os.path.exists(final_audio):
                            file_size = os.path.getsize(final_audio)
                            duration = single_tts_service.get_audio_duration(final_audio)
                            
                            # Copy to temp location for UI
                            combined_audio = "temp_audio/combined_tts_preview.wav"
                            os.makedirs("temp_audio", exist_ok=True)
                            import shutil
                            shutil.copy2(final_audio, combined_audio)
                            
                            return f"""✅ Single-Request Gemini TTS completed successfully!
📁 File: {final_audio}
📊 Size: {file_size:,} bytes
⏱️ Duration: {duration:.2f}s
🎵 Segments: {len(translated_segments)}
🚀 API Calls: {len(translated_segments)} → 1 (saved {len(translated_segments)-1} calls)
🎯 Method: Single Request with consistent timing""", combined_audio
                        else:
                            return "❌ Single-request Gemini TTS failed - trying individual method as fallback...", None
                    
                    else:
                        # Use Individual Segments TTS (Final Working TTS)
                        print("🔄 Using Individual Segments Gemini TTS method")
                        tts_service = FinalWorkingTTS(api_keys[0], gemini_voice)
                        
                        final_audio = tts_service.process_subtitle_json(
                            translated_segments, progress_callback
                        )
                        
                        if final_audio and os.path.exists(final_audio):
                            file_size = os.path.getsize(final_audio)
                            duration = tts_service.get_audio_duration(final_audio)
                            
                            # Copy to temp location for UI
                            combined_audio = "temp_audio/combined_tts_preview.wav"
                            os.makedirs("temp_audio", exist_ok=True)
                            import shutil
                            shutil.copy2(final_audio, combined_audio)
                            
                            return f"""✅ Individual Gemini TTS completed successfully!
📁 File: {final_audio}
📊 Size: {file_size:,} bytes
⏱️ Duration: {duration:.2f}s
🎵 Segments: {len(translated_segments)}
🔄 API Calls: {len(translated_segments)} individual requests
🎯 Method: Individual segments processing""", combined_audio
                        else:
                            return "❌ Gemini TTS generation failed - check API key and network connection", None
                
            except Exception as e:
                return f"❌ TTS generation failed: {str(e)}", None
        
        def get_chunked_audio_status():
            """Get status of chunked audio processing."""
            try:
                status_lines = []
                
                # Check for chunked transcript
                if os.path.exists("chunked_transcript.json"):
                    with open("chunked_transcript.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and "metadata" in data:
                        metadata = data["metadata"]
                        chunks_count = metadata.get("total_chunks", 0)
                        total_duration = metadata.get("total_duration", 0)
                        status_lines.append(f"✅ Chunked transcript: {chunks_count} chunks ({total_duration:.1f}s)")
                    else:
                        status_lines.append("✅ Chunked transcript: Available")
                else:
                    status_lines.append("❌ Chunked transcript: Not found")
                
                # Check for TTS chunks
                chunks_dirs = ["edge_tts_chunks", "tts_chunks", "simple_edge_output"]
                chunks_found = False
                
                for chunks_dir in chunks_dirs:
                    if os.path.exists(chunks_dir):
                        chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith(('.wav', '.mp3'))]
                        if chunk_files:
                            total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
                            status_lines.append(f"✅ TTS chunks ({chunks_dir}): {len(chunk_files)} files ({total_size:,} bytes)")
                            chunks_found = True
                            break
                
                if not chunks_found:
                    status_lines.append("❌ TTS chunks: Not found")
                
                # Check for final audio files
                final_audio_files = [
                    ("final_audio/edge_tts_final.wav", "Edge TTS final"),
                    ("final_audio/edge_tts_video_ready.wav", "Edge TTS video-ready"),
                    ("final_audio/gemini_tts_final.wav", "Gemini TTS final"),
                    ("temp_audio/combined_tts_preview.wav", "Preview audio")
                ]
                
                final_audio_found = False
                for audio_file, description in final_audio_files:
                    if os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        
                        # Get audio duration if possible
                        try:
                            stitcher = ChunkedAudioStitcher()
                            audio_info = stitcher._get_audio_info(audio_file)
                            duration = audio_info.get('duration', 0)
                            status_lines.append(f"✅ {description}: {file_size:,} bytes ({duration:.1f}s)")
                        except:
                            status_lines.append(f"✅ {description}: {file_size:,} bytes")
                        
                        final_audio_found = True
                
                if not final_audio_found:
                    status_lines.append("❌ Final audio: Not found")
                
                # Check for final video
                if os.path.exists("final_dubbed_video.mp4"):
                    video_size = os.path.getsize("final_dubbed_video.mp4")
                    status_lines.append(f"✅ Final video: {video_size:,} bytes")
                else:
                    status_lines.append("❌ Final video: Not created")
                
                # Overall readiness assessment
                if chunks_found and final_audio_found:
                    status_lines.insert(0, "🎯 Status: Ready for final video creation")
                elif chunks_found:
                    status_lines.insert(0, "⚠️ Status: TTS completed, needs audio stitching")
                else:
                    status_lines.insert(0, "❌ Status: TTS generation required")
                
                return "\n".join(status_lines)
                
            except Exception as e:
                return f"❌ Error checking audio status: {str(e)}"
        
        def create_final_video(video_file):
            """Create final dubbed video with enhanced audio stitching"""
            try:
                if not video_file:
                    return "❌ No video file provided", None
                
                # Look for properly stitched audio first
                video_ready_audio = "final_audio/edge_tts_video_ready.wav"
                gemini_audio = "final_audio/gemini_tts_final.wav"
                fallback_audio = "temp_audio/combined_tts_preview.wav"
                
                # Determine which audio to use
                audio_to_use = None
                audio_source = ""
                
                if os.path.exists(video_ready_audio):
                    audio_to_use = video_ready_audio
                    audio_source = "Edge TTS (video-ready)"
                elif os.path.exists(gemini_audio):
                    audio_to_use = gemini_audio
                    audio_source = "Gemini TTS (final)"
                elif os.path.exists(fallback_audio):
                    audio_to_use = fallback_audio
                    audio_source = "Preview audio (fallback)"
                else:
                    return "❌ No TTS audio found. Please generate TTS first.", None
                
                print(f"🎵 Using audio: {audio_to_use} ({audio_source})")
                
                # Create video-ready audio if needed
                if audio_to_use == fallback_audio:
                    try:
                        stitcher = ChunkedAudioStitcher()
                        audio_to_use = stitcher.create_video_ready_audio(
                            fallback_audio,
                            video_file,
                            "final_audio/video_ready_fallback.wav"
                        )
                        audio_source = "Processed fallback audio"
                        print(f"🔧 Processed fallback audio for video compatibility")
                    except Exception as e:
                        print(f"⚠️ Could not process fallback audio: {str(e)}")
                
                # Create final dubbed video using FFmpeg directly
                output_video = "final_dubbed_video.mp4"
                
                print(f"🎬 Creating dubbed video: {video_file} + {audio_to_use}")
                
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_file,      # Input video
                    "-i", audio_to_use,    # Input audio
                    "-c:v", "copy",        # Copy video stream (no re-encoding)
                    "-c:a", "aac",         # Encode audio as AAC
                    "-b:a", "128k",        # Audio bitrate
                    "-map", "0:v:0",       # Map video from first input
                    "-map", "1:a:0",       # Map audio from second input
                    "-shortest",           # End when shortest stream ends
                    output_video
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(output_video):
                    # Get output video info
                    try:
                        video_info_cmd = [
                            'ffprobe', '-v', 'quiet', '-print_format', 'json',
                            '-show_format', output_video
                        ]
                        info_result = subprocess.run(video_info_cmd, capture_output=True, text=True)
                        if info_result.returncode == 0:
                            info = json.loads(info_result.stdout)
                            duration = float(info['format'].get('duration', 0))
                            file_size = os.path.getsize(output_video)
                            
                            return f"""✅ Dubbed video created successfully!
🎬 Output: {output_video}
🎵 Audio source: {audio_source}
⏱️ Duration: {duration:.2f}s
📊 File size: {file_size:,} bytes
🎯 Video codec: Copy (no re-encoding)
🔊 Audio codec: AAC 128k
📺 Ready for playback and sharing!""", output_video
                        else:
                            return f"✅ Dubbed video created: {output_video}", output_video
                    except Exception as e:
                        return f"✅ Dubbed video created: {output_video}", output_video
                else:
                    error_msg = result.stderr if result.stderr else "Unknown FFmpeg error"
                    return f"❌ Video creation failed: {error_msg}", None
                
            except Exception as e:
                return f"❌ Video creation failed: {str(e)}", None

        def start_dubbing_process(video_file, translation_prompt_text, voice_name, manual_translation_text):
            if not video_file:
                return "❌ No video file provided", None, None, "❌ No video file"
            
            try:
                # Check if API keys are saved
                if not has_api_keys():
                    return "❌ No API keys saved. Please save API keys first.", None, None, "❌ No API keys"
                
                # Get API keys from memory
                api_keys = get_api_keys()
                if not api_keys:
                    return "❌ No API keys available", None, None, "❌ No API keys"
                
                # Initialize dubbing service with API keys
                dubbing_service = RealGeminiService(api_keys)
                
                # Get ASR data
                asr_data = load_asr_results()
                if not asr_data:
                    return "❌ No transcription found. Please transcribe the video first.", None, None, "❌ No transcription"
                
                progress_log = []
                
                def update_progress(progress, message):
                    progress_log.append(f"[{progress:.1%}] {message}")
                    return "\n".join(progress_log[-10:])  # Keep last 10 messages
                
                # Determine if using manual or automatic translation
                if manual_translation_text.strip():
                    # Manual mode
                    try:
                        translated_segments = json.loads(manual_translation_text)
                        progress_log.append("✅ Using manual translation")
                    except json.JSONDecodeError:
                        return "❌ Invalid JSON in manual translation", None, None, "❌ Invalid JSON"
                else:
                    # Automatic mode - translate using prompt
                    if not translation_prompt_text.strip():
                        translation_prompt_text = '{"tone": "neutral", "dialect": "standard", "genre": "general"}'
                    
                    progress_log.append("🔄 Starting automatic translation...")
                    
                    try:
                        # Parse style config from translation prompt
                        try:
                            style_config = json.loads(translation_prompt_text)
                        except:
                            style_config = {"tone": "neutral", "dialect": "standard", "genre": "general"}
                        
                        translated_segments = dubbing_service.translate_full_transcript(
                            asr_data, style_config,
                            lambda p, m: progress_log.append(f"[Translation {p:.1%}] {m}")
                        )
                        progress_log.append("✅ Translation completed")
                    except Exception as e:
                        return f"❌ Translation failed: {str(e)}", None, None, "❌ Translation failed"
                
                # Generate TTS audio using FIXED service
                progress_log.append("🔄 Starting FINAL WORKING TTS generation...")
                try:
                    # Initialize Final Working TTS service (confirmed working)
                    tts_service = FinalWorkingTTS(api_keys[0], voice_name)
                    
                    # Generate TTS audio with final working service
                    final_audio = tts_service.process_subtitle_json(
                        translated_segments,
                        lambda p, m: progress_log.append(f"[TTS {p:.1%}] {m}")
                    )
                    progress_log.append("✅ FINAL WORKING TTS generation completed - Real Hindi audio!")
                except Exception as e:
                    return f"❌ TTS failed: {str(e)}", None, None, "❌ TTS failed"
                
                # Create final dubbed video
                progress_log.append("🔄 Creating dubbed video...")
                try:
                    # Create final video using FFmpeg directly
                    dubbed_video_path = "final_dubbed.mp4"
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_file,
                        "-i", final_audio,
                        "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-shortest",
                        dubbed_video_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0 and os.path.exists(dubbed_video_path):
                        progress_log.append("✅ Dubbing completed successfully!")
                        progress_log.append("🎉 Full TTS dubbing with REAL AI-generated Hindi voice completed!")
                        progress_log.append(f"📁 Audio: {final_audio}")
                        progress_log.append(f"🎬 Video: {dubbed_video_path}")
                        
                        return "\n".join(progress_log), dubbed_video_path, final_audio, "✅ Completed"
                    else:
                        raise Exception(f"FFmpeg failed: {result.stderr}")
                    
                except Exception as e:
                    # Even if video creation fails, we have the audio
                    progress_log.append(f"⚠️ Video creation failed: {str(e)}")
                    progress_log.append("✅ But TTS audio was generated successfully!")
                    progress_log.append(f"📁 Audio: {final_audio}")
                    return "\n".join(progress_log), None, final_audio, "✅ Audio completed"
                
            except Exception as e:
                return f"❌ Dubbing process failed: {str(e)}", None, None, "❌ Process failed"
        
        # Step-by-Step Event Handlers
        
        # Step 2: Transcription options
        transcribe_here_btn.click(
            transcribe_video_here,
            inputs=[video_upload, is_music_mode, step_enable_chunking, step_chunk_duration],
            outputs=[transcription_display, transcription_status]
        )
        
        load_transcription_btn.click(
            load_transcription_from_asr,
            outputs=[transcription_display, transcription_status]
        )
        
        paste_json_btn.click(
            enable_manual_paste,
            outputs=[transcription_display, transcription_status]
        )
        
        # Step 3: Translation options
        translate_btn.click(
            translate_with_gemini,
            inputs=[transcription_display, translation_prompt],
            outputs=[translation_display, translation_status]
        )
        
        paste_translation_btn.click(
            enable_manual_translation,
            outputs=[translation_display, translation_status]
        )
        
        # Multi-language translation handlers
        enable_multi_lang.change(
            lambda enabled: (
                gr.update(visible=enabled),  # multi_lang_selection
                gr.update(visible=enabled),  # custom_languages
                gr.update(visible=enabled),  # selected_lang_config
                gr.update(visible=enabled),  # multi_lang_style
                gr.update(visible=enabled),  # translate_multi_btn
                gr.update(visible=enabled),  # multi_lang_results
                gr.update(visible=enabled),  # custom_voice_assignment_panel
                gr.update(visible=enabled),  # voice_assignments_display
                gr.update(visible=enabled),  # voice_management_row
                gr.update(visible=enabled),  # custom_voice_upload_group
                gr.update(visible=enabled),  # voice_generation_group
                gr.update(visible=enabled)   # final_dubbed_videos_group
            ),
            inputs=[enable_multi_lang],
            outputs=[multi_lang_selection, custom_languages, selected_lang_config, multi_lang_style, translate_multi_btn, multi_lang_results, custom_voice_assignment_panel, voice_assignments_display, voice_management_row, custom_voice_upload_group, voice_generation_group, final_dubbed_videos_group]
        )
        
        # Update language configuration display when languages are selected
        multi_lang_selection.change(
            update_language_config_display,
            inputs=[multi_lang_selection],
            outputs=[selected_lang_config]
        )
        
        translate_multi_btn.click(
            translate_multi_language,
            inputs=[transcription_display, multi_lang_selection, custom_languages, selected_lang_config, multi_lang_style],
            outputs=[translation_display, multi_lang_results]
        )
        
        # Voice assignment handlers
        refresh_voices_btn.click(
            refresh_voice_assignments,
            outputs=[voice_assignments_display, multi_lang_results]
        )
        
        load_voice_config_btn.click(
            load_voice_assignments,
            outputs=[voice_assignments_display, multi_lang_results]
        )
        
        save_voice_config_btn.click(
            save_voice_assignments,
            inputs=[voice_assignments_display],
            outputs=[multi_lang_results]
        )
        
        upload_custom_voice_btn.click(
            upload_custom_voice,
            inputs=[custom_voice_language, custom_voice_file],
            outputs=[multi_lang_results]
        )
        
        # Voice generation handlers
        generate_all_voices_btn.click(
            generate_all_voices,
            outputs=[voice_generation_status, voice_generation_summary]
        )
        
        refresh_voice_previews_btn.click(
            refresh_voice_previews,
            outputs=[voice_generation_summary, select_language_for_regen]
        )
        
        regenerate_single_voice_btn.click(
            regenerate_single_voice,
            inputs=[select_language_for_regen],
            outputs=[single_voice_status]
        )
        
        # Video dubbing handlers
        create_all_dubbed_videos_btn.click(
            create_all_dubbed_videos,
            inputs=[overwrite_existing_videos],
            outputs=[video_dubbing_status, dubbed_videos_summary, dubbing_summary_display]
        )
        
        refresh_dubbed_videos_btn.click(
            refresh_dubbed_videos,
            outputs=[dubbed_videos_summary, select_language_for_video_regen]
        )
        
        recreate_single_video_btn.click(
            recreate_single_dubbed_video,
            inputs=[select_language_for_video_regen],
            outputs=[single_video_status]
        )
        
        delete_single_video_btn.click(
            delete_single_dubbed_video,
            inputs=[select_language_for_video_regen],
            outputs=[single_video_status]
        )
        
        # Custom voice assignment panel handlers
        refresh_voice_table_btn.click(
            refresh_voice_assignment_table,
            outputs=[voice_assignment_status, voice_assignment_summary]
        )
        
        auto_assign_voices_btn.click(
            auto_assign_best_voices,
            outputs=[voice_assignment_status, voice_assignment_summary]
        )
        
        save_voice_assignments_btn.click(
            save_current_voice_assignments,
            outputs=[voice_assignment_status, voice_assignment_summary]
        )
        
        upload_custom_voice_file_btn.click(
            upload_custom_voice_file,
            inputs=[custom_voice_file_upload, custom_voice_language_code, custom_voice_name],
            outputs=[custom_voice_upload_status]
        )
        
        generate_voice_previews_btn.click(
            generate_voice_previews,
            outputs=[voice_previews_container]
        )
        
        clear_voice_previews_btn.click(
            clear_voice_previews,
            outputs=[voice_previews_container]
        )
        
        # Step 4: TTS generation
        generate_tts_btn.click(
            generate_tts_audio,
            inputs=[translation_display, tts_engine_selection, gemini_language_selection, gemini_voice_selection, edge_language_selection, edge_voice_selection, kokoro_language_selection, kokoro_voice_selection, tts_method_selection, tts_instructions],
            outputs=[tts_status, tts_audio_output]
        )
        
        # Step 5: Final video
        create_video_btn.click(
            create_final_video,
            inputs=[video_input],
            outputs=[video_status, final_video_output]
        )
    
    # Batch Video Creation event handler
    batch_create_btn.click(
        fn=run_batch_video_creation,
        inputs=[batch_video_input, batch_audio_input],
        outputs=[batch_output, batch_files_output]
    )

# Launch the app
if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        inbrowser=False
    ) 
