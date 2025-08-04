# Gemini TTS Complete Guide 🤖

## 🎯 Overview
This document explains how Gemini TTS works in the Mipax dubbing pipeline, what data is sent to the API, and how to replicate this functionality in a standalone recap application.

## 🔄 Current System Architecture

### 1. **Data Flow in Mipax Pipeline**
```
Audio/Video Input → ASR Transcription → Translation → Gemini TTS → Audio Output
```

### 2. **What Gets Sent to Gemini TTS**
The system sends **translated text segments** with timing information, NOT the original audio:

```json
[
  {
    "start": 0.0,
    "end": 4.5,
    "text_translated": "नमस्ते सब लोग, मैं मिपैक्स बोल रहा हूँ।"
  },
  {
    "start": 4.5,
    "end": 9.8,
    "text_translated": "आज हम वन पीस की ताज़ा थ्योरीज़ पर बात करने वाले हैं।"
  }
]
```

### 3. **Gemini TTS Processing Methods**

#### **Method A: Individual Segments** (Default)
- Each segment processed separately
- One API call per segment
- Better for error recovery
- More API calls = higher cost

#### **Method B: Single Request** (Optimized)
- All segments combined into one request
- Single API call for entire script
- Better timing consistency
- Lower cost, faster processing

## 📊 Data Transfer Analysis

### **Input Data Structure**
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 4.5,
      "text_translated": "Hello everyone, this is Mipax speaking.",
      "duration": 4.5
    }
  ],
  "voice": "Kore",
  "instructions": "Speak with excitement and energy"
}
```

### **Data Size Estimation**
- **Average segment**: ~50-100 characters
- **10-minute video**: ~150 segments
- **Total text data**: ~7,500-15,000 characters
- **JSON overhead**: ~2x text size
- **Total payload**: ~15-30 KB per request

### **API Call Patterns**
```python
# Individual Method: 150 segments = 150 API calls
for segment in segments:
    gemini_tts_call(segment.text, voice, duration)

# Single Request Method: 150 segments = 1 API call
combined_text = join_all_segments(segments)
gemini_tts_call(combined_text, voice, instructions)
```

## 🛠️ Technical Implementation

### **Core Gemini TTS Service**
```python
class GeminiTTSService:
    def __init__(self, api_key: str, voice: str = "Kore"):
        self.api_key = api_key
        self.voice = voice
        self.client = genai.configure(api_key=api_key)
    
    def generate_tts(self, text: str, voice: str = None) -> bytes:
        """Generate TTS audio from text"""
        response = genai.generate_content(
            model="gemini-2.5-pro-preview-tts",
            contents=[{
                "parts": [{
                    "text": text,
                    "voice": voice or self.voice
                }]
            }]
        )
        return response.audio_data
    
    def process_segments(self, segments: List[Dict]) -> str:
        """Process multiple segments"""
        for i, segment in enumerate(segments):
            audio_data = self.generate_tts(
                text=segment["text_translated"],
                voice=self.voice
            )
            
            # Save to file
            output_file = f"tts_chunk_{i:03d}.wav"
            with open(output_file, "wb") as f:
                f.write(audio_data)
```

### **Single Request Optimization**
```python
def process_single_request(self, segments: List[Dict], instructions: str = "") -> str:
    """Process all segments in single API call"""
    
    # Combine all text with timing markers
    combined_text = self._build_combined_script(segments, instructions)
    
    # Single API call
    audio_data = self.generate_tts(combined_text, self.voice)
    
    # Save combined audio
    output_file = "combined_tts_output.wav"
    with open(output_file, "wb") as f:
        f.write(audio_data)
    
    return output_file

def _build_combined_script(self, segments: List[Dict], instructions: str) -> str:
    """Build combined script with timing cues"""
    script_parts = []
    
    if instructions:
        script_parts.append(f"Instructions: {instructions}")
    
    for segment in segments:
        duration = segment["end"] - segment["start"]
        text = segment["text_translated"]
        
        # Add timing context
        script_parts.append(f"[{duration:.1f}s] {text}")
    
    return " ".join(script_parts)
