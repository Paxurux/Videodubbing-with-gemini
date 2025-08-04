# Dubbing Pipeline User Manual

A comprehensive guide to using the Dubbing Pipeline system for creating dubbed videos with automatic speech recognition, translation, and text-to-speech synthesis.

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Interface Guide](#user-interface-guide)
3. [Automatic Mode](#automatic-mode)
4. [Manual Mode](#manual-mode)
5. [Configuration Options](#configuration-options)
6. [File Management](#file-management)
7. [Quality Control](#quality-control)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

## Getting Started

### System Requirements

**Minimum Requirements:**
- Windows 10, macOS 10.15, or Linux (Ubuntu 18.04+)
- Python 3.8+
- 8GB RAM
- 10GB free disk space
- Stable internet connection

**Recommended:**
- 16GB+ RAM
- NVIDIA GPU with 4GB+ VRAM
- 50GB+ free disk space
- High-speed internet (100+ Mbps)

### Installation

1. **Download and Setup:**
   ```bash
   git clone <repository-url>
   cd dubbing-pipeline
   pip install -r requirements.txt
   ```

2. **Install FFmpeg:**
   - **Windows:** Download from https://ffmpeg.org and add to PATH
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`

3. **Get API Keys:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create one or more Gemini API keys
   - Keep keys secure and never share them

4. **Launch Application:**
   ```bash
   python app.py
   ```
   - Open browser to http://localhost:7860

### First Run

1. **Test Your Setup:**
   - Upload a short video (under 2 minutes)
   - Use the transcription tab first
   - Verify ASR results before dubbing

2. **Configure API Keys:**
   - Enter your Gemini API keys in the dubbing tab
   - Use multiple keys for better reliability
   - Test keys with a small translation first

## User Interface Guide

### Main Interface Layout

The application has three main tabs:

#### 1. Transcription Tab
- **Purpose:** Convert speech to text with timestamps
- **Input:** Audio/video files or microphone recording
- **Output:** Timestamped transcription in multiple formats

#### 2. Dubbing Pipeline Tab
- **Purpose:** Create dubbed videos from transcriptions
- **Modes:** Automatic (AI translation) or Manual (user-provided translation)
- **Output:** Dubbed video file

#### 3. Help Tab
- **Purpose:** Documentation and troubleshooting
- **Content:** Usage guides, examples, and support information

### Navigation Tips

- **Progress Tracking:** Real-time progress bars show current operation status
- **Error Messages:** Clear error messages appear in red text boxes
- **File Downloads:** Completed files appear as download links
- **State Persistence:** Your work is automatically saved between sessions

## Automatic Mode

Automatic mode uses AI to translate your content and create dubbed videos with minimal user input.

### Step-by-Step Process

#### Step 1: Transcription

1. **Go to Transcription Tab**
2. **Upload Your Video:**
   - Click "Choose File" and select your video
   - Supported formats: MP4, AVI, MOV, MKV, WebM
   - Maximum recommended size: 2GB

3. **Configure Settings:**
   - **Music Mode:** Enable for songs or music videos
   - **Chunk Duration:** Use default (10 minutes) for most content

4. **Start Transcription:**
   - Click "Transcribe Video/Audio"
   - Wait for processing (typically 1-5 minutes per minute of video)
   - Review the generated transcript

5. **Download Results:**
   - JSON format for pipeline use
   - CSV format for spreadsheet editing
   - HTML format for web viewing

#### Step 2: Automatic Dubbing

1. **Switch to Dubbing Pipeline Tab**
2. **Select Automatic Mode**
3. **Upload Video:**
   - Use the same video file from transcription
   - Or upload a different video if using existing ASR results

4. **Configure Translation:**
   - **API Keys:** Enter your Gemini API keys (one per line)
   - **Target Language:** Select from available options
   - **Style Configuration:**
     - **Tone:** neutral, friendly, professional, casual
     - **Dialect:** standard, regional variations
     - **Genre:** educational, business, entertainment, documentary
     - **Formality:** formal, informal, conversational

5. **Configure Voice:**
   - **Voice Selection:** Choose from available TTS voices
   - **Voice Preview:** Test voice with sample text
   - **Voice Settings:** Adjust speed, pitch, volume if available

6. **Run Pipeline:**
   - Click "🚀 Run Pipeline"
   - Monitor progress through multiple stages:
     - ASR Processing (if needed)
     - Translation
     - TTS Generation
     - Audio Stitching
     - Video Synchronization

7. **Download Result:**
   - Download the final dubbed video
   - Review quality and timing
   - Re-run with different settings if needed

### Automatic Mode Tips

**For Best Results:**
- Use clear, well-recorded audio
- Avoid background music during speech
- Keep segments under 30 seconds for better translation
- Use multiple API keys to avoid quota limits

**Common Settings by Content Type:**

**Educational Content:**
```
Tone: friendly
Dialect: standard
Genre: educational
Formality: conversational
```

**Business Presentations:**
```
Tone: professional
Dialect: standard
Genre: business
Formality: formal
```

**Entertainment/YouTube:**
```
Tone: casual
Dialect: regional
Genre: entertainment
Formality: informal
```

## Manual Mode

Manual mode gives you complete control over translations, perfect for precise content or when automatic translation needs refinement.

### When to Use Manual Mode

- **Precise Control:** When exact wording matters
- **Technical Content:** Specialized terminology or jargon
- **Creative Content:** Maintaining style and voice
- **Quality Assurance:** When automatic translation needs improvement
- **Multiple Languages:** Creating versions in languages not supported by automatic mode

### Step-by-Step Process

#### Step 1: Prepare Translation

1. **Complete Transcription First:**
   - Use the Transcription tab to get ASR results
   - Review and note any transcription errors

2. **Generate Template:**
   - In Dubbing Pipeline tab, select "Manual" mode
   - Click "Generate Template from ASR"
   - This creates a JSON template with original text and timing

3. **Edit Translation:**
   - Copy the generated template
   - Replace `"text_translated"` fields with your translations
   - Maintain the JSON structure exactly
   - Keep timing information unchanged

#### Step 2: Translation Format

**Required JSON Structure:**
```json
[
  {
    "start": 0.0,
    "end": 3.2,
    "text_translated": "Your translated text here"
  },
  {
    "start": 3.2,
    "end": 6.8,
    "text_translated": "Next translated segment"
  }
]
```

**Important Rules:**
- Each segment must have `start`, `end`, and `text_translated`
- Times must be in seconds (decimal allowed)
- Segments should not overlap
- Text should be natural and speakable

#### Step 3: Input Translation

1. **Paste Your Translation:**
   - Copy your completed JSON translation
   - Paste into the "Manual Translation Input" text area

2. **Validate Format:**
   - Click "Validate Translation"
   - Fix any format errors reported
   - Ensure all required fields are present

3. **Alternative Input Formats:**
   - **SRT Format:** Standard subtitle format
   - **CSV Format:** Spreadsheet-compatible format
   - **Direct JSON:** Copy-paste JSON directly

#### Step 4: Run Manual Pipeline

1. **Configure Voice Settings:**
   - Select appropriate TTS voice for target language
   - Test voice with sample text if available

2. **Run Pipeline:**
   - Click "🚀 Run Pipeline"
   - Monitor progress through TTS and video sync stages
   - Manual mode skips automatic translation

3. **Review and Download:**
   - Check timing and audio quality
   - Download final dubbed video
   - Make adjustments if needed

### Manual Mode Tools

#### Template Generator

**From ASR Results:**
```python
# Generates template with original text and timing
{
  "start": 0.0,
  "end": 2.5,
  "original_text": "Hello, welcome to our video",
  "text_translated": "[TRANSLATE: Hello, welcome to our video]"
}
```

**From Timing Only:**
```python
# Creates empty template with specified timing
{
  "start": 0.0,
  "end": 3.0,
  "text_translated": "[Your translation here]"
}
```

#### Format Converter

**SRT to JSON:**
```srt
1
00:00:00,000 --> 00:00:03,200
Your translated text here

2
00:00:03,200 --> 00:00:06,800
Next translated segment
```

**CSV to JSON:**
```csv
start_time,end_time,translated_text
0.0,3.2,"Your translated text here"
3.2,6.8,"Next translated segment"
```

### Manual Mode Best Practices

1. **Translation Quality:**
   - Keep translations natural and conversational
   - Match the original tone and style
   - Consider cultural context and idioms
   - Avoid overly literal translations

2. **Timing Considerations:**
   - Ensure translations fit within time segments
   - Longer translations may sound rushed
   - Shorter translations may have awkward pauses
   - Adjust segment boundaries if needed

3. **Technical Terms:**
   - Maintain consistency in technical vocabulary
   - Use standard translations for common terms
   - Consider your target audience's expertise level

4. **Quality Control:**
   - Review translations before processing
   - Test with a short segment first
   - Listen to TTS output for pronunciation issues
   - Iterate and refine as needed

## Configuration Options

### Translation Style Configuration

**Tone Options:**
- `neutral`: Balanced, professional tone
- `friendly`: Warm, approachable tone
- `professional`: Formal, business-appropriate
- `casual`: Relaxed, conversational tone
- `enthusiastic`: Energetic, excited tone

**Dialect Options:**
- `standard`: Standard/neutral dialect
- `american`: American English variants
- `british`: British English variants
- `australian`: Australian English variants
- `regional`: Local/regional variations

**Genre Options:**
- `educational`: Learning and instructional content
- `business`: Corporate and professional content
- `entertainment`: Movies, shows, casual content
- `documentary`: Factual, informative content
- `marketing`: Promotional and advertising content
- `technical`: Specialized technical content

**Formality Levels:**
- `formal`: Official, ceremonial language
- `informal`: Relaxed, everyday language
- `conversational`: Natural dialogue style

### Voice Configuration

**Voice Selection Criteria:**
- **Language Match:** Choose voices that match your target language
- **Gender Preference:** Male/female voice options
- **Age Appropriateness:** Younger/older sounding voices
- **Accent/Dialect:** Regional accent preferences
- **Quality Level:** Standard vs. premium voice models

**Popular Voice Recommendations:**

**English:**
- `en-US-Journey-D`: High-quality, natural American English
- `en-US-Studio-M`: Professional male voice
- `en-GB-Standard-A`: British English female
- `en-AU-Standard-B`: Australian English male

**Spanish:**
- `es-ES-Standard-A`: European Spanish female
- `es-US-Standard-A`: Latin American Spanish female
- `es-MX-Standard-A`: Mexican Spanish female

**French:**
- `fr-FR-Standard-A`: European French female
- `fr-CA-Standard-A`: Canadian French female

**German:**
- `de-DE-Standard-A`: German female
- `de-DE-Standard-B`: German male

### Audio Processing Settings

**Sample Rate:** 24000 Hz (default, good quality)
**Channels:** 1 (mono, sufficient for speech)
**Format:** WAV (uncompressed, best quality)
**Normalization:** -16 LUFS (broadcast standard)

**Advanced Settings:**
```python
AUDIO_SETTINGS = {
    "sample_rate": 24000,
    "channels": 1,
    "bit_depth": 16,
    "normalization_target": -16.0,
    "fade_in_duration": 0.1,
    "fade_out_duration": 0.1
}
```

### Pipeline Settings

**Chunk Duration:** 30 seconds (default)
- Shorter chunks: Better for complex content, slower processing
- Longer chunks: Faster processing, may have quality issues

**Retry Settings:**
- Max attempts: 3
- Retry delay: 5 seconds
- Exponential backoff: Enabled

**Memory Management:**
- Auto cleanup: Enabled
- Temp file retention: 24 hours
- Cache size limit: 5GB

## File Management

### Input File Requirements

**Supported Video Formats:**
- MP4 (recommended)
- AVI
- MOV
- MKV
- WebM

**Supported Audio Formats:**
- WAV
- MP3
- M4A
- FLAC

**File Size Limits:**
- Maximum file size: 2GB
- Recommended: Under 500MB for best performance
- For larger files: Use video compression or split into segments

**Quality Recommendations:**
- Video resolution: 720p or higher
- Audio bitrate: 128kbps or higher
- Audio sample rate: 44.1kHz or 48kHz
- Clear speech with minimal background noise

### Output Files

**Generated Files:**
- `original_asr.json`: ASR transcription results
- `translated.json`: Translation results
- `tts_chunks/`: Individual TTS audio files
- `stitched_audio.wav`: Combined audio track
- `output_dubbed.mp4`: Final dubbed video
- `pipeline_state.json`: Processing state
- `pipeline.log`: Processing log

**File Organization:**
```
project_folder/
├── input_video.mp4          # Your original video
├── original_asr.json        # ASR results
├── translated.json          # Translation results
├── tts_chunks/              # TTS audio chunks
│   ├── chunk_001.wav
│   ├── chunk_002.wav
│   └── ...
├── stitched_audio.wav       # Combined audio
├── output_dubbed.mp4        # Final result
├── pipeline_state.json      # Processing state
└── pipeline.log             # Processing log
```

### File Cleanup

**Automatic Cleanup:**
- Temporary files are cleaned up after successful completion
- Failed processing files are retained for debugging
- Cache files are cleaned after 24 hours

**Manual Cleanup:**
```python
# Clean all temporary files
from pipeline_controller import PipelineController
controller = PipelineController()
controller.cleanup_temp_files()
```

**Selective Cleanup:**
- Keep ASR results for reuse with different translations
- Keep translation results for voice changes
- Remove TTS chunks after successful video creation

## Quality Control

### Transcription Quality

**Review Checklist:**
- [ ] All speech segments captured
- [ ] Timing accuracy (±0.5 seconds)
- [ ] Proper punctuation and capitalization
- [ ] Technical terms spelled correctly
- [ ] No missing words or phrases

**Common Issues:**
- **Background Music:** May interfere with speech recognition
- **Multiple Speakers:** May merge different speakers
- **Accents:** May misinterpret non-standard pronunciation
- **Technical Terms:** May not recognize specialized vocabulary

**Improvement Tips:**
- Use music mode for content with background music
- Pre-process audio to reduce background noise
- Manually correct transcription before translation
- Use shorter segments for complex audio

### Translation Quality

**Automatic Translation Review:**
- [ ] Meaning preserved from original
- [ ] Natural flow in target language
- [ ] Cultural appropriateness
- [ ] Technical accuracy
- [ ] Consistent terminology

**Manual Translation Guidelines:**
- Maintain original tone and style
- Adapt cultural references appropriately
- Keep translations within timing constraints
- Use natural, speakable language
- Avoid overly literal translations

### Audio Quality

**TTS Output Review:**
- [ ] Clear pronunciation
- [ ] Natural rhythm and pacing
- [ ] Appropriate emotional tone
- [ ] Consistent volume levels
- [ ] No robotic artifacts

**Sync Quality:**
- [ ] Audio matches video timing
- [ ] No gaps or overlaps
- [ ] Smooth transitions between segments
- [ ] Consistent audio levels
- [ ] No audio artifacts

### Final Video Quality

**Technical Checks:**
- [ ] Video plays without errors
- [ ] Audio and video are synchronized
- [ ] No visual artifacts
- [ ] Appropriate file size
- [ ] Compatible with target platforms

**Content Checks:**
- [ ] Translation accuracy maintained
- [ ] Appropriate voice and tone
- [ ] Cultural sensitivity
- [ ] Professional presentation
- [ ] Meets project requirements

## Advanced Features

### Batch Processing

Process multiple videos with different configurations:

```python
# Example batch configuration
batch_configs = [
    {
        "name": "video1_spanish",
        "video_path": "video1.mp4",
        "target_language": "Spanish",
        "voice_name": "es-ES-Standard-A"
    },
    {
        "name": "video1_french", 
        "video_path": "video1.mp4",
        "target_language": "French",
        "voice_name": "fr-FR-Standard-A"
    }
]
```

### API Integration

Use the pipeline programmatically:

```python
from pipeline_controller import PipelineController, PipelineConfig

# Configure pipeline
config = PipelineConfig(
    video_path="input.mp4",
    api_keys=["your_api_key"],
    voice_name="es-ES-Standard-A",
    style_config={"tone": "professional"},
    mode="automatic"
)

# Run pipeline
controller = PipelineController()
result = controller.run_automatic_pipeline(config)
print(f"Dubbed video: {result}")
```

### Custom Workflows

Create specialized workflows for specific use cases:

```python
# Educational content workflow
def educational_workflow(video_path, target_language):
    config = PipelineConfig(
        video_path=video_path,
        api_keys=api_keys,
        voice_name=get_educational_voice(target_language),
        style_config={
            "tone": "friendly",
            "genre": "educational",
            "formality": "conversational"
        },
        mode="automatic"
    )
    return controller.run_automatic_pipeline(config)
```

### Performance Optimization

**For Large Files:**
- Process in smaller segments
- Use multiple API keys
- Enable GPU acceleration
- Increase system memory

**For High Volume:**
- Use batch processing
- Implement queue management
- Monitor system resources
- Use dedicated hardware

## Best Practices

### Content Preparation

1. **Audio Quality:**
   - Record in quiet environment
   - Use good quality microphone
   - Minimize background noise
   - Maintain consistent volume

2. **Video Quality:**
   - Use standard formats (MP4 recommended)
   - Maintain reasonable file sizes
   - Ensure good compression balance
   - Test with short clips first

3. **Content Structure:**
   - Keep segments reasonably short
   - Pause between major topics
   - Speak clearly and at moderate pace
   - Avoid overlapping speech

### Translation Strategy

1. **Automatic Mode:**
   - Use for general content
   - Review and refine results
   - Test with short segments first
   - Use multiple API keys for reliability

2. **Manual Mode:**
   - Use for precise control
   - Maintain consistent terminology
   - Consider cultural context
   - Test pronunciation with TTS

3. **Hybrid Approach:**
   - Start with automatic translation
   - Manually refine critical sections
   - Use templates for consistency
   - Iterate and improve

### Quality Assurance

1. **Testing Process:**
   - Test with short clips first
   - Review each stage output
   - Check timing and synchronization
   - Validate on target devices

2. **Review Checklist:**
   - Technical quality (audio/video)
   - Translation accuracy
   - Cultural appropriateness
   - Professional presentation

3. **Iteration Strategy:**
   - Make incremental improvements
   - Document successful configurations
   - Learn from failed attempts
   - Build reusable templates

### Production Workflow

1. **Development Phase:**
   - Test with sample content
   - Establish quality standards
   - Create configuration templates
   - Train team members

2. **Production Phase:**
   - Use proven configurations
   - Implement quality checks
   - Monitor processing status
   - Maintain backup procedures

3. **Delivery Phase:**
   - Validate final outputs
   - Test on target platforms
   - Gather feedback
   - Document lessons learned

## FAQ

### General Questions

**Q: What video formats are supported?**
A: MP4, AVI, MOV, MKV, and WebM. MP4 is recommended for best compatibility.

**Q: How long does processing take?**
A: Typically 2-5x the video duration. A 10-minute video usually takes 20-50 minutes to process completely.

**Q: Can I process multiple videos simultaneously?**
A: Yes, using batch processing features or running multiple instances with different configurations.

**Q: Is there a file size limit?**
A: Recommended maximum is 2GB. Larger files should be split into segments or compressed.

### Technical Questions

**Q: Why is my GPU not being used?**
A: Ensure CUDA is installed and PyTorch can detect your GPU. Check with `torch.cuda.is_available()`.

**Q: How can I improve processing speed?**
A: Use GPU acceleration, multiple API keys, shorter segments, and ensure adequate system memory.

**Q: What if I run out of API quota?**
A: Use multiple API keys, monitor usage, or upgrade your API plan. The system will rotate keys automatically.

**Q: Can I pause and resume processing?**
A: Yes, the system saves state automatically. You can resume from the last completed stage.

### Quality Questions

**Q: How can I improve translation quality?**
A: Use manual mode for critical content, provide context in style configuration, and review automatic translations.

**Q: Why does the TTS sound robotic?**
A: Try different voices, adjust speaking rate, or use premium voice models. Some languages have better TTS quality than others.

**Q: How do I fix audio sync issues?**
A: Ensure accurate timing in transcription, validate segment boundaries, and check for processing errors.

**Q: Can I use my own voice model?**
A: Currently, the system uses Google Cloud TTS voices. Custom voice models are not supported in this version.

### Troubleshooting Questions

**Q: What if processing fails?**
A: Check logs for error messages, verify API keys, ensure sufficient disk space, and try with a shorter video first.

**Q: How do I reset the pipeline?**
A: Delete `pipeline_state.json` and temporary files, or use the reset function in the pipeline controller.

**Q: Why am I getting API errors?**
A: Verify API keys are valid, check quota limits, ensure internet connectivity, and try with backup keys.

**Q: What if the output video is corrupted?**
A: Check input video quality, ensure sufficient disk space, verify FFmpeg installation, and review processing logs.

### Advanced Questions

**Q: Can I customize the translation prompts?**
A: Yes, modify the style configuration or edit the translation service code for custom prompts.

**Q: How do I integrate this with other systems?**
A: Use the API interface or import the pipeline controller into your Python applications.

**Q: Can I add support for new languages?**
A: Yes, if Google Cloud TTS supports the language. Add voice configurations and test thoroughly.

**Q: How do I optimize for my specific use case?**
A: Create custom configuration templates, adjust processing parameters, and implement specialized workflows.

---

This user manual provides comprehensive guidance for using the Dubbing Pipeline system effectively. For additional support, consult the troubleshooting guide, API documentation, and example implementations.