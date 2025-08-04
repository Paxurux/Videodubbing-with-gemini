# Complete App.py Analysis and Documentation

## Overview
This is a comprehensive analysis of the Parakeet-TDT ASR application with dubbing pipeline capabilities. The app is built using Gradio and provides transcription, translation, and text-to-speech functionality.

## File Structure Analysis

### 1. IMPORTS AND DEPENDENCIES (Lines 1-60)
```python
# Core libraries
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

# Custom modules for transcript processing
from transcript_chunker import TranscriptChunker, ChunkConfig
from chunked_audio_stitcher import ChunkedAudioStitcher

# Dubbing pipeline components (conditional imports)
try:
    import google.generativeai as genai
    import wave
    import requests
    from api_key_manager import APIKeyManager
    from real_gemini_service import RealGeminiService
    from enhanced_tts_pipeline import EnhancedTTSPipeline
    from fixed_tts_dubbing import FixedTTSDubbing
    from final_working_tts import FinalWorkingTTS
    from single_request_tts import SingleRequestTTS
    from simple_edge_tts import SimpleEdgeTTS, EDGE_TTS_AVAILABLE
    from enhanced_edge_tts_service import EnhancedEdgeTTSService, EdgeTTSConfig
    from edge_tts_voice_parser import EdgeTTSVoiceParser
    from kokoro_tts_service import KokoroTTSService
    from kokoro_voice_parser import KokoroVoiceParser
    DUBBING_AVAILABLE = True
except ImportError as e:
    DUBBING_AVAILABLE = False
```

**Purpose**: Sets up all required dependencies with graceful fallback for optional dubbing features.

### 2. MODEL LOADING AND GLOBAL VARIABLES (Lines 61-75)
```python
def load_model():
    print("Loading ASR model...")
    asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
    print("Model loaded successfully!")
    return asr_model

model = None  # Global model variable to avoid reloading
```

**Purpose**: Lazy loading of the ASR model to avoid memory issues and startup delays.

### 3. AUDIO PROCESSING UTILITIES (Lines 76-200)
- `get_audio_duration()`: Uses ffprobe to get audio file duration
- `extract_audio_from_video()`: Extracts audio from video files using ffmpeg
- `split_audio_file()`: Splits long audio files into manageable chunks

**Purpose**: Core audio processing functions for handling various input formats and long files.

### 4. MAIN TRANSCRIPTION FUNCTIONS (Lines 201-500)
- `transcribe_audio()`: Main audio transcription function
- `transcribe_video()`: Video transcription wrapper
- `process_long_audio()`: Handles files >10 minutes by chunking
- `process_audio_chunk()`: Processes individual audio segments

**Key Features**:
- Automatic stereo-to-mono conversion
- Music mode with vocal enhancement
- Smart chunking for API efficiency
- Timestamp preservation across chunks

### 5. UI AND DISPLAY FUNCTIONS (Lines 501-600)
- `create_transcript_table()`: Creates interactive HTML table for transcripts
- CSV export functionality
- Clickable segments for audio playback

### 6. DUBBING PIPELINE INTEGRATION (Lines 601-900)
- `save_asr_results()`: Saves transcription in dubbing-compatible format
- `load_asr_results()`: Loads existing ASR results
- `run_dubbing_pipeline()`: Main dubbing pipeline orchestrator
- `continue_dubbing_pipeline()`: Resume from checkpoints
- Pipeline state detection and validation

**Purpose**: Bridges ASR output with translation and TTS services.

## GRADIO INTERFACE STRUCTURE

Now I'll continue reading the Gradio interface section to complete the analysis:
### 
7. GRADIO INTERFACE STRUCTURE (Lines 900-2431)

The Gradio interface is organized into several main sections:

#### A. STEP-BY-STEP DUBBING PIPELINE
- **Step 1**: API Keys setup and validation
- **Step 2**: Transcription (upload video, load from main tab, or paste JSON)
- **Step 3**: Translation (automatic with Gemini or manual)
- **Step 4**: TTS Generation with multiple engine support

#### B. TTS ENGINE SUPPORT
- **Gemini TTS**: 8 voice options (Kore, Puck, Zephyr, etc.)
- **Edge TTS**: 302+ neural voices across 21+ languages
- **Kokoro TTS**: Local TTS with 9 language options

#### C. VOICE SELECTION SYSTEM
- Dynamic UI that shows/hides options based on selected engine
- Language-based voice filtering for Edge TTS
- Voice preview functionality

#### D. MAIN TRANSCRIPTION TAB
- Audio/Video/Microphone input support
- Music mode for vocal enhancement
- Smart chunking options
- Long audio processing (>10 minutes)

## IDENTIFIED ISSUES AND FIXES NEEDED

### 1. CRITICAL INDENTATION ERRORS
**Location**: Lines 1495-1520 in `update_edge_voices()` function
**Problem**: Function body not properly indented
**Fix**: All function content needs 4-space indentation

### 2. INCONSISTENT INDENTATION LEVELS
**Location**: Throughout Gradio interface section
**Problem**: Mixed 4-space, 8-space, and tab indentation
**Fix**: Standardize to 4-space indentation

### 3. FUNCTION PLACEMENT ISSUES
**Location**: Functions defined inside `with` blocks
**Problem**: Functions should be defined at module level
**Fix**: Move function definitions outside interface creation

### 4. MISSING CLOSING BLOCKS
**Location**: Various `with gr.Group():` and `with gr.Row():` blocks
**Problem**: Some blocks may not be properly closed
**Fix**: Ensure all `with` blocks have proper indentation structure

## CORRECTED STRUCTURE PLAN

1. **Move all function definitions** to module level (before interface creation)
2. **Standardize indentation** to 4 spaces throughout
3. **Fix nested `with` block structure**
4. **Ensure proper closing** of all Gradio components
5. **Maintain functionality** while fixing structure

## FUNCTIONS THAT NEED TO BE MOVED
- `toggle_tts_engine()`
- `update_edge_voices()`
- `update_kokoro_voices()`
- `preview_voice()`
- Various event handlers and callbacks

Now I'll create the corrected version...