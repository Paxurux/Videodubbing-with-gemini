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

# Import dubbing pipeline components
try:
    import google.generativeai as genai
    import wave
    import requests
    from api_key_manager import APIKeyManager
    from real_gemini_service import RealGeminiService
    from final_working_tts import FinalWorkingTTS
    from simple_edge_tts import SimpleEdgeTTS, EDGE_TTS_AVAILABLE
    print("✅ Google Generative AI library available")
    print("✅ Final Working TTS service loaded")
    if EDGE_TTS_AVAILABLE:
        print("✅ Edge TTS service loaded")
    else:
        print("⚠️ Edge TTS service not available")
    DUBBING_AVAILABLE = True
    print("✅ Dubbing pipeline components loaded successfully")
    
except ImportError as e:
    DUBBING_AVAILABLE = False
    print(f"⚠️ Dubbing pipeline not available: {str(e)}")
    print("💡 To enable dubbing features, please install: pip install google-generativeai requests")

# Function to load the parakeet TDT model
def load_model():
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
    if progress is None:
        progress = lambda x, desc=None: None
    
    progress(0.1, desc="Extracting audio from video...")
    
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    audio_path = temp_audio.name
    temp_audio.close()
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        audio_path,
        '-y'
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        progress(0.2, desc="Audio extraction complete")
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        return None

def transcribe_audio(audio_file, is_music=False, progress=gr.Progress()):
    global model
    
    if model is None:
        progress(0.1, desc="Loading model...")
        model = load_model()
    
    # Handle different input types
    if isinstance(audio_file, tuple):
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()
        
        sample_rate, audio_data = audio_file
        
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        import soundfile as sf
        sf.write(temp_audio_path, audio_data, sample_rate)
        audio_path = temp_audio_path
    else:
        import soundfile as sf
        try:
            audio_data, sample_rate = sf.read(audio_file)
            
            if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
                audio_data = np.mean(audio_data, axis=1)
                
                if is_music:
                    try:
                        audio_data = audio_data / np.max(np.abs(audio_data))
                        from scipy import signal
                        b, a = signal.butter(4, 200/(sample_rate/2), 'highpass')
                        audio_data = signal.filtfilt(b, a, audio_data)
                        
                        threshold = 0.1
                        ratio = 0.5
                        audio_data = np.where(
                            np.abs(audio_data) > threshold,
                            threshold + (np.abs(audio_data) - threshold) * ratio * np.sign(audio_data),
                            audio_data
                        )
                    except ImportError:
                        pass
                
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio_path = temp_audio.name
                temp_audio.close()
                sf.write(temp_audio_path, audio_data, sample_rate)
                audio_path = temp_audio_path
            else:
                audio_path = audio_file
        except Exception:
            audio_path = audio_file
    
    progress(0.3, desc="Transcribing audio...")
    
    # Transcribe with timestamps
    output = model.transcribe([audio_path], timestamps=True)
    
    # Extract segments
    segments = []
    csv_data = []
    
    if hasattr(output[0], 'timestamp') and 'segment' in output[0].timestamp:
        for stamp in output[0].timestamp['segment']:
            segment_text = stamp['segment']
            start_time = stamp['start']
            end_time = stamp['end']
            
            if is_music:
                end_time += 0.3
                min_duration = 0.5
                if end_time - start_time < min_duration:
                    end_time = start_time + min_duration
            
            segments.append({
                "text": segment_text,
                "start": start_time,
                "end": end_time
            })
            
            csv_data.append({
                "Start (s)": f"{start_time:.2f}",
                "End (s)": f"{end_time:.2f}",
                "Segment": segment_text
            })
    
    # Create CSV
    df = pd.DataFrame(csv_data)
    csv_path = "transcript.csv"
    df.to_csv(csv_path, index=False)
    
    # Full transcript
    full_text = output[0].text if hasattr(output[0], 'text') else ""
    
    # Clean up temp file
    if isinstance(audio_path, str) and os.path.exists(audio_path) and audio_path.startswith(tempfile.gettempdir()):
        try:
            os.unlink(audio_path)
        except:
            pass
    
    progress(1.0, desc="Done!")
    
    return full_text, create_transcript_table(segments), csv_path

