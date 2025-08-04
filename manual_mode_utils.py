"""
Utilities for manual mode functionality in the dubbing pipeline.
Provides JSON validation, template generation, and format conversion tools.
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

class ManualModeValidator:
    """Validator for manual translation JSON format."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_translation_json(self, translation_text: str) -> Tuple[bool, str, List[Dict]]:
        """
        Validate manual translation JSON format.
        
        Args:
            translation_text: JSON string containing translation data
            
        Returns:
            Tuple of (is_valid, error_message, parsed_data)
        """
        if not translation_text or not translation_text.strip():
            return False, "Translation cannot be empty", []
            
        try:
            # Parse JSON
            data = json.loads(translation_text.strip())
            
            # Validate it's a list
            if not isinstance(data, list):
                return False, "Translation must be a JSON array of segments", []
                
            if len(data) == 0:
                return False, "Translation array cannot be empty", []
            
            # Validate each segment
            for i, segment in enumerate(data):
                is_valid, error_msg = self._validate_segment(segment, i + 1)
                if not is_valid:
                    return False, error_msg, []
            
            # Additional validations
            validation_warnings = self._check_segment_consistency(data)
            
            return True, f"Valid translation with {len(data)} segments" + (f". Warnings: {'; '.join(validation_warnings)}" if validation_warnings else ""), data
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}", []
        except Exception as e:
            return False, f"Validation error: {str(e)}", []
    
    def _validate_segment(self, segment: Dict, segment_num: int) -> Tuple[bool, str]:
        """Validate a single segment."""
        if not isinstance(segment, dict):
            return False, f"Segment {segment_num} must be a JSON object"
        
        # Check required fields
        required_fields = ["start", "end", "text_translated"]
        for field in required_fields:
            if field not in segment:
                return False, f"Segment {segment_num} missing required field: {field}"
        
        # Validate field types and values
        try:
            start_time = float(segment["start"])
            end_time = float(segment["end"])
        except (ValueError, TypeError):
            return False, f"Segment {segment_num} has invalid start/end times (must be numbers)"
        
        if start_time < 0:
            return False, f"Segment {segment_num} has negative start time"
            
        if end_time <= start_time:
            return False, f"Segment {segment_num} has invalid timing: end time must be greater than start time"
        
        if not isinstance(segment["text_translated"], str) or not segment["text_translated"].strip():
            return False, f"Segment {segment_num} has empty or invalid translated text"
            
        # Check for reasonable duration (not too short or too long)
        duration = end_time - start_time
        if duration < 0.2:  # Minimum 0.2 seconds
            return False, f"Segment {segment_num} duration too short ({duration:.2f}s)"
        if duration > 300:  # 5 minutes
            return False, f"Segment {segment_num} duration too long ({duration:.2f}s)"
            
        return True, ""
    
    def _check_segment_consistency(self, segments: List[Dict]) -> List[str]:
        """Check for consistency issues across segments."""
        warnings = []
        
        # Check for overlapping segments
        sorted_segments = sorted(segments, key=lambda x: x["start"])
        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i]["end"]
            next_start = sorted_segments[i + 1]["start"]
            if current_end > next_start:
                warnings.append(f"Overlapping segments detected: segment ending at {current_end:.2f}s overlaps with segment starting at {next_start:.2f}s")
        
        # Check for large gaps
        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i]["end"]
            next_start = sorted_segments[i + 1]["start"]
            gap = next_start - current_end
            if gap > 5.0:  # 5 second gap
                warnings.append(f"Large gap detected: {gap:.2f}s gap between segments")
        
        # Check for very short or very long segments
        for i, segment in enumerate(segments):
            duration = segment["end"] - segment["start"]
            if duration < 0.5:
                warnings.append(f"Very short segment {i+1}: {duration:.2f}s")
            elif duration > 30:
                warnings.append(f"Very long segment {i+1}: {duration:.2f}s")
        
        return warnings

class ManualModeTemplateGenerator:
    """Generator for manual translation templates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_template_from_asr(self, asr_file_path: str = "original_asr.json") -> str:
        """
        Generate a manual translation template from existing ASR results.
        
        Args:
            asr_file_path: Path to ASR results file
            
        Returns:
            JSON template string for manual translation
        """
        try:
            if not os.path.exists(asr_file_path):
                return self._generate_empty_template()
            
            with open(asr_file_path, "r", encoding="utf-8") as f:
                asr_data = json.load(f)
            
            # Handle both old and new ASR format
            if isinstance(asr_data, list):
                segments = asr_data
            elif isinstance(asr_data, dict) and "segments" in asr_data:
                segments = asr_data["segments"]
            else:
                return self._generate_empty_template()
            
            # Generate template
            template_segments = []
            for segment in segments:
                template_segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text_translated": f"[TRANSLATE: {segment['text']}]",
                    "original_text": segment["text"]  # For reference
                })
            
            return json.dumps(template_segments, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error generating template from ASR: {str(e)}")
            return self._generate_empty_template()
    
    def _generate_empty_template(self) -> str:
        """Generate an empty template with example format."""
        template = [
            {
                "start": 0.0,
                "end": 2.5,
                "text_translated": "Your translated text here",
                "original_text": "(Original text for reference)"
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text_translated": "Another translated segment",
                "original_text": "(Original text for reference)"
            }
        ]
        
        return json.dumps(template, indent=2, ensure_ascii=False)
    
    def generate_template_with_timing(self, total_duration: float, segment_length: float = 3.0) -> str:
        """
        Generate a template with evenly spaced timing.
        
        Args:
            total_duration: Total duration in seconds
            segment_length: Average segment length in seconds
            
        Returns:
            JSON template string
        """
        template_segments = []
        current_time = 0.0
        segment_num = 1
        
        while current_time < total_duration:
            end_time = min(current_time + segment_length, total_duration)
            
            template_segments.append({
                "start": round(current_time, 2),
                "end": round(end_time, 2),
                "text_translated": f"Translated text for segment {segment_num}",
                "original_text": f"(Original text for segment {segment_num})"
            })
            
            current_time = end_time
            segment_num += 1
        
        return json.dumps(template_segments, indent=2, ensure_ascii=False)

class ManualModeConverter:
    """Converter for different manual translation formats."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_srt_to_json(self, srt_content: str) -> str:
        """
        Convert SRT subtitle format to manual translation JSON.
        
        Args:
            srt_content: SRT format content
            
        Returns:
            JSON format string
        """
        try:
            segments = []
            srt_blocks = srt_content.strip().split('\n\n')
            
            for block in srt_blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                # Parse timing line (format: 00:00:00,000 --> 00:00:02,500)
                timing_line = lines[1]
                if '-->' not in timing_line:
                    continue
                
                start_str, end_str = timing_line.split(' --> ')
                start_time = self._parse_srt_time(start_str.strip())
                end_time = self._parse_srt_time(end_str.strip())
                
                # Get text (may span multiple lines)
                text = ' '.join(lines[2:]).strip()
                
                if start_time is not None and end_time is not None and text:
                    segments.append({
                        "start": start_time,
                        "end": end_time,
                        "text_translated": text
                    })
            
            return json.dumps(segments, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error converting SRT to JSON: {str(e)}")
            raise ValueError(f"Failed to convert SRT format: {str(e)}")
    
    def _parse_srt_time(self, time_str: str) -> Optional[float]:
        """Parse SRT time format to seconds."""
        try:
            # Format: 00:00:02,500
            time_part, ms_part = time_str.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
            
        except Exception:
            return None
    
    def convert_csv_to_json(self, csv_content: str) -> str:
        """
        Convert CSV format to manual translation JSON.
        Expected CSV format: start,end,text_translated
        
        Args:
            csv_content: CSV format content
            
        Returns:
            JSON format string
        """
        try:
            import csv
            import io
            
            segments = []
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row in csv_reader:
                # Handle different possible column names
                start_key = next((k for k in row.keys() if 'start' in k.lower()), None)
                end_key = next((k for k in row.keys() if 'end' in k.lower()), None)
                text_key = next((k for k in row.keys() if 'text' in k.lower() or 'translation' in k.lower()), None)
                
                if not all([start_key, end_key, text_key]):
                    raise ValueError("CSV must contain columns for start time, end time, and translated text")
                
                try:
                    start_time = float(row[start_key])
                    end_time = float(row[end_key])
                    text = row[text_key].strip()
                    
                    if text:
                        segments.append({
                            "start": start_time,
                            "end": end_time,
                            "text_translated": text
                        })
                        
                except (ValueError, TypeError):
                    continue  # Skip invalid rows
            
            return json.dumps(segments, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error converting CSV to JSON: {str(e)}")
            raise ValueError(f"Failed to convert CSV format: {str(e)}")

class ManualModeWorkflow:
    """Complete workflow manager for manual mode operations."""
    
    def __init__(self):
        self.validator = ManualModeValidator()
        self.template_generator = ManualModeTemplateGenerator()
        self.converter = ManualModeConverter()
        self.logger = logging.getLogger(__name__)
    
    def process_manual_input(self, input_text: str, input_format: str = "json") -> Tuple[bool, str, List[Dict]]:
        """
        Process manual input in various formats.
        
        Args:
            input_text: Input text in specified format
            input_format: Format type ("json", "srt", "csv")
            
        Returns:
            Tuple of (success, message, segments_data)
        """
        try:
            # Convert to JSON if needed
            if input_format.lower() == "srt":
                json_text = self.converter.convert_srt_to_json(input_text)
            elif input_format.lower() == "csv":
                json_text = self.converter.convert_csv_to_json(input_text)
            else:
                json_text = input_text
            
            # Validate JSON
            is_valid, message, segments = self.validator.validate_translation_json(json_text)
            
            if is_valid:
                # Save to translated.json
                self._save_translation_results(segments)
                return True, message, segments
            else:
                return False, message, []
                
        except Exception as e:
            error_msg = f"Error processing manual input: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, []
    
    def _save_translation_results(self, segments: List[Dict]):
        """Save translation results to file."""
        # Add metadata
        translation_data = {
            "metadata": {
                "mode": "manual",
                "total_segments": len(segments),
                "total_duration": max(seg["end"] for seg in segments) if segments else 0,
                "created_at": datetime.now().isoformat(),
                "format_version": "1.0"
            },
            "segments": segments
        }
        
        with open("translated.json", "w", encoding="utf-8") as f:
            json.dump(translation_data, f, indent=2, ensure_ascii=False)
    
    def get_manual_mode_status(self) -> Dict:
        """Get current manual mode status."""
        status = {
            "asr_available": os.path.exists("original_asr.json"),
            "translation_exists": os.path.exists("translated.json"),
            "can_generate_template": False,
            "template_segments": 0
        }
        
        if status["asr_available"]:
            try:
                with open("original_asr.json", "r", encoding="utf-8") as f:
                    asr_data = json.load(f)
                
                if isinstance(asr_data, list):
                    status["template_segments"] = len(asr_data)
                elif isinstance(asr_data, dict) and "segments" in asr_data:
                    status["template_segments"] = len(asr_data["segments"])
                
                status["can_generate_template"] = status["template_segments"] > 0
                
            except Exception:
                pass
        
        return status
    
    def generate_help_text(self) -> str:
        """Generate help text for manual mode."""
        return """
# Manual Mode Help

## JSON Format
Provide translations in JSON array format:
```json
[
  {
    "start": 0.0,
    "end": 2.5,
    "text_translated": "Your translated text here"
  },
  {
    "start": 2.5,
    "end": 5.0,
    "text_translated": "Another translated segment"
  }
]
```

## Required Fields
- `start`: Start time in seconds (number)
- `end`: End time in seconds (number)  
- `text_translated`: Translated text (string)

## Optional Fields
- `original_text`: Original text for reference

## Tips
- Ensure segments don't overlap significantly
- Keep segment durations reasonable (0.5s - 30s)
- Use precise timing for better synchronization
- Test with a few segments first

## Supported Import Formats
- **JSON**: Direct paste or upload
- **SRT**: Subtitle file format
- **CSV**: Spreadsheet format with start,end,text columns
"""