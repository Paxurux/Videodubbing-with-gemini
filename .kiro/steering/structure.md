# Project Structure

## Root Directory
```
├── app.py                 # Main Gradio application entry point
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── PINOKIO.MD            # Pinokio platform documentation
├── icon.png              # Application icon
└── ENVIRONMENT           # Environment variables for Pinokio
```

## Pinokio Scripts
```
├── pinokio.js            # UI menu configuration and launcher
├── install.js            # Dependency installation script
├── start.js              # Application startup with daemon mode
├── torch.js              # Platform-specific PyTorch installation
├── update.js             # Update dependencies
├── reset.js              # Reset to clean state
└── link.js               # Deduplicate library files
```

## Configuration Files
```
├── pinokio_meta.json     # Pinokio metadata (posts, links)
└── .kiro/                # Kiro IDE configuration
    ├── steering/         # AI assistant guidance documents
    └── specs/            # Feature specifications
        └── dubbing-pipeline/
            ├── requirements.md
            ├── design.md
            └── tasks.md
```

## Runtime Directories
```
├── env/                  # Python virtual environment
├── cache/                # Model and temporary file cache
│   ├── GRADIO_TEMP_DIR/
│   ├── HF_HOME/         # Hugging Face model cache
│   └── TORCH_HOME/      # PyTorch model cache
└── .git/                # Git repository
```

## Planned Structure (Dubbing Pipeline)
```
├── translation.py        # Gemini API translation service
├── tts.py               # Text-to-speech generation
├── pipeline_controller.py # Main pipeline orchestration
├── state_manager.py     # State persistence and recovery
├── audio_utils.py       # Extended audio processing utilities
├── original_asr.json    # ASR output with timestamps
├── translated.json      # Translated segments
├── tts_chunks/          # Individual TTS audio files
├── pipeline_state.json  # Current processing state
├── pipeline.log         # Comprehensive operation logging
└── output_dubbed.mp4    # Final dubbed video output
```

## Code Organization Patterns

### Main Application (`app.py`)
- **Global Model Loading**: Single model instance to avoid reloading
- **Function Separation**: Distinct functions for audio/video/microphone input
- **Progress Callbacks**: Gradio Progress integration for long operations
- **Temporary File Management**: Automatic cleanup with proper error handling

### Pinokio Integration
- **Script Modularity**: Separate concerns (install, start, torch, etc.)
- **Environment Detection**: Platform and GPU-specific logic
- **State Management**: UI menu reflects current application state
- **Error Handling**: Graceful fallbacks for different hardware configurations

### Future Modular Design
- **Service Layer**: Separate classes for Translation, TTS, State management
- **Controller Pattern**: Pipeline orchestration with clear interfaces
- **Persistence Layer**: JSON-based state storage with validation
- **Utility Functions**: Reusable audio/video processing functions

## File Naming Conventions
- **Python Files**: Snake_case (e.g., `pipeline_controller.py`)
- **JavaScript Files**: Camelcase for functions, lowercase for files
- **JSON Files**: Descriptive names with underscores (e.g., `pipeline_state.json`)
- **Temporary Files**: Prefixed with temp or stored in dedicated directories
- **Log Files**: `.log` extension with descriptive names

## Import Structure
```python
# Standard library imports first
import os
import tempfile
import subprocess

# Third-party imports
import gradio as gr
import torch
import pandas as pd
import nemo.collections.asr as nemo_asr

# Local imports last
from translation import TranslationService
from tts import TTSService
from pipeline_controller import PipelineController
```

## Configuration Management
- **Environment Variables**: Stored in `ENVIRONMENT` file for Pinokio
- **Model Paths**: Cached in `cache/` directories
- **API Keys**: Memory-only storage, never persisted
- **User Settings**: JSON configuration files in project root