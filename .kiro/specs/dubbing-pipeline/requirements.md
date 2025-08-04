# Requirements Document

## Introduction

This feature extends the existing Python/Gradio ASR project to include a complete translate-and-dub pipeline. The system will integrate translation and text-to-speech (TTS) capabilities using Gemini models while preserving the existing ASR functionality. The pipeline will support both automatic mode (full ASR → Translation → TTS workflow) and manual mode (user-provided translations → TTS), with robust error handling, model fallbacks, and persistent intermediate results for resumable operations.

## Requirements

### Requirement 1

**User Story:** As a content creator, I want to automatically translate and dub my video content into different languages, so that I can reach international audiences without manual translation work.

#### Acceptance Criteria

1. WHEN a user uploads a video file THEN the system SHALL extract audio, run ASR to produce timestamped segments, translate the full transcript using Gemini models, generate TTS audio chunks, and produce a dubbed video output
2. WHEN the automatic pipeline encounters API errors or quota limits THEN the system SHALL automatically rotate through the predefined fallback list of Gemini models for both translation and TTS
3. WHEN processing completes successfully THEN the system SHALL save `original_asr.json`, `translated.json`, and individual TTS chunks in `tts_chunks/` folder
4. WHEN the final output is generated THEN the system SHALL produce `output_dubbed.mp4` with perfect audio-video synchronization

### Requirement 2

**User Story:** As a user with existing translations, I want to use manual mode to generate dubbed audio from my pre-translated content, so that I can have control over the translation quality while still benefiting from automated TTS generation.

#### Acceptance Criteria

1. WHEN a user selects manual mode and provides a video file with `translated.json` THEN the system SHALL skip ASR and translation steps and proceed directly to TTS chunking and audio generation
2. WHEN manual mode is activated THEN the system SHALL accept user-pasted JSON in the format `[{start, end, text_translated}, ...]`
3. WHEN manual mode processes the translation THEN the system SHALL validate the JSON format and time segments before proceeding to TTS generation
4. WHEN manual mode completes THEN the system SHALL produce the same output format as automatic mode

### Requirement 3

**User Story:** As a user experiencing interruptions during processing, I want to continue from any intermediate stage, so that I don't have to restart the entire pipeline when errors occur or processing is interrupted.

#### Acceptance Criteria

1. WHEN the system encounters an interruption at any stage THEN it SHALL save the current progress to persistent JSON files on disk
2. WHEN a user clicks "Continue from Here" THEN the system SHALL detect existing intermediate files (`original_asr.json`, `translated.json`, `tts_chunks/`) and resume from the appropriate stage
3. WHEN resuming from an intermediate stage THEN the system SHALL skip completed steps and continue with the next required operation
4. WHEN intermediate files are corrupted or missing THEN the system SHALL provide clear error messages indicating which stage needs to be rerun

### Requirement 4

**User Story:** As a user configuring the dubbing system, I want to provide multiple API keys and customize translation style, so that I can ensure reliable service and control the output quality according to my content needs.

#### Acceptance Criteria

1. WHEN a user provides up to 5 Gemini API keys THEN the system SHALL use them in rotation when primary keys hit quota limits or errors
2. WHEN a user specifies style configuration JSON THEN the system SHALL apply tone, dialect, and genre settings to the translation process
3. WHEN a user selects a TTS voice from prebuilt options THEN the system SHALL use that voice consistently across all generated audio segments
4. WHEN API keys are exhausted or all models fail THEN the system SHALL provide clear error messages with suggested next steps

### Requirement 5

**User Story:** As a user processing long-form content, I want the system to handle large files efficiently through chunking, so that I can dub lengthy videos without hitting token limits or memory constraints.

#### Acceptance Criteria

1. WHEN the translated content exceeds 30,000 tokens THEN the system SHALL split segments into chunk-groups that stay within the token limit
2. WHEN creating TTS chunks THEN the system SHALL preserve original start/end timestamps for each segment to maintain synchronization
3. WHEN a TTS chunk fails due to size or duration mismatch THEN the system SHALL automatically split that chunk in half and retry
4. WHEN all chunks are processed THEN the system SHALL concatenate audio files in timestamp order and sync with the original video

### Requirement 6

**User Story:** As a system administrator, I want comprehensive logging and error handling, so that I can troubleshoot issues and monitor API usage effectively.

#### Acceptance Criteria

1. WHEN any API request is made THEN the system SHALL log the request details, model name, API key index, and success/failure status to `pipeline.log`
2. WHEN an error occurs during processing THEN the system SHALL log the error details and attempt automatic recovery using fallback models
3. WHEN quota limits are reached THEN the system SHALL automatically rotate to the next available API key and model combination
4. WHEN all recovery attempts fail THEN the system SHALL provide detailed error information to help users resolve the issue

### Requirement 7

**User Story:** As a user of the Gradio interface, I want intuitive controls for both automatic and manual modes, so that I can easily configure and run the dubbing pipeline according to my needs.

#### Acceptance Criteria

1. WHEN the interface loads THEN it SHALL display radio buttons for Automatic vs Manual mode selection
2. WHEN in automatic mode THEN the interface SHALL show file upload, API key input, style configuration JSON textarea, and voice selection dropdown
3. WHEN in manual mode THEN the interface SHALL additionally show a textarea for pasting translated JSON
4. WHEN processing begins THEN the interface SHALL show "Run Pipeline" and "Continue from Here" buttons with appropriate enabling/disabling based on system state
5. WHEN ASR results exist THEN the interface SHALL provide a toggle to skip ASR and use existing `original_asr.json`