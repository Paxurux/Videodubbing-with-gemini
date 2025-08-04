module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        env: {
          // Cache directories for models and temporary files
          "HF_HOME": "./cache/HF_HOME",
          "TORCH_HOME": "./cache/TORCH_HOME", 
          "GRADIO_TEMP_DIR": "./cache/GRADIO_TEMP_DIR",
          
          // Performance optimizations
          "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:512",
          
          // Reduce startup noise
          "PYTHONWARNINGS": "ignore::UserWarning",
          "TF_CPP_MIN_LOG_LEVEL": "2",
          "PYTHONUNBUFFERED": "1"
        },
        message: [
          "echo '🚀 Starting Video Dubbing Pipeline...'",
          "python app.py"
        ],
        on: [{
          "event": "/http:\\/\\/[0-9.:]+/",
          "done": true
        }]
      }
    },
    
    {
      method: "local.set",
      params: {
        url: "{{input.event[0]}}"
      }
    },
    
    {
      method: "notify",
      params: {
        html: "🎉 Video Dubbing Pipeline is ready! Click to open.",
        href: "{{local.url}}",
        target: "_blank"
      }
    }
  ]
}

