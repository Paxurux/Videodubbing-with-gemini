# Implementation Plan

- [x] 1. Set up core infrastructure and dependencies



  - Update requirements.txt with Gemini API client, tiktoken tokenizer, and additional audio processing libraries
  - Create directory structure for new modules (translation.py, tts.py, pipeline_controller.py, state_manager.py, audio_utils.py)
  - Define base configuration constants for model fallback lists and default settings
  - _Requirements: 4.1, 4.2, 6.1_

- [x] 2. Implement state management system



  - Create StateManager class with methods for saving/loading pipeline state, detecting current stage, and managing persistent JSON files
  - Implement pipeline state detection logic that checks for existing original_asr.json, translated.json, and tts_chunks/ directory
  - Add comprehensive logging system that writes to pipeline.log with request details, model usage, and error tracking
  - Write unit tests for state persistence, recovery scenarios, and logging functionality
  - _Requirements: 3.1, 3.2, 3.3, 6.1, 6.2_

- [x] 3. Create translation service with Gemini API integration



  - Implement TranslationService class with API key rotation and model fallback logic
  - Create translation request formatting that includes style configuration (tone, dialect, genre) and segment arrays
  - Add error handling for quota limits, network errors, and invalid responses with automatic fallback to next model
  - Implement token counting and request batching to stay within API limits
  - Write unit tests for API error handling, fallback logic, and translation request formatting
  - _Requirements: 1.2, 4.1, 4.2, 6.2, 6.3_

- [x] 4. Develop TTS service with chunking capabilities



  - Create TTSService class with token-based chunking algorithm that groups segments into ≤30,000 token chunks
  - Implement TTS generation using Gemini TTS models with consistent voice configuration across chunks
  - Add audio duration validation and time-scaling to ensure generated audio matches expected segment timing
  - Create chunk splitting logic that automatically halves oversized chunks and retries TTS generation
  - Write unit tests for chunking algorithms, audio duration matching, and TTS error recovery
  - _Requirements: 5.1, 5.2, 5.3, 4.3, 6.2_

- [x] 5. Extend audio processing utilities





  - Add audio stitching function that concatenates TTS chunks in timestamp order using FFmpeg
  - Implement video remuxing functionality that syncs generated audio with original video to produce output_dubbed.mp4
  - Create audio-video synchronization validation to ensure perfect A/V sync in final output
  - Add audio normalization and format standardization for consistent output quality
  - Write unit tests for audio stitching, video remuxing, and synchronization validation
  - _Requirements: 1.4, 5.4, 1.1_

- [x] 6. Create pipeline controller orchestration






  - Implement PipelineController class with run_automatic_pipeline and run_manual_pipeline methods
  - Add continue_from_checkpoint functionality that detects current stage and resumes processing
  - Create progress callback system that provides real-time updates to the Gradio interface
  - Implement error recovery logic that handles interruptions and provides clear error messages
  - Write integration tests for complete pipeline workflows and error recovery scenarios
  - _Requirements: 1.1, 2.1, 3.2, 3.4, 6.4_

- [x] 7. Extend Gradio UI for dubbing pipeline



  - Add radio buttons for Automatic vs Manual mode selection to existing interface
  - Create input fields for API keys (up to 5), style configuration JSON textarea, and TTS voice dropdown
  - Add manual mode textarea for user-provided translated JSON input
  - Implement "Run Pipeline" and "Continue from Here" buttons with appropriate state management
  - Add toggle for skipping ASR when original_asr.json exists
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Integrate pipeline with existing ASR workflow



  - Modify existing transcribe_audio and transcribe_video functions to save output in original_asr.json format
  - Update ASR output format to ensure compatibility with translation service input requirements
  - Add pipeline mode detection to existing UI that shows dubbing options when ASR completes
  - Ensure existing ASR functionality remains unchanged while adding new pipeline capabilities
  - Write integration tests to verify ASR-to-translation workflow continuity
  - _Requirements: 1.1, 3.3, 7.5_

- [x] 9. Implement manual mode functionality



  - Create JSON validation for user-provided translated segments with start, end, and text_translated fields
  - Add manual mode workflow that skips ASR and translation steps, proceeding directly to TTS generation
  - Implement error handling for invalid JSON format or missing required fields in manual input
  - Create UI feedback for manual mode validation and processing status
  - Write unit tests for JSON validation and manual mode workflow
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 10. Add comprehensive error handling and recovery





  - Implement API quota exhaustion handling with automatic key rotation and model fallback
  - Create user-friendly error messages for common failure scenarios (invalid keys, network issues, file errors)
  - Add automatic retry logic with exponential backoff for transient failures
  - Implement graceful degradation when all API keys are exhausted or models unavailable
  - Write unit tests for error scenarios and recovery mechanisms
  - _Requirements: 6.2, 6.3, 6.4, 4.4_

- [x] 11. Create final integration and testing



  - Perform end-to-end testing of complete automatic pipeline workflow
  - Test manual mode with various translated JSON inputs and edge cases
  - Validate continue-from-checkpoint functionality across all pipeline stages
  - Test error recovery and fallback mechanisms under various failure conditions
  - Verify audio-video synchronization accuracy in final dubbed output
  - _Requirements: 1.1, 1.4, 2.1, 3.2, 5.4_

- [x] 12. Update documentation and requirements


  - Update requirements.txt with all new dependencies including google-generativeai, tiktoken, and additional FFmpeg bindings
  - Add inline code documentation for all new classes and methods
  - Create usage examples and configuration guides for API keys and style settings
  - Document troubleshooting steps for common error scenarios
  - _Requirements: 4.1, 6.4_