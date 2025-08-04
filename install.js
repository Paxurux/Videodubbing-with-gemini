module.exports = {
  run: [
    // Install PyTorch with CUDA support
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env"
        }
      }
    },
    
    // Install core dependencies from requirements.txt
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "uv pip install --upgrade pip setuptools wheel",
          "uv pip install -r requirements.txt"
        ]
      }
    },
    
    // Create necessary directories
    {
      method: "shell.run",
      params: {
        message: [
          "mkdir -p cache",
          "mkdir -p cache/GRADIO_TEMP_DIR", 
          "mkdir -p cache/HF_HOME",
          "mkdir -p cache/TORCH_HOME",
          "mkdir -p batch_dubbed_videos",
          "mkdir -p temp_audio"
        ]
      }
    },
    
    // Verify core installations
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python -c \"import gradio; print('✅ Gradio:', gradio.__version__)\"",
          "python -c \"import torch; print('✅ PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available())\"",
          "python -c \"import nemo; print('✅ NeMo toolkit installed')\"",
          "python -c \"import google.generativeai; print('✅ Google Generative AI installed')\"",
          "python -c \"import edge_tts; print('✅ Edge TTS installed')\"",
          "python -c \"import soundfile; print('✅ Audio processing ready')\""
        ]
      }
    },
    
    // Verify project modules
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python -c \"from real_gemini_service import RealGeminiService; print('✅ Gemini service ready')\"",
          "python -c \"from final_working_tts import FinalWorkingTTS; print('✅ TTS service ready')\"",
          "python -c \"from simple_edge_tts import SimpleEdgeTTS; print('✅ Edge TTS ready')\""
        ]
      }
    },
    
    // Run installation validation
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "python validate_installation.py"
      }
    },
    
    // Final installation summary
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "echo ''",
          "echo '🎯 INSTALLATION COMPLETE!'",
          "echo '=================================='",
          "echo '✅ All dependencies installed'",
          "echo '✅ Project directories created'", 
          "echo '✅ Core modules verified'",
          "echo ''",
          "echo '🚀 Features Ready:'",
          "echo '  • Video Dubbing Pipeline'",
          "echo '  • Batch Video Creation'",
          "echo '  • Multi-language Translation'",
          "echo '  • TTS Generation'",
          "echo '  • Audio/Video Processing'",
          "echo ''",
          "echo '📝 Notes:'",
          "echo '  • Models download automatically when first used'",
          "echo '  • FFmpeg required for video processing'",
          "echo '  • GPU recommended for best performance'",
          "echo '  • Provide your own Gemini API keys'",
          "echo ''",
          "echo '🎬 Ready to start!'",
          "echo '=================================='",
          "echo ''"
        ]
      }
    }
  ]
}
