# Custom Voice Assignment Panel ✅

## 🎯 Status: FULLY IMPLEMENTED AND INTEGRATED!

The custom voice assignment panel has been successfully implemented with dynamic language detection, comprehensive voice selection, custom voice uploads, and preview functionality.

## ✅ Features Implemented

### **🎤 Dynamic Voice Assignment Panel**
- **Language Detection**: Automatically detects translated languages from translation files
- **Voice Assignment Table**: Dynamic table with one row per language
- **Comprehensive Voice Database**: Supports Gemini, Edge TTS, Kokoro, and custom voices
- **Auto Assignment**: Intelligent voice assignment with priority-based selection
- **Custom Voice Upload**: Upload and manage custom voice files

### **📜 Voice Assignment Table**
- **Dynamic Generation**: Creates table based on detected translated languages
- **Voice Dropdowns**: Populated with available voices for each language
- **TTS Engine Display**: Shows which engine provides each voice
- **Current Assignment**: Displays currently assigned voice for each language
- **Test Voice Button**: Preview functionality for each voice assignment

### **🧩 Custom Voice Upload System**
- **File Upload**: Supports .wav and .mp3 files
- **Language Mapping**: Associates custom voices with specific languages
- **Organized Storage**: Saves files in `/custom_voices/` directory
- **Automatic Registration**: Adds uploaded voices to available voice database
- **Naming Convention**: `[voice_name]_[language_code].wav` format

## 🔧 Technical Implementation

### **CustomVoiceAssignmentPanel Class**
```python
class CustomVoiceAssignmentPanel:
    def __init__(self):
        self.custom_voices_dir = Path("custom_voices")
        self.voice_assignments_file = "voice_assignments.json"
        self.available_voices = self._load_available_voices()
    
    def get_detected_languages(self) -> Dict[str, str]:
        """Get detected translated languages from translation files."""
        
    def create_voice_assignment_table_data(self) -> List[Dict[str, Any]]:
        """Create data for the voice assignment table."""
        
    def upload_custom_voice(self, voice_file_path: str, language_code: str, voice_name: str) -> Tuple[bool, str]:
        """Upload a custom voice file."""
```

### **Comprehensive Voice Database**
```python
available_voices = {
    "gemini": {
        "en": ["gemini_en_soft", "gemini_en_deep", "gemini_en_natural"],
        "hi": ["gemini_hi_deep", "gemini_hi_soft", "gemini_hi_natural"],
        "es": ["gemini_es_soft", "gemini_es_deep", "gemini_es_natural"],
        # ... more languages
    },
    "edge": {
        "en": ["en-US-AriaNeural", "en-US-DavisNeural", "en-US-GuyNeural"],
        "hi": ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
        "es": ["es-US-AlonsoNeural", "es-US-PalomaNeural"],
        # ... comprehensive voice library
    },
    "kokoro": {
        "en": ["af_heart", "af_bella", "af_sarah", "am_adam", "am_michael"],
        "ja": ["af_heart", "af_bella", "jf_alpha", "jm_beta"],
        # ... supported languages
    },
    "custom": {}  # Populated with uploaded voices
}
```

## 🎛️ User Interface Components

### **Voice Assignment Table**
```python
# Dynamic table generation for each detected language
for data in table_data:
    lang_code = data["language_code"]
    lang_name = data["language_name"]
    voice_options = data["voice_options"]
    current_voice = data["current_voice"]
    
    # Create dropdown with available voices
    voice_dropdown = gr.Dropdown(
        label=f"{lang_name} Voice",
        choices=voice_options,
        value=current_voice
    )
    
    # Test voice button
    test_voice_btn = gr.Button(f"🧪 Test {lang_code}")
```

### **Custom Voice Upload**
```python
custom_voice_file_upload = gr.File(
    label="Upload Voice File (.wav or .mp3)",
    file_types=[".wav", ".mp3"],
    type="filepath"
)

custom_voice_language_code = gr.Textbox(
    label="Language Code",
    placeholder="e.g., hi, es, ja"
)

custom_voice_name = gr.Textbox(
    label="Voice Name", 
    placeholder="e.g., my_custom_voice_hi"
)
```