```

## 🎬 Standalone Recap App Implementation

### **1. Basic Recap App Structure**
```python
import gradio as gr
import google.generativeai as genai
import json

class RecapTTSApp:
    def __init__(self):
        self.gemini_service = None
    
    def create_interface(self):
        with gr.Blocks() as app:
            gr.Markdown("# 🎤 Recap TTS Generator")
            
            # API Key Input
            api_key = gr.Textbox(
                label="Gemini API Key",
                type="password",
                placeholder="Enter your Gemini API key"
            )
            
            # Voice Selection
            voice_selection = gr.Dropdown(
                label="Select Voice",
                choices=["Kore", "Puck", "Zephyr", "Charon", "Fenrir", "Leda", "Orus", "Aoede"],
                value="Kore"
            )
            
            # Input Methods
            with gr.Tabs():
                # Tab 1: Plain Text
                with gr.TabItem("📝 Plain Text"):
                    text_input = gr.Textbox(
                        label="Enter text to convert to speech",
                        lines=5,
                        placeholder="Type your recap text here..."
                    )
                    generate_text_btn = gr.Button("🎵 Generate TTS")
                
                # Tab 2: JSON with Timestamps
                with gr.TabItem("📋 JSON with Timestamps"):
                    json_input = gr.Textbox(
                        label="JSON Input (with timestamps)",
                        lines=10,
                        placeholder='''[
  {"start": 0.0, "end": 4.5, "text": "Hello everyone, welcome to today's recap."},
  {"start": 4.5, "end": 9.0, "text": "Let's dive into the main topics."}
]''',
                        info="Provide segments with start, end, and text fields"
                    )
                    generate_json_btn = gr.Button("🎵 Generate from JSON")
                
                # Tab 3: Script with Timestamps
                with gr.TabItem("📜 Script Format"):
                    script_input = gr.Textbox(
                        label="Script with Timestamps",
                        lines=10,
                        placeholder='''[00:00 - 00:04] Hello everyone, welcome to today's recap.
[00:04 - 00:09] Let's dive into the main topics.
[00:09 - 00:15] First, we'll discuss the latest developments.''',
                        info="Format: [MM:SS - MM:SS] Text content"
                    )
                    generate_script_btn = gr.Button("🎵 Generate from Script")
            
            # Output
            audio_output = gr.Audio(label="Generated TTS Audio")
            status_output = gr.Textbox(label="Status", lines=3)
            
            # Event handlers
            generate_text_btn.click(
                self.generate_from_text,
                inputs=[api_key, voice_selection, text_input],
                outputs=[audio_output, status_output]
            )
            
            generate_json_btn.click(
                self.generate_from_json,
                inputs=[api_key, voice_selection, json_input],
                outputs=[audio_output, status_output]
            )
            
            generate_script_btn.click(
                self.generate_from_script,
                inputs=[api_key, voice_selection, script_input],
                outputs=[audio_output, status_output]
            )
        
        return app
```

### **2. Processing Methods**
```python
def generate_from_text(self, api_key: str, voice: str, text: str):
    """Generate TTS from plain text"""
    try:
        if not api_key or not text:
            return None, "❌ Please provide API key and text"
        
        # Initialize Gemini service
        self.gemini_service = GeminiTTSService(api_key, voice)
        
        # Generate TTS
        audio_data = self.gemini_service.generate_tts(text, voice)
        
        # Save to file
        output_file = "recap_tts_output.wav"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        return output_file, f"✅ TTS generated successfully!\n🎤 Voice: {voice}\n📝 Text length: {len(text)} characters"
        
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