def transcribe_video(video_file, is_music=False, progress=gr.Progress()):
    """Transcribe the audio track from a video file"""
    audio_path = extract_audio_from_video(video_file, progress)
    if not audio_path:
        return "Error extracting audio from video", "", None
    
    return transcribe_audio(audio_path, is_music, progress)

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
        <tr>
            <td>{segment['start']:.2f}</td>
            <td>{segment['end']:.2f}</td>
            <td>{segment['text']}</td>
        </tr>
        """
    
    html += "</table>"
    return html

# Dubbing functions
def save_asr_results(segments, video_path=None):
    """Save ASR results for dubbing pipeline."""
    if not segments:
        return False
        
    asr_data = []
    for segment in segments:
        asr_data.append({
            "start": float(segment["start"]),
            "end": float(segment["end"]), 
            "text": str(segment["text"]).strip(),
            "duration": float(segment["end"]) - float(segment["start"])
        })
    
    with open("original_asr.json", "w", encoding="utf-8") as f:
        json.dump(asr_data, f, indent=2, ensure_ascii=False)
    
    return True

def load_asr_results():
    """Load existing ASR results."""
    try:
        if os.path.exists("original_asr.json"):
            with open("original_asr.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading ASR results: {str(e)}")
        return []

def run_dubbing_pipeline(mode, video_file, api_keys_text, voice_name, manual_translation, skip_asr):
    """Run the dubbing pipeline."""
    if not DUBBING_AVAILABLE:
        return "❌ Dubbing pipeline not available", None, None
    
    try:
        if not api_keys_text.strip():
            return "❌ No API keys provided", None, None
        
        api_keys = [key.strip() for key in api_keys_text.strip().split('\n') if key.strip()]
        
        # Initialize TTS service
        tts_service = FinalWorkingTTS(api_keys[0], voice_name)
        
        # Get transcription data
        asr_data = load_asr_results()
        if not asr_data and not skip_asr:
            return "❌ No ASR results found. Please run transcription first.", None, None
        
        # Handle translation
        if mode == "automatic":
            real_service = RealGeminiService(api_keys)
            
            style_json = {
                "target_language": "Hindi",
                "tone": "neutral",
                "dialect": "hindi_devanagari",
                "genre": "general"
            }
            
            def progress_callback(progress, message):
                print(f"Translation Progress: {progress:.1%} - {message}")
            
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
        
        # Generate TTS
        def tts_progress_callback(progress, message):
            print(f"TTS Progress: {progress:.1%} - {message}")
        
        final_audio = tts_service.process_subtitle_json(
            translated_segments, tts_progress_callback
        )
        
        # Create final video if provided
        if video_file:
            try:
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
                return f"✅ Dubbing completed!\n🎬 Video: {dubbed_video_path}\n🎵 Audio: {final_audio}", dubbed_video_path, final_audio
            except Exception as e:
                return f"✅ TTS generated!\n🎵 Audio: {final_audio}\n⚠️ Video creation failed: {str(e)}", None, final_audio
        else:
            return f"✅ TTS generated!\n🎵 Audio: {final_audio}", None, final_audio
        
    except Exception as e:
        return f"❌ Pipeline failed: {str(e)}", None, None

# Create simple Gradio interface
with gr.Blocks(css="footer {visibility: hidden}") as app:
    gr.Markdown("# 🎤 Parakeet-TDT ASR Transcription")
    gr.Markdown("Upload audio/video files or record from microphone to get timestamped transcriptions")
    
    with gr.Tab("🎤 Transcription"):
        with gr.Tab("📁 Audio/Video File"):
            with gr.Row():
                with gr.Column():
                    audio_input = gr.File(
                        label="Upload Audio/Video File",
                        file_types=["audio", "video"]
                    )
                    
                    is_music = gr.Checkbox(
                        label="Music Mode",
                        value=False,
                        info="Enable for better accuracy with songs/music"
                    )
                    
                    transcribe_btn = gr.Button("🎤 Transcribe", variant="primary", size="lg")
                
                with gr.Column():
                    transcript_output = gr.Textbox(
                        label="Full Transcript",
                        lines=10,
                        interactive=False
                    )
                    
                    transcript_table = gr.HTML(label="Interactive Transcript")
                    
                    with gr.Row():
                        csv_download = gr.File(label="Download CSV")
                        save_for_dubbing_btn = gr.Button("💾 Save for Dubbing", variant="secondary")
        
        with gr.Tab("🎙️ Microphone"):
            with gr.Row():
                with gr.Column():
                    mic_input = gr.Audio(
                        label="Record from Microphone",
                        sources=["microphone"],
                        type="numpy"
                    )
                    
                    mic_is_music = gr.Checkbox(
                        label="Music Mode",
                        value=False,
                        info="Enable for singing or music content"
                    )
                    
                    mic_transcribe_btn = gr.Button("🎤 Transcribe Recording", variant="primary", size="lg")
                
                with gr.Column():
                    mic_transcript_output = gr.Textbox(
                        label="Transcript from Microphone",
                        lines=10,
                        interactive=False
                    )
                    
                    mic_transcript_table = gr.HTML(label="Interactive Transcript")
                    
                    with gr.Row():
                        mic_csv_download = gr.File(label="Download CSV")
                        mic_save_for_dubbing_btn = gr.Button("💾 Save for Dubbing", variant="secondary")
    
    if DUBBING_AVAILABLE:
        with gr.Tab("🎬 Dubbing Pipeline"):
            gr.Markdown("## 🎬 Video Dubbing Pipeline")
            gr.Markdown("Complete dubbing workflow: Transcribe → Translate → Generate TTS → Create dubbed video")
            
            with gr.Group():
                gr.Markdown("### 🔑 API Configuration")
                api_keys_input = gr.Textbox(
                    label="Gemini API Keys (one per line)",
                    placeholder="Enter your Gemini API keys here...",
                    lines=3,
                    type="password"
                )
            
            with gr.Group():
                gr.Markdown("### 📹 Video Input")
                video_input = gr.File(
                    label="Upload Video File",
                    file_types=["video"]
                )
            
            with gr.Group():
                gr.Markdown("### 🎙️ Voice Configuration")
                voice_name_input = gr.Textbox(
                    label="Voice Name",
                    value="Kore",
                    placeholder="Enter voice name (e.g., Kore, Puck, Zephyr)"
                )
            
            with gr.Group():
                gr.Markdown("### 🌐 Translation Mode")
                dubbing_mode = gr.Radio(
                    label="Dubbing Mode",
                    choices=[
                        ("🤖 Automatic Translation", "automatic"),
                        ("📝 Manual Translation", "manual")
                    ],
                    value="automatic"
                )
                
                manual_translation_input = gr.Textbox(
                    label="Manual Translation (JSON format)",
                    lines=8,
                    placeholder='[{"start": 0.0, "end": 4.5, "text_translated": "Your translation here"}]',
                    visible=False
                )
                
                skip_asr_checkbox = gr.Checkbox(
                    label="Skip ASR (use existing transcription)",
                    value=False
                )
            
            run_dubbing_btn = gr.Button("🚀 Run Dubbing Pipeline", variant="primary", size="lg")
            
            dubbing_output = gr.Textbox(
                label="Dubbing Results",
                lines=5,
                interactive=False
            )
            
            with gr.Row():
                dubbed_video_output = gr.File(label="Download Dubbed Video")
                dubbed_audio_output = gr.File(label="Download Dubbed Audio")
    
    # Event handlers
    def handle_transcribe(audio_file, is_music_mode):
        if audio_file is None:
            return "Please upload an audio or video file first.", "", None
        
        # Extract segments for saving
        full_text, table_html, csv_file = transcribe_audio(audio_file, is_music_mode)
        
        # Parse segments from the model output for saving
        global model
        if model is not None:
            try:
                output = model.transcribe([audio_file], timestamps=True)
                segments = []
                if hasattr(output[0], 'timestamp') and 'segment' in output[0].timestamp:
                    for stamp in output[0].timestamp['segment']:
                        segments.append({
                            "text": stamp['segment'],
                            "start": stamp['start'],
                            "end": stamp['end']
                        })
                
                # Store segments globally for save button
                global current_segments
                current_segments = segments
            except:
                current_segments = []
        
        return full_text, table_html, csv_file
    
    def save_current_transcription():
        global current_segments
        if 'current_segments' in globals() and current_segments:
            success = save_asr_results(current_segments)
            if success:
                return "✅ Transcription saved for dubbing pipeline!"
            else:
                return "❌ Failed to save transcription"
        else:
            return "❌ No transcription to save. Please transcribe first."
    
    def toggle_manual_translation(mode):
        return gr.update(visible=(mode == "manual"))
    
    # Connect event handlers
    transcribe_btn.click(
        fn=handle_transcribe,
        inputs=[audio_input, is_music],
        outputs=[transcript_output, transcript_table, csv_download]
    )
    
    mic_transcribe_btn.click(
        fn=handle_transcribe,
        inputs=[mic_input, mic_is_music],
        outputs=[mic_transcript_output, mic_transcript_table, mic_csv_download]
    )
    
    save_for_dubbing_btn.click(
        fn=save_current_transcription,
        outputs=[transcript_output]
    )
    
    mic_save_for_dubbing_btn.click(
        fn=save_current_transcription,
        outputs=[mic_transcript_output]
    )
    
    if DUBBING_AVAILABLE:
        dubbing_mode.change(
            fn=toggle_manual_translation,
            inputs=[dubbing_mode],
            outputs=[manual_translation_input]
        )
        
        run_dubbing_btn.click(
            fn=run_dubbing_pipeline,
            inputs=[
                dubbing_mode,
                video_input,
                api_keys_input,
                voice_name_input,
                manual_translation_input,
                skip_asr_checkbox
            ],
            outputs=[dubbing_output, dubbed_video_output, dubbed_audio_output]
        )

# Global variable to store current segments
current_segments = []

# Launch the app
if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )