# Technology Stack

## Core Technologies
- **Python 3.8+**: Primary language with CUDA GPU support
- **Gradio**: Web interface framework for ML applications
- **PyTorch**: Deep learning framework with CUDA acceleration
- **NVIDIA NeMo**: ASR toolkit for Parakeet-TDT model
- **FFmpeg**: Audio/video processing and format conversion

## Key Dependencies
- `nemo-toolkit[asr]>=1.20.0`: ASR model framework
- `gradio>=3.50.0`: Web UI components
- `pandas>=2.0.0`: Data processing and CSV export
- `soundfile>=0.12.0`: Audio file I/O
- `scipy>=1.10.0`: Signal processing for audio preprocessing
- `google-generativeai`: Gemini API integration (planned)
- `tiktoken`: Token counting for API limits (planned)

## Build System
**Pinokio Platform**: Automated deployment with JavaScript-based scripts
- `install.js`: Dependency installation with PyTorch CUDA setup
- `start.js`: Application launcher with daemon mode
- `torch.js`: Platform-specific PyTorch installation (CUDA/ROCm/CPU)
- `pinokio.js`: UI menu configuration and state management

## Package Management
- **UV**: Fast Python package installer (`uv pip install`)
- **Virtual Environment**: Isolated in `env/` directory
- **CUDA Support**: Automatic GPU detection and appropriate PyTorch variant

## Common Commands

### Installation
```bash
# Install dependencies (handled by install.js)
uv pip install -r requirements.txt

# Manual PyTorch installation
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Development
```bash
# Start application
python app.py

# Run with specific port
python app.py --port 7860
```

### Audio Processing
```bash
# Extract audio from video
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav

# Split long audio files
ffmpeg -i input.wav -ss 0 -t 600 chunk_001.wav
```

## Architecture Patterns
- **Modular Design**: Separate services for ASR, translation, TTS
- **State Persistence**: JSON-based intermediate file storage
- **Error Recovery**: Automatic fallback and retry mechanisms
- **Progress Tracking**: Real-time UI updates via Gradio Progress
- **Resource Management**: Automatic cleanup of temporary files

## GPU Requirements
- **NVIDIA GPU**: Required for optimal ASR performance
- **CUDA 12.4+**: For PyTorch acceleration
- **VRAM**: Minimum 4GB for Parakeet-TDT model
- **Fallback**: CPU mode available but significantly slower