def generate_from_json(self, api_key: str, voice: str, json_input: str):
    """Generate TTS from JSON segments"""
    try:
        if not api_key or not json_input:
            return None, "❌ Please provide API key and JSON input"
        
        # Parse JSON
        segments = json.loads(json_input)
        
        # Validate segments
        if not self._validate_segments(segments):
            return None, "❌ Invalid JSON format. Please check your segments."
        
        # Initialize service
        self.gemini_service = GeminiTTSService(api_key, voice)
        
        # Process segments
        output_file = self.gemini_service.process_segments(segments)
        
        total_duration = segments[-1]["end"] if segments else 0
        
        return output_file, f"""✅ TTS generated from JSON!
🎤 Voice: {voice}
📊 Segments: {len(segments)}
⏱️ Total duration: {total_duration:.1f}s
💰 API calls: {len(segments)}"""
        
    except json.JSONDecodeError:
        return None, "❌ Invalid JSON format"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

def generate_from_script(self, api_key: str, voice: str, script_input: str):
    """Generate TTS from script format"""
    try:
        if not api_key or not script_input:
            return None, "❌ Please provide API key and script"
        
        # Parse script format
        segments = self._parse_script_format(script_input)
        
        if not segments:
            return None, "❌ No valid segments found in script"
        
        # Initialize service
        self.gemini_service = GeminiTTSService(api_key, voice)
        
        # Process segments
        output_file = self.gemini_service.process_segments(segments)
        
        return output_file, f"""✅ TTS generated from script!
🎤 Voice: {voice}
📊 Segments: {len(segments)}
📝 Format: Script with timestamps"""
        
    except Exception as e:
        return None, f"❌ Error: {str(e)}"
```

### **3. Utility Functions**
```python
def _validate_segments(self, segments: List[Dict]) -> bool:
    """Validate JSON segments format"""
    required_fields = ["start", "end", "text"]
    
    for segment in segments:
        if not isinstance(segment, dict):
            return False
        
        for field in required_fields:
            if field not in segment:
                return False
        
        # Validate timing
        try:
            start = float(segment["start"])
            end = float(segment["end"])
            if start >= end:
                return False
        except (ValueError, TypeError):
            return False
    
    return True

def _parse_script_format(self, script: str) -> List[Dict]:
    """Parse script format: [MM:SS - MM:SS] Text"""
    import re
    
    segments = []
    lines = script.strip().split('\n')
    
    for line in lines:
        # Match pattern: [MM:SS - MM:SS] Text
        match = re.match(r'\[(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})\]\s*(.+)', line.strip())
        
        if match:
            start_min, start_sec, end_min, end_sec, text = match.groups()
            
            start_time = int(start_min) * 60 + int(start_sec)
            end_time = int(end_min) * 60 + int(end_sec)
            
            segments.append({
                "start": start_time,
                "end": end_time,
                "text": text.strip()
            })
    
    return segments
```

## 💰 Cost & Performance Analysis

### **API Usage Patterns**
```python
# Cost Estimation
def estimate_cost(segments: List[Dict], method: str = "individual"):
    """Estimate Gemini TTS API cost"""
    
    if method == "individual":
        api_calls = len(segments)
        total_chars = sum(len(seg["text"]) for seg in segments)
    else:  # single_request
        api_calls = 1
        total_chars = sum(len(seg["text"]) for seg in segments)
    
    # Gemini TTS pricing (example rates)
    cost_per_call = 0.01  # $0.01 per API call
    cost_per_char = 0.0001  # $0.0001 per character
    
    total_cost = (api_calls * cost_per_call) + (total_chars * cost_per_char)
    
    return {
        "api_calls": api_calls,
        "total_characters": total_chars,
        "estimated_cost": total_cost,
        "method": method
    }
```

### **Performance Optimization**
```python
# Chunking Strategy for Large Scripts
def optimize_segments(segments: List[Dict], max_chars_per_call: int = 5000):
    """Optimize segments for API efficiency"""
    
    optimized_chunks = []
    current_chunk = []
    current_chars = 0
    
    for segment in segments:
        segment_chars = len(segment["text"])
        
        if current_chars + segment_chars > max_chars_per_call and current_chunk:
            # Save current chunk
            optimized_chunks.append(current_chunk)
            current_chunk = [segment]
            current_chars = segment_chars
        else:
            current_chunk.append(segment)
            current_chars += segment_chars
    
    if current_chunk:
        optimized_chunks.append(current_chunk)
    
    return optimized_chunks
