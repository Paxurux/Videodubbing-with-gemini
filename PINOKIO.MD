# Video Dubbing Pipeline - Pinokio Installation Guide

## 🎯 Overview
Professional video dubbing solution with automated transcription, translation, and text-to-speech generation. Built on Parakeet-TDT-0.6b-v2 with Google Gemini AI integration.

### Key Features
- **Automated Video Dubbing**: Complete end-to-end dubbing workflow
- **Batch Video Creation**: Process multiple audio files with one video
- **AI Translation**: Google Gemini-powered translation
- **Professional TTS**: High-quality text-to-speech generation
- **Video Synchronization**: Automatic audio-video sync

## 🚀 Quick Start

### 1. Installation
Click the **"Install"** button in Pinokio to automatically:
- Set up Python virtual environment
- Install PyTorch with CUDA support
- Download all required dependencies
- Create necessary project directories
- Verify all components

### 2. Launch
Click **"Start Application"** to launch the Gradio interface.

### 3. Access
The application will open in your browser at `http://localhost:7860`

## 🎬 Features

### Step-by-Step Dubbing
- **Video Upload**: Support for MP4, AVI, MOV, MKV, WebM
- **Automatic Transcription**: Extract and transcribe audio using Parakeet-TDT
- **AI Translation**: Translate to target language using Gemini AI
- **Manual Translation**: Support for custom JSON translations
- **TTS Generation**: High-quality voice synthesis
- **Video Output**: Synchronized dubbed video

### Batch Video Creation
- **Multiple Audio Processing**: Upload one video + multiple audio files
- **Batch Output**: Generate multiple dubbed videos automatically
- **Efficient Workflow**: Process variations quickly
- **Organized Output**: All videos saved in dedicated folder

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **RAM**: 8GB (16GB recommended)
- **Storage**: 10GB free space
- **Internet**: Required for model downloads and API services

### Recommended for Optimal Performance
- **GPU**: NVIDIA GPU with 4GB+ VRAM
- **CUDA**: Version 12.4 or later
- **RAM**: 16GB or more
- **CPU**: Multi-core processor (8+ cores recommended)

### Required External Tools
- **FFmpeg**: Automatically handled by Pinokio installation

## 🔧 Configuration

### API Keys Setup
The application requires Google Gemini API keys:

1. **Get API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Multiple Keys**: Support for multiple keys for higher rate limits
3. **Secure Input**: Keys entered securely in the application (not stored)

### Environment Variables
Automatically configured by Pinokio:
```bash
HF_HOME=./cache/HF_HOME                    # Hugging Face model cache
TORCH_HOME=./cache/TORCH_HOME              # PyTorch model cache
GRADIO_TEMP_DIR=./cache/GRADIO_TEMP_DIR    # Gradio temporary files
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # CUDA memory optimization
```

## 📁 Directory Structure

### Automatically Created Directories
```
├── cache/                     # Model and temporary file cache
│   ├── HF_HOME/              # Hugging Face models
│   ├── TORCH_HOME/           # PyTorch models
│   └── GRADIO_TEMP_DIR/      # Gradio temporary files
├── batch_dubbed_videos/       # Batch processing output
└── temp_audio/               # Temporary audio processing
```

## 🎯 Usage Workflow

### Step-by-Step Dubbing
1. **API Keys**: Enter your Gemini API keys
2. **Upload Video**: Select video file for dubbing
3. **Choose Voice**: Select voice name (Kore, Puck, Zephyr, etc.)
4. **Translation Mode**: 
   - **Automatic**: AI-powered translation
   - **Manual**: Provide custom JSON translation
5. **Run Pipeline**: Click "Run Dubbing Pipeline"
6. **Download**: Get dubbed video and audio files

### Batch Video Creation
1. **API Keys**: Enter your Gemini API keys
2. **Upload Video**: Select base video file
3. **Upload Audio**: Select multiple audio files
4. **Choose Voice**: Select voice configuration
5. **Create Batch**: Click "Create Batch Videos"
6. **Download All**: Get all generated videos from batch folder

## 🔍 Troubleshooting

### Common Issues

#### Installation Problems
- **PyTorch CUDA**: Automatic detection and installation
- **Model Downloads**: Large models download on first use
- **Dependency Conflicts**: Virtual environment isolation prevents conflicts

#### Runtime Issues
- **GPU Memory**: Automatic memory management with fallback to CPU
- **Model Loading**: Models cached after first download
- **API Limits**: Multiple API key support for higher throughput

#### Performance Optimization
- **GPU Acceleration**: Automatic CUDA detection and usage
- **Memory Management**: Efficient model loading and unloading
- **Batch Processing**: Optimized for multiple file processing

### Getting Help
1. **Check Logs**: View terminal output for detailed error messages
2. **Restart Application**: Use Pinokio's restart function
3. **Reinstall**: Use "Reset & Clean" option for fresh installation
4. **Update**: Use "Update Dependencies" for latest versions

## 📊 Performance Metrics

### Processing Speed (Approximate)
- **Transcription**: 2-5x real-time (with GPU)
- **Translation**: 10-20 segments per minute
- **TTS Generation**: 1-3x real-time
- **Video Processing**: 1-2x real-time

### Accuracy Metrics
- **ASR Accuracy**: 95%+ for clear audio
- **Translation Quality**: Professional-grade with Gemini
- **Voice Synthesis**: Natural-sounding output

## 🔄 Updates and Maintenance

### Automatic Updates
- **Dependencies**: Use "Update Dependencies" in Pinokio
- **Models**: Automatic updates when available
- **Application**: Git-based updates

### Manual Maintenance
- **Cache Cleanup**: Use "Reset & Clean" option
- **Model Refresh**: Delete cache directories to re-download
- **Configuration Reset**: Remove configuration files to reset settings

---

## 📞 Support

For technical support and questions:
- Check the troubleshooting section above
- Review application logs in the terminal
- Use Pinokio's built-in diagnostic tools

**Enjoy creating professional dubbed content!** 🎬✨