### **Voice Preview System**
```python
# Generate previews for assigned voices
for lang_code, assignment in assignments.items():
    preview_text = generate_voice_preview_text(lang_code)
    
    # Create preview component
    preview_component = gr.Audio(
        label=f"{lang_name} ({voice_name}) - {engine.title()} TTS",
        value=None,  # Will be populated with generated preview
        autoplay=False
    )
```

## 📊 Language Detection Process

### **1. Scan Translation Files**
```python
# Detect languages from translation directory
for json_file in translations_dir.glob("transcript_*.json"):
    lang_code = json_file.stem.replace("transcript_", "")
    if lang_code != "original":
        simple_code = get_simple_language_code(lang_code)
        language_name = language_names.get(lang_code, lang_code.upper())
        detected_languages[simple_code] = language_name
```

### **2. Map to Voice Database**
```python
# Convert full language codes to simple codes for voice matching
code_mapping = {
    "ar-EG": "ar", "de-DE": "de", "es-US": "es", "fr-FR": "fr",
    "hi-IN": "hi", "ja-JP": "ja", "ko-KR": "ko", "pt-BR": "pt",
    # ... comprehensive mapping
}
```

### **3. Create Assignment Table**
```python
# For each detected language
for lang_code, lang_name in detected_languages.items():
    available_voices = get_available_voices_for_language(lang_code)
    
    # Create voice options list
    voice_options = []
    for engine, voices in available_voices.items():
        for voice in voices:
            voice_options.append(f"{engine}:{voice}")
```

## 🎯 Auto Assignment Logic

### **Priority-Based Selection**
```python
# Priority order: custom > gemini > edge > kokoro
engine_priority = ["custom", "gemini", "edge", "kokoro"]

for lang_code, lang_name in detected_languages.items():
    available_voices = get_available_voices_for_language(lang_code)
    
    # Find best engine and voice
    for engine in engine_priority:
        if engine in available_voices and available_voices[engine]:
            voice = available_voices[engine][0]  # Use first voice
            auto_assignments[lang_code] = {
                "engine": engine,
                "voice": voice,
                "source": "auto_assigned"
            }
            break
```

### **Assignment Results**
```json
{
  "hi": {"engine": "custom", "voice": "my_custom_voice_hi", "source": "auto_assigned"},
  "es": {"engine": "edge", "voice": "es-ES-AlvaroNeural", "source": "auto_assigned"},
  "ja": {"engine": "kokoro", "voice": "jf_alpha", "source": "auto_assigned"}
}
```

## 🧩 Custom Voice Upload Process

### **1. File Upload**
```python
def upload_custom_voice(voice_file_path: str, language_code: str, voice_name: str):
    # Clean voice name
    clean_voice_name = "".join(c for c in voice_name if c.isalnum() or c in "_-")
    
    # Create filename with language code
    filename = f"{clean_voice_name}_{language_code}.wav"
    destination = custom_voices_dir / filename
    
    # Copy uploaded file
    shutil.copy2(voice_file_path, destination)
```

### **2. Registration**
```python
# Update available voices database
if language_code not in available_voices["custom"]:
    available_voices["custom"][language_code] = []

voice_id = f"{clean_voice_name}_{language_code}"
available_voices["custom"][language_code].append(voice_id)
```

### **3. File Organization**
```
custom_voices/
├── my_custom_voice_hi_hi.wav    # Hindi custom voice
├── professional_voice_es.wav    # Spanish custom voice
├── anime_voice_ja_ja.wav        # Japanese custom voice
└── narrator_voice_en_en.wav     # English custom voice
```

## 🎧 Voice Preview System

### **Preview Text Generation**
```python
preview_texts = {
    "en": "Hello world, this is a voice preview test.",
    "hi": "नमस्ते दुनिया, यह एक आवाज़ पूर्वावलोकन परीक्षण है।",
    "es": "Hola mundo, esta es una prueba de vista previa de voz.",
    "ja": "こんにちは世界、これは音声プレビューテストです。",
    "fr": "Bonjour le monde, ceci est un test d'aperçu vocal.",
    # ... comprehensive preview texts
}
```

