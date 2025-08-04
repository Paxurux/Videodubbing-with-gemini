"""
Configuration constants for the dubbing pipeline.
Defines model fallback lists, default settings, and voice options.
"""

# Translation model fallback priority list
TRANSLATION_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro", 
    "gemini-2.5-pro-preview-06-05",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-pro-preview-03-25",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-pro",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-1.5-pro-002",
    "gemini-1.5-pro-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-001"
]

# TTS model fallback priority list
TTS_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts"
]

# Available TTS voice options with descriptions
TTS_VOICES = {
    "Zephyr": "Bright",
    "Puck": "Upbeat", 
    "Charon": "Informative",
    "Kore": "Firm",
    "Fenrir": "Excitable",
    "Leda": "Youthful",
    "Orus": "Firm",
    "Aoede": "Breezy",
    "Callirrhoe": "Easy-going",
    "Autonoe": "Bright",
    "Enceladus": "Breathy",
    "Iapetus": "Clear",
    "Umbriel": "Easy-going",
    "Algieba": "Smooth",
    "Despina": "Smooth",
    "Erinome": "Clear",
    "Algenib": "Gravelly",
    "Rasalgethi": "Informative",
    "Laomedeia": "Upbeat",
    "Achernar": "Soft",
    "Alnilam": "Firm",
    "Schedar": "Even",
    "Gacrux": "Mature",
    "Pulcherrima": "Forward",
    "Achird": "Friendly",
    "Zubenelgenubi": "Casual",
    "Vindemiatrix": "Gentle",
    "Sadachbia": "Lively",
    "Sadaltager": "Knowledgeable",
    "Sulafat": "Warm"
}

# Default style configuration
DEFAULT_STYLE_CONFIG = {
    "tone": "neutral",
    "dialect": "standard", 
    "genre": "general"
}

# Pipeline configuration defaults
PIPELINE_DEFAULTS = {
    "max_tokens_per_chunk": 30000,
    "max_retry_attempts": 3,
    "audio_sample_rate": 24000,
    "audio_channels": 1,
    "audio_format": "wav",
    "video_codec": "copy",
    "audio_codec": "aac"
}

# File paths and directories
FILE_PATHS = {
    "original_asr": "original_asr.json",
    "translated": "translated.json", 
    "pipeline_state": "pipeline_state.json",
    "pipeline_log": "pipeline.log",
    "tts_chunks_dir": "tts_chunks",
    "output_video": "output_dubbed.mp4",
    "stitched_audio": "stitched_audio.wav"
}

# Supported languages for translation
SUPPORTED_LANGUAGES = [
    "Arabic (Egyptian)", "German (Germany)", "English (US)", "Spanish (US)",
    "French (France)", "Hindi (India)", "Indonesian (Indonesia)", "Italian (Italy)",
    "Japanese (Japan)", "Korean (Korea)", "Portuguese (Brazil)", "Russian (Russia)",
    "Dutch (Netherlands)", "Polish (Poland)", "Thai (Thailand)", "Turkish (Turkey)",
    "Vietnamese (Vietnam)", "Romanian (Romania)", "Ukrainian (Ukraine)", 
    "Bengali (Bangladesh)", "English (India)", "Marathi (India)", "Tamil (India)",
    "Telugu (India)"
]

# Error messages
ERROR_MESSAGES = {
    "no_api_keys": "No API keys provided. Please add at least one Gemini API key.",
    "invalid_json": "Invalid JSON format in manual translation. Please check your input.",
    "missing_asr": "ASR results not found. Please run transcription first.",
    "all_models_failed": "All translation models and API keys have been exhausted.",
    "tts_generation_failed": "TTS generation failed for all available models.",
    "video_sync_failed": "Failed to sync audio with video. Check video file format.",
    "file_not_found": "Required file not found. Pipeline may need to be restarted."
}

# Progress stage descriptions
PROGRESS_STAGES = {
    "asr_needed": "ASR transcription required",
    "translation_needed": "Translation in progress", 
    "tts_needed": "TTS generation in progress",
    "stitching_needed": "Audio stitching and video sync",
    "complete": "Pipeline completed successfully",
    "error": "Pipeline encountered an error"
}