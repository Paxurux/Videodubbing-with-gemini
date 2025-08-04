# Requirements Document

## Introduction

This feature implements a single-request TTS approach that converts JSON subtitle data into a formatted prompt for Gemini TTS, allowing the entire dialogue to be generated in one API call instead of multiple individual requests. This approach should improve timing consistency, reduce API overhead, and potentially resolve rate limiting issues.

## Requirements

### Requirement 1: JSON to Prompt Conversion

**User Story:** As a developer, I want to convert JSON subtitle data into a formatted prompt, so that I can send all dialogue to Gemini TTS in a single request.

#### Acceptance Criteria

1. WHEN the system receives JSON subtitle data THEN it SHALL convert it to a formatted prompt with timing information
2. WHEN formatting the prompt THEN it SHALL include start and end timestamps in [MM:SS - MM:SS] format
3. WHEN formatting the prompt THEN it SHALL include speaker names and dialogue text
4. WHEN formatting the prompt THEN it SHALL add appropriate instructions for voice, pacing, and timing
5. WHEN multiple subtitle segments exist THEN they SHALL be combined into a single cohesive prompt
6. WHEN timestamps have different formats THEN the system SHALL normalize them to consistent format

### Requirement 2: Single-Request TTS Generation

**User Story:** As a user, I want the system to generate all TTS audio in one API call, so that I get consistent timing and reduce API overhead.

#### Acceptance Criteria

1. WHEN the formatted prompt is ready THEN the system SHALL send it to Gemini TTS in a single request
2. WHEN making the TTS request THEN it SHALL use the confirmed working API configuration
3. WHEN the request succeeds THEN it SHALL receive a single audio file containing all dialogue
4. WHEN the audio is received THEN it SHALL be saved as a properly formatted WAV file
5. WHEN the request fails THEN it SHALL provide detailed error information
6. WHEN rate limiting occurs THEN it SHALL implement appropriate retry logic

### Requirement 3: Audio Quality Verification

**User Story:** As a user, I want the generated audio to be verified for quality, so that I know it contains actual speech and not silence.

#### Acceptance Criteria

1. WHEN audio is generated THEN the system SHALL verify it contains actual audio content
2. WHEN verifying audio THEN it SHALL check RMS levels and amplitude
3. WHEN audio appears silent THEN it SHALL provide debugging information
4. WHEN audio is valid THEN it SHALL confirm duration and quality metrics
5. WHEN audio format is incorrect THEN it SHALL attempt format conversion
6. WHEN verification fails THEN it SHALL provide specific failure reasons

### Requirement 4: Prompt Optimization

**User Story:** As a developer, I want to optimize the prompt format, so that Gemini TTS generates the most natural and accurately timed speech.

#### Acceptance Criteria

1. WHEN creating prompts THEN it SHALL include clear timing instructions
2. WHEN dialogue has emotional context THEN it SHALL add appropriate voice direction
3. WHEN speakers change THEN it SHALL provide clear speaker transitions
4. WHEN pauses are needed THEN it SHALL include pause instructions
5. WHEN dialogue is long THEN it SHALL optimize for natural pacing
6. WHEN multiple languages are present THEN it SHALL handle language transitions

### Requirement 5: Fallback and Error Handling

**User Story:** As a user, I want robust error handling, so that the system gracefully handles failures and provides alternatives.

#### Acceptance Criteria

1. WHEN single-request fails THEN it SHALL fall back to individual segment processing
2. WHEN API quota is exceeded THEN it SHALL implement exponential backoff
3. WHEN audio generation fails THEN it SHALL provide detailed error diagnostics
4. WHEN network issues occur THEN it SHALL retry with appropriate delays
5. WHEN voice is unavailable THEN it SHALL try alternative voices
6. WHEN model is unavailable THEN it SHALL try alternative models

### Requirement 6: Integration with Existing Pipeline

**User Story:** As a developer, I want this feature to integrate seamlessly with the existing dubbing pipeline, so that users can choose between single-request and multi-request approaches.

#### Acceptance Criteria

1. WHEN integrating THEN it SHALL maintain compatibility with existing subtitle formats
2. WHEN users select single-request mode THEN it SHALL use the new approach
3. WHEN users prefer individual segments THEN it SHALL use the existing approach
4. WHEN switching between modes THEN it SHALL preserve all functionality
5. WHEN errors occur THEN it SHALL gracefully fall back to the working approach
6. WHEN testing THEN it SHALL provide comparison between both approaches

### Requirement 7: Performance and Optimization

**User Story:** As a user, I want improved performance and reduced API usage, so that the dubbing process is faster and more cost-effective.

#### Acceptance Criteria

1. WHEN using single-request THEN it SHALL reduce total API calls by at least 80%
2. WHEN processing multiple segments THEN it SHALL complete faster than individual requests
3. WHEN rate limiting occurs THEN it SHALL be less frequent due to fewer requests
4. WHEN measuring performance THEN it SHALL track timing and success metrics
5. WHEN comparing approaches THEN it SHALL provide performance statistics
6. WHEN optimizing THEN it SHALL balance speed with audio quality

### Requirement 8: Debug and Monitoring

**User Story:** As a developer, I want comprehensive debugging and monitoring, so that I can troubleshoot issues and optimize performance.

#### Acceptance Criteria

1. WHEN processing requests THEN it SHALL log detailed timing and status information
2. WHEN errors occur THEN it SHALL provide comprehensive error details
3. WHEN audio is generated THEN it SHALL log quality metrics and file information
4. WHEN debugging THEN it SHALL provide audio analysis tools
5. WHEN monitoring THEN it SHALL track success rates and performance metrics
6. WHEN troubleshooting THEN it SHALL provide step-by-step diagnostic information