### **Preview Generation**
```python
# For each assigned voice
for lang_code, assignment in assignments.items():
    engine = assignment.get("engine")
    voice = assignment.get("voice")
    preview_text = generate_voice_preview_text(lang_code)
    
    # Generate short audio preview
    preview_audio = generate_preview_audio(preview_text, engine, voice)
    
    # Create preview component
    preview_component = f"🔊 {lang_name} ({voice}) – Play"
```

## 🔒 Save & Apply System

### **JSON Schema**
```json
{
  "hi": {
    "engine": "custom",
    "voice": "my_custom_voice_hi",
    "source": "manual"
  },
  "es": {
    "engine": "edge", 
    "voice": "es-ES-AlvaroNeural",
    "source": "manual"
  },
  "ja": {
    "engine": "kokoro",
    "voice": "jf_alpha",
    "source": "manual"
  }
}
```

### **Persistence**
```python
def save_voice_assignments(assignments: Dict[str, Dict[str, str]]) -> bool:
    with open(voice_assignments_file, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
    return True

def load_voice_assignments() -> Dict[str, Dict[str, str]]:
    if os.path.exists(voice_assignments_file):
        with open(voice_assignments_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
```

## 🛡️ Safety Features

### **✅ File Validation**
- **File Type Check**: Only accepts .wav and .mp3 files
- **Name Sanitization**: Removes special characters from voice names
- **Language Code Validation**: Ensures valid language codes
- **Duplicate Prevention**: Handles duplicate voice names gracefully

### **✅ Error Handling**
```python
try:
    # Upload custom voice
    shutil.copy2(voice_file_path, destination)
    return True, f"✅ Custom voice uploaded: {filename}"
except Exception as e:
    error_msg = f"❌ Error uploading custom voice: {str(e)}"
    return False, error_msg
```

### **✅ Data Integrity**
- **JSON Validation**: Validates assignment data before saving
- **Backup Handling**: Preserves existing assignments on errors
- **Consistent Schema**: Maintains strict JSON structure
- **Recovery Options**: Provides clear error messages for recovery

## 🚀 Integration with Pipeline

### **Seamless Workflow**
```python
# Complete pipeline integration:
# 1. Translation → 2. Custom Voice Assignment → 3. Voice Generation → 4. Video Dubbing

# After translation
detected_languages = panel.get_detected_languages()

# Custom voice assignment
assignments = panel.create_voice_assignment_table_data()

# Voice generation uses assignments
voice_generator.generate_all_voices(assignments)

# Video dubbing uses generated voices
video_dubber.create_all_dubbed_videos()
```

### **UI Integration**
- **Progressive Disclosure**: Panel appears after translation
- **Dynamic Updates**: Table updates based on detected languages
- **Status Feedback**: Real-time status updates and error messages
- **Consistent Design**: Matches existing UI patterns and styling

## 📋 Assignment Summary

### **Comprehensive Summary Display**
```
🎤 Voice Assignment Summary (3 languages):
==================================================
  Hindi (hi): 📁 Custom: my_custom_voice_hi
  Spanish (es): ✅ Edge: es-ES-AlvaroNeural  
  Japanese (ja): ✅ Kokoro: jf_alpha
```

### **Status Indicators**
- **✅ Assigned**: Voice successfully assigned
- **📁 Custom**: Custom uploaded voice
- **🤖 Auto**: Auto-assigned voice
- **❌ Missing**: No voice available

## 🎉 Benefits

### **✅ User Friendly**
- **Visual Interface**: Clear table layout with dropdowns
- **One-Click Operations**: Auto assignment and save functions
- **Custom Upload**: Simple drag-and-drop voice upload
- **Preview System**: Test voices before final generation

### **✅ Flexible & Powerful**
- **Multi-Engine Support**: Works with all TTS engines
- **Custom Voice Support**: Upload any voice for any language
- **Priority System**: Intelligent auto-assignment logic
- **Session Persistence**: Saves assignments across sessions

### **✅ Production Ready**
- **Robust Error Handling**: Comprehensive error recovery
- **File Management**: Organized storage with consistent naming
- **Data Validation**: Strict JSON schema validation
- **Integration Ready**: Seamless pipeline integration

The custom voice assignment panel is now **fully integrated** and provides comprehensive voice management capabilities with dynamic language detection, custom voice uploads, and seamless integration with the dubbing pipeline! 🚀