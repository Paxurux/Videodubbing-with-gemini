# Dubbing Pipeline Examples

This document provides comprehensive examples for using the dubbing pipeline in various scenarios.

## Table of Contents

1. [Basic Usage Examples](#basic-usage-examples)
2. [Advanced Configuration](#advanced-configuration)
3. [Manual Mode Examples](#manual-mode-examples)
4. [Error Handling and Recovery](#error-handling-and-recovery)
5. [Batch Processing](#batch-processing)
6. [Custom Workflows](#custom-workflows)
7. [Integration Examples](#integration-examples)
8. [Performance Optimization](#performance-optimization)

## Basic Usage Examples

### Example 1: Simple Automatic Dubbing

```python
#!/usr/bin/env python3
"""
Simple automatic dubbing example.
Transcribes a video and creates a dubbed version.
"""

from pipeline_controller import PipelineController, PipelineConfig

def simple_dubbing_example():
    # Initialize the pipeline controller
    controller = PipelineController()
    
    # Configure the pipeline
    config = PipelineConfig(
        video_path="my_video.mp4",
        api_keys=["your_gemini_api_key_here"],
        voice_name="en-US-Journey-D",
        style_config={"tone": "neutral"},
        mode="automatic"
    )
    
    # Simple progress callback
    def show_progress(progress, status):
        print(f"Progress: {progress*100:.1f}% - {status}")
    
    try:
        # Run the complete pipeline
        result_video = controller.run_automatic_pipeline(config, show_progress)
        print(f"\n✅ Dubbing completed successfully!")
        print(f"📹 Dubbed video saved as: {result_video}")
        
    except Exception as e:
        print(f"❌ Dubbing failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    simple_dubbing_example()
```

### Example 2: Manual Mode with Custom Translation

```python
#!/usr/bin/env python3
"""
Manual mode dubbing with custom translations.
"""

import json
from pipeline_controller import PipelineController, PipelineConfig

def manual_dubbing_example():
    # Your custom translations
    manual_translations = [
        {
            "start": 0.0,
            "end": 3.2,
            "text_translated": "Bienvenidos a nuestro tutorial de inteligencia artificial"
        },
        {
            "start": 3.2,
            "end": 6.8,
            "text_translated": "Hoy aprenderemos sobre redes neuronales"
        },
        {
            "start": 6.8,
            "end": 10.5,
            "text_translated": "Comenzaremos con los conceptos básicos"
        }
    ]
    
    # Convert to JSON string
    translation_json = json.dumps(manual_translations, indent=2, ensure_ascii=False)
    
    # Configure pipeline for manual mode
    config = PipelineConfig(
        video_path="tutorial_video.mp4",
        api_keys=["your_gemini_api_key"],  # Still needed for TTS
        voice_name="es-ES-Standard-A",     # Spanish voice
        style_config={},
        mode="manual",
        manual_translation=translation_json
    )
    
    controller = PipelineController()
    
    try:
        result = controller.run_manual_pipeline(config)
        print(f"✅ Manual dubbing completed: {result}")
        
    except Exception as e:
        print(f"❌ Manual dubbing failed: {e}")

if __name__ == "__main__":
    manual_dubbing_example()
```

## Advanced Configuration

### Example 3: Multi-Language Dubbing with Style Configuration

```python
#!/usr/bin/env python3
"""
Advanced dubbing with detailed style configuration.
"""

from pipeline_controller import PipelineController, PipelineConfig
import os

def advanced_dubbing_example():
    # Advanced style configuration
    style_configs = {
        "spanish": {
            "tone": "friendly",
            "dialect": "latin_american",
            "genre": "educational",
            "formality": "casual",
            "target_audience": "young_adults"
        },
        "french": {
            "tone": "professional",
            "dialect": "european",
            "genre": "business",
            "formality": "formal",
            "target_audience": "professionals"
        }
    }
    
    # Voice configurations
    voice_configs = {
        "spanish": "es-ES-Standard-A",
        "french": "fr-FR-Standard-A"
    }
    
    # Multiple API keys for better reliability
    api_keys = [
        "gemini_key_1",
        "gemini_key_2",
        "gemini_key_3"
    ]
    
    input_video = "corporate_presentation.mp4"
    
    # Process each language
    for language, style_config in style_configs.items():
        print(f"\n🌍 Processing {language.title()} dubbing...")
        
        config = PipelineConfig(
            video_path=input_video,
            api_keys=api_keys,
            voice_name=voice_configs[language],
            style_config=style_config,
            mode="automatic"
        )
        
        controller = PipelineController()
        
        def language_progress(progress, status):
            print(f"[{language.upper()}] {progress*100:.1f}% - {status}")
        
        try:
            result = controller.run_automatic_pipeline(config, language_progress)
            
            # Rename output for clarity
            output_name = f"corporate_presentation_{language}.mp4"
            os.rename(result, output_name)
            
            print(f"✅ {language.title()} dubbing completed: {output_name}")
            
        except Exception as e:
            print(f"❌ {language.title()} dubbing failed: {e}")
            continue

if __name__ == "__main__":
    advanced_dubbing_example()
```

## Manual Mode Examples

### Example 4: Template-Based Manual Translation

```python
#!/usr/bin/env python3
"""
Manual mode using template generation from ASR results.
"""

from manual_mode_utils import ManualModeWorkflow
from pipeline_controller import PipelineController, PipelineConfig
import json

def template_based_translation_example():
    # Initialize manual mode workflow
    workflow = ManualModeWorkflow()
    
    # Check if we can generate a template
    status = workflow.get_manual_mode_status()
    
    if not status['asr_available']:
        print("❌ No ASR results found. Please run transcription first.")
        return False
    
    print(f"📋 ASR results available: {status['template_segments']} segments")
    
    # Generate template from ASR
    print("🔧 Generating translation template...")
    template_json = workflow.template_generator.generate_template_from_asr()
    template_data = json.loads(template_json)
    
    print(f"Generated template with {len(template_data)} segments:")
    for i, segment in enumerate(template_data[:3]):  # Show first 3
        print(f"  {i+1}. [{segment['start']:.1f}s-{segment['end']:.1f}s] {segment['original_text']}")
    
    # Simulate manual translation process
    print("\n✏️ Applying manual translations...")
    
    # Translation mapping (in real use, this would come from user input)
    translations = {
        "Hello world": "Hola mundo",
        "How are you today?": "¿Cómo estás hoy?",
        "I am doing great": "Estoy muy bien",
        "Let's get started": "Empecemos",
        "Thank you for watching": "Gracias por ver"
    }
    
    # Apply translations to template
    for segment in template_data:
        original_text = segment['original_text']
        # Simple translation lookup (in practice, use proper translation)
        translated = translations.get(original_text, f"[TRANSLATE: {original_text}]")
        segment['text_translated'] = translated
    
    # Convert back to JSON
    final_translation = json.dumps(template_data, indent=2, ensure_ascii=False)
    
    # Validate the translation
    print("🔍 Validating translation...")
    is_valid, message, segments = workflow.validator.validate_translation_json(final_translation)
    
    if not is_valid:
        print(f"❌ Validation failed: {message}")
        return False
    
    print(f"✅ Validation passed: {message}")
    
    # Process the manual translation
    success, process_message, processed_segments = workflow.process_manual_input(
        final_translation, "json"
    )
    
    if not success:
        print(f"❌ Processing failed: {process_message}")
        return False
    
    print(f"✅ Translation processed: {process_message}")
    
    # Now run the manual pipeline
    print("\n🚀 Running manual dubbing pipeline...")
    
    config = PipelineConfig(
        video_path="input_video.mp4",
        api_keys=["your_gemini_api_key"],
        voice_name="es-ES-Standard-A",
        style_config={},
        mode="manual",
        manual_translation=final_translation
    )
    
    controller = PipelineController()
    
    try:
        result = controller.run_manual_pipeline(config)
        print(f"🎉 Template-based dubbing completed: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Manual pipeline failed: {e}")
        return False

if __name__ == "__main__":
    template_based_translation_example()
```

## Error Handling and Recovery

### Example 5: Robust Pipeline with Recovery

```python
#!/usr/bin/env python3
"""
Robust pipeline execution with comprehensive error handling and recovery.
"""

import logging
import time
import os
from pipeline_controller import PipelineController, PipelineConfig
from state_manager import StateManager

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dubbing_pipeline_robust.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def robust_pipeline_example():
    """Robust pipeline with automatic recovery and detailed error handling."""
    
    # Configuration
    config = PipelineConfig(
        video_path="important_video.mp4",
        api_keys=[
            "primary_gemini_key",
            "backup_gemini_key_1",
            "backup_gemini_key_2"
        ],
        voice_name="en-US-Journey-D",
        style_config={"tone": "professional", "genre": "business"},
        mode="automatic"
    )
    
    controller = PipelineController()
    state_manager = StateManager()
    
    # Execution parameters
    max_attempts = 5
    base_delay = 10  # seconds
    
    def detailed_progress(progress, status):
        logger.info(f"Progress: {progress*100:.1f}% - {status}")
        print(f"[{time.strftime('%H:%M:%S')}] {progress*100:6.1f}% - {status}")
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Starting pipeline attempt {attempt + 1}/{max_attempts}")
            
            # Check current pipeline state
            current_state = controller.detect_pipeline_state()
            logger.info(f"Current pipeline state: {current_state}")
            
            if current_state == "complete":
                logger.info("Pipeline already complete!")
                print("✅ Pipeline already complete!")
                return True
            
            # Determine execution strategy
            if current_state in ["translation_needed", "tts_needed", "stitching_needed"]:
                logger.info("Continuing from checkpoint...")
                print("🔄 Continuing from checkpoint...")
                result = controller.continue_from_checkpoint(config, detailed_progress)
            else:
                logger.info("Starting fresh pipeline...")
                print("🚀 Starting fresh pipeline...")
                result = controller.run_automatic_pipeline(config, detailed_progress)
            
            # Success!
            logger.info(f"Pipeline completed successfully: {result}")
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📹 Final video: {result}")
            
            # Validate output
            if os.path.exists(result) and os.path.getsize(result) > 0:
                logger.info("Output validation passed")
                print("✅ Output validation passed")
                return True
            else:
                raise Exception("Output file is missing or empty")
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            
            # Save current state for analysis
            try:
                current_state = state_manager.load_pipeline_state()
                logger.info(f"Current state saved: {current_state}")
            except:
                logger.warning("Could not save current state")
            
            if attempt < max_attempts - 1:
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("All attempts exhausted")
                print("💥 All attempts exhausted. Check logs for details.")
                
                # Final state analysis
                try:
                    final_state = state_manager.load_pipeline_state()
                    logger.error(f"Final pipeline state: {final_state}")
                    print(f"📊 Final pipeline state: {final_state}")
                except:
                    logger.error("Could not load final state")
                
                return False
    
    return False

if __name__ == "__main__":
    success = robust_pipeline_example()
    exit(0 if success else 1)
```

## Batch Processing

### Example 6: Batch Video Processing

```python
#!/usr/bin/env python3
"""
Batch processing multiple videos with different configurations.
"""

import os
import json
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pipeline_controller import PipelineController, PipelineConfig

class BatchProcessor:
    """Handles batch processing of multiple videos."""
    
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.results = []
        self.failed_jobs = []
    
    def process_video_batch(self, batch_configs: List[Dict]) -> Dict:
        """Process a batch of videos with different configurations."""
        
        print(f"🚀 Starting batch processing of {len(batch_configs)} videos...")
        print(f"   Max concurrent jobs: {self.max_workers}")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_config = {
                executor.submit(self._process_single_video, config): config 
                for config in batch_configs
            }
            
            # Process completed jobs
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                
                try:
                    result = future.result()
                    self.results.append({
                        "config": config,
                        "result": result,
                        "status": "success"
                    })
                    print(f"✅ Completed: {config['name']}")
                    
                except Exception as e:
                    self.failed_jobs.append({
                        "config": config,
                        "error": str(e),
                        "status": "failed"
                    })
                    print(f"❌ Failed: {config['name']} - {e}")
        
        # Generate summary
        summary = {
            "total_jobs": len(batch_configs),
            "successful": len(self.results),
            "failed": len(self.failed_jobs),
            "success_rate": len(self.results) / len(batch_configs) * 100,
            "results": self.results,
            "failures": self.failed_jobs
        }
        
        return summary
    
    def _process_single_video(self, config_dict: Dict) -> str:
        """Process a single video configuration."""
        
        # Convert dict to PipelineConfig
        pipeline_config = PipelineConfig(
            video_path=config_dict["video_path"],
            api_keys=config_dict["api_keys"],
            voice_name=config_dict["voice_name"],
            style_config=config_dict.get("style_config", {}),
            mode=config_dict.get("mode", "automatic"),
            manual_translation=config_dict.get("manual_translation")
        )
        
        controller = PipelineController()
        
        def job_progress(progress, status):
            print(f"[{config_dict['name']}] {progress*100:.1f}% - {status}")
        
        if pipeline_config.mode == "automatic":
            result = controller.run_automatic_pipeline(pipeline_config, job_progress)
        else:
            result = controller.run_manual_pipeline(pipeline_config, job_progress)
        
        # Rename output file to include job name
        output_name = f"{config_dict['name']}_dubbed.mp4"
        os.rename(result, output_name)
        
        return output_name

def batch_processing_example():
    """Example of batch processing multiple videos."""
    
    # Define batch configurations
    batch_configs = [
        {
            "name": "corporate_presentation_spanish",
            "video_path": "corporate_presentation.mp4",
            "api_keys": ["gemini_key_1", "gemini_key_2"],
            "voice_name": "es-ES-Standard-A",
            "style_config": {
                "tone": "professional",
                "dialect": "european",
                "genre": "business"
            },
            "mode": "automatic"
        },
        {
            "name": "tutorial_video_french",
            "video_path": "tutorial_video.mp4", 
            "api_keys": ["gemini_key_3", "gemini_key_4"],
            "voice_name": "fr-FR-Standard-A",
            "style_config": {
                "tone": "friendly",
                "dialect": "european",
                "genre": "educational"
            },
            "mode": "automatic"
        }
    ]
    
    # Initialize batch processor
    processor = BatchProcessor(max_workers=2)  # Process 2 videos simultaneously
    
    # Process the batch
    summary = processor.process_video_batch(batch_configs)
    
    # Display results
    print(f"\n📊 Batch Processing Summary:")
    print(f"   Total jobs: {summary['total_jobs']}")
    print(f"   Successful: {summary['successful']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    
    if summary['successful'] > 0:
        print(f"\n✅ Successful outputs:")
        for result in summary['results']:
            print(f"   - {result['result']}")
    
    if summary['failed'] > 0:
        print(f"\n❌ Failed jobs:")
        for failure in summary['failures']:
            print(f"   - {failure['config']['name']}: {failure['error']}")
    
    # Save detailed report
    with open("batch_processing_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Detailed report saved: batch_processing_report.json")
    
    return summary['success_rate'] > 50  # Consider successful if >50% success rate

if __name__ == "__main__":
    success = batch_processing_example()
    exit(0 if success else 1)
```

## Integration Examples

### Example 7: Web API Integration

```python
#!/usr/bin/env python3
"""
Web API integration example using Flask.
"""

from flask import Flask, request, jsonify, send_file
import os
import threading
import uuid
from pipeline_controller import PipelineController, PipelineConfig

app = Flask(__name__)

# Global storage for job status
job_status = {}
job_results = {}

class DubbingAPI:
    """Web API wrapper for dubbing pipeline."""
    
    def __init__(self):
        self.controller = PipelineController()
    
    def start_dubbing_job(self, job_config: dict) -> str:
        """Start a dubbing job asynchronously."""
        
        job_id = str(uuid.uuid4())
        job_status[job_id] = {"status": "starting", "progress": 0.0, "message": "Initializing..."}
        
        # Start job in background thread
        thread = threading.Thread(
            target=self._run_dubbing_job,
            args=(job_id, job_config)
        )
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _run_dubbing_job(self, job_id: str, job_config: dict):
        """Run dubbing job in background."""
        
        try:
            # Create pipeline config
            config = PipelineConfig(
                video_path=job_config["video_path"],
                api_keys=job_config["api_keys"],
                voice_name=job_config["voice_name"],
                style_config=job_config.get("style_config", {}),
                mode=job_config.get("mode", "automatic"),
                manual_translation=job_config.get("manual_translation")
            )
            
            def update_progress(progress, status):
                job_status[job_id] = {
                    "status": "processing",
                    "progress": progress,
                    "message": status
                }
            
            # Run pipeline
            if config.mode == "automatic":
                result = self.controller.run_automatic_pipeline(config, update_progress)
            else:
                result = self.controller.run_manual_pipeline(config, update_progress)
            
            # Job completed successfully
            job_status[job_id] = {
                "status": "completed",
                "progress": 1.0,
                "message": "Dubbing completed successfully"
            }
            job_results[job_id] = result
            
        except Exception as e:
            # Job failed
            job_status[job_id] = {
                "status": "failed",
                "progress": 0.0,
                "message": f"Dubbing failed: {str(e)}"
            }

# Initialize API
dubbing_api = DubbingAPI()

@app.route('/api/dub', methods=['POST'])
def start_dubbing():
    """Start a new dubbing job."""
    
    try:
        job_config = request.json
        
        # Validate required fields
        required_fields = ["video_path", "api_keys", "voice_name"]
        for field in required_fields:
            if field not in job_config:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Start job
        job_id = dubbing_api.start_dubbing_job(job_config)
        
        return jsonify({
            "job_id": job_id,
            "status": "started",
            "message": "Dubbing job started successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a dubbing job."""
    
    if job_id not in job_status:
        return jsonify({"error": "Job not found"}), 404
    
    status = job_status[job_id]
    response = {
        "job_id": job_id,
        "status": status["status"],
        "progress": status["progress"],
        "message": status["message"]
    }
    
    # Add result if completed
    if status["status"] == "completed" and job_id in job_results:
        response["result_file"] = job_results[job_id]
    
    return jsonify(response)

def web_api_example():
    """Example of using the web API."""
    
    print("🌐 Starting Dubbing Pipeline Web API...")
    print("📡 API Endpoints:")
    print("   POST /api/dub - Start dubbing job")
    print("   GET /api/status/<job_id> - Get job status")
    print("\n🚀 Server starting on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    web_api_example()
```

This comprehensive examples document provides practical, real-world usage scenarios for the dubbing pipeline system. Each example is self-contained and demonstrates different aspects of the system, from basic usage to advanced integration techniques.