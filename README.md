# 🎬 Video Dubbing Pipeline

Professional video dubbing solution with automated transcription, translation, and text-to-speech generation using Parakeet-TDT-0.6b-v2, Gemini AI, and Edge TTS.

## ✨ Features

### 🎬 Step-by-Step Dubbing
- **Automatic Transcription**: Extract and transcribe audio from videos using Parakeet-TDT-0.6b-v2
- **AI Translation**: Translate content using Google Gemini AI
- **Manual Translation**: Support for custom translations in JSON format
- **TTS Generation**: High-quality text-to-speech with multiple voice options
- **Video Synchronization**: Automatically sync dubbed audio with original video

### 🎵 Batch Video Creation
- **Multiple Audio Processing**: Upload one video and multiple audio files
- **Batch Output**: Generate multiple dubbed videos automatically
- **Efficient Workflow**: Process multiple variations quickly

## 🚀 Quick Start

### Installation via Pinokio
1. Install through Pinokio platform
2. Click "Install" to set up dependencies
3. Click "Start Application" to launch

### Manual Installation
```bash
# Clone repository
git clone <repository-url>
cd video-dubbing-pipeline

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start application
python app.py
```

## 📋 Requirements

### System Requirements
- **Python 3.8+**
- **FFmpeg** (for video/audio processing)
- **CUDA GPU** (recommended for optimal performance)
- **4GB+ VRAM** (for ASR model)

### API Requirements
- **Google Gemini API Key** (for translation and TTS)
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Multiple keys supported for higher rate limits

## 🎯 Usage

### Step-by-Step Dubbing
1. **Configure API Keys**: Enter your Gemini API keys (one per line)
2. **Upload Video**: Select your video file for dubbing
3. **Choose Voice**: Select voice name (e.g., Kore, Puck, Zephyr)
4. **Select Mode**: 
   - **Automatic**: AI-powered translation
   - **Manual**: Provide custom JSON translation
5. **Run Pipeline**: Click "Run Dubbing Pipeline"
6. **Download Results**: Get dubbed video and audio files

### Batch Video Creation
1. **Configure API Keys**: Enter your Gemini API keys
2. **Upload Video**: Select base video file
3. **Upload Audio Files**: Select multiple audio files
4. **Choose Voice**: Select voice configuration
5. **Create Batch**: Click "Create Batch Videos"
6. **Download All**: Get all generated videos

## 📁 Project Structure

```
├── app.py                     # Main Gradio application
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── PINOKIO.MD               # Pinokio platform documentation
├── install.js               # Pinokio installation script
├── start.js                 # Pinokio startup script
├── pinokio.js              # Pinokio configuration
├── real_gemini_service.py   # Gemini AI translation service
├── final_working_tts.py     # TTS generation service
├── simple_edge_tts.py       # Edge TTS integration
└── batch_dubbed_videos/     # Output directory for batch processing
```

## 🔧 Configuration

### Voice Options
- **Kore**: Balanced, natural voice
- **Puck**: Energetic, youthful voice  
- **Zephyr**: Calm, professional voice
- **Custom**: Specify your own voice name

### Translation Settings
- **Target Language**: Currently optimized for Hindi
- **Tone**: Neutral, professional tone
- **Dialect**: Hindi Devanagari script
- **Genre**: General content adaptation

## 🎵 Supported Formats

### Input Formats
- **Video**: MP4, AVI, MOV, MKV, WebM
- **Audio**: WAV, MP3, FLAC, M4A, OGG

### Output Formats
- **Video**: MP4 (H.264 + AAC)
- **Audio**: WAV (16-bit, 16kHz)

## 🚨 Troubleshooting

### Common Issues
1. **Model Loading Errors**: Ensure sufficient VRAM (4GB+)
2. **FFmpeg Not Found**: Install FFmpeg and add to PATH
3. **API Key Errors**: Verify Gemini API key validity
4. **CUDA Issues**: Install CUDA toolkit for GPU acceleration

### Performance Tips
- Use GPU for faster transcription
- Provide multiple API keys for higher rate limits
- Process shorter videos for faster results
- Ensure stable internet connection for API calls

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the documentation
3. Open an issue on GitHub

---

**Made with ❤️ for content creators and developers**