```

## 🎯 Data Transfer Specifications

### **Minimum Required Data**
```json
{
  "text": "Hello world",
  "voice": "Kore"
}
```

### **Complete Data Structure**
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 4.5,
      "text": "Hello everyone, this is a recap.",
      "duration": 4.5,
      "speaker": "narrator",
      "language": "en",
      "emphasis": "normal"
    }
  ],
  "voice": "Kore",
  "instructions": "Speak clearly and with enthusiasm",
  "speed": 1.0,
  "pitch": 0.0,
  "volume": 1.0
}
```

### **Batch Processing Example**
```python
def process_large_script(segments: List[Dict], batch_size: int = 50):
    """Process large scripts in batches"""
    
    results = []
    total_batches = len(segments) // batch_size + (1 if len(segments) % batch_size else 0)
    
    for i in range(0, len(segments), batch_size):
        batch = segments[i:i + batch_size]
        
        print(f"Processing batch {i//batch_size + 1}/{total_batches}")
        
        # Process batch
        batch_result = self.gemini_service.process_segments(batch)
        results.append(batch_result)
        
        # Rate limiting
        time.sleep(1)  # 1 second between batches
    
    return results
```

## 🚀 Quick Start Template

### **Minimal Recap App**
```python
import gradio as gr
import google.generativeai as genai

def create_recap_app():
    def generate_recap_tts(api_key, voice, text):
        try:
            genai.configure(api_key=api_key)
            
            response = genai.generate_content(
                model="gemini-2.5-pro-preview-tts",
                contents=[{
                    "parts": [{
                        "text": text,
                        "voice": voice
                    }]
                }]
            )
            
            # Save audio
            with open("recap_output.wav", "wb") as f:
                f.write(response.audio_data)
            
            return "recap_output.wav", "✅ Recap TTS generated!"
            
        except Exception as e:
            return None, f"❌ Error: {str(e)}"
    
    with gr.Blocks() as app:
        gr.Markdown("# 🎤 Quick Recap TTS")
        
        api_key = gr.Textbox(label="Gemini API Key", type="password")
        voice = gr.Dropdown(
            label="Voice", 
            choices=["Kore", "Puck", "Zephyr", "Charon"],
            value="Kore"
        )
        text = gr.Textbox(label="Recap Text", lines=5)
        
        generate_btn = gr.Button("🎵 Generate TTS")
        
        audio_output = gr.Audio(label="Generated Audio")
        status = gr.Textbox(label="Status")
        
        generate_btn.click(
            generate_recap_tts,
            inputs=[api_key, voice, text],
            outputs=[audio_output, status]
        )
    
    return app

# Launch app
if __name__ == "__main__":
    app = create_recap_app()
    app.launch()
```

## 📋 Summary

### **Key Points**
- ✅ Gemini TTS receives **text data only**, not audio
- ✅ Data size: ~15-30 KB per 10-minute video
- ✅ Two methods: Individual segments vs Single request
- ✅ JSON format with timestamps is optimal
- ✅ Single request method reduces API calls by 99%
- ✅ Standalone apps can replicate full functionality
- ✅ Cost scales with text length and API calls
- ✅ Batch processing recommended for large scripts

### **Best Practices**
1. **Use Single Request method** for cost efficiency
2. **Batch large scripts** to avoid rate limits
3. **Validate JSON input** before processing
4. **Implement error handling** for API failures
5. **Cache API keys** securely
6. **Monitor usage** to control costs
7. **Optimize text length** for better performance

This guide provides everything needed to understand and replicate Gemini TTS functionality in any application! 🚀