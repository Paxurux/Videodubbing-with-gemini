# Product Overview

## Core Product
Audio and video transcription application with automatic speech recognition (ASR) using NVIDIA's Parakeet-TDT-0.6b model. The application provides timestamped transcription with interactive playback capabilities through a Gradio web interface.

## Key Features
- **ASR Processing**: Word-level timestamps with 600M parameter model
- **Multi-Input Support**: Audio files, video files, and microphone recording
- **Interactive Transcripts**: Clickable segments for audio playback
- **Export Capabilities**: CSV download with timestamps
- **Long Audio Handling**: Automatic chunking for files >10 minutes
- **Music Mode**: Specialized processing for songs and vocal content

## Current Development
The project is actively expanding to include a complete **translate-and-dub pipeline** using Google's Gemini models. This will add:
- Automatic translation of transcribed content
- Text-to-speech (TTS) generation with voice consistency
- Video dubbing with audio-video synchronization
- Manual mode for user-provided translations
- Resumable pipeline with state persistence

## Target Users
- Content creators needing multilingual dubbing
- Transcription service providers
- Media professionals working with audio/video content
- Researchers requiring accurate speech-to-text with timestamps

## Deployment
Designed for deployment via Pinokio platform with one-click installation and GPU acceleration support.