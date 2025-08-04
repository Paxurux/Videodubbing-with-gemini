module.exports = {
  run: [
    // Update dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "echo '🔄 Updating dependencies...'",
          "uv pip install --upgrade pip setuptools wheel",
          "uv pip install -r requirements.txt --upgrade"
        ]
      }
    },
    
    // Verify core components
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python -c \"import torch; print('✅ PyTorch:', torch.__version__)\"",
          "python -c \"import gradio; print('✅ Gradio:', gradio.__version__)\"",
          "python -c \"import nemo; print('✅ NeMo toolkit ready')\"",
          "python -c \"import google.generativeai; print('✅ Gemini API ready')\"",
          "python -c \"import edge_tts; print('✅ Edge TTS ready')\""
        ]
      }
    },
    
    // Update complete
    {
      method: "shell.run",
      params: {
        message: [
          "echo ''",
          "echo '✅ UPDATE COMPLETE!'",
          "echo '🚀 All dependencies updated'",
          "echo '📋 System ready for use'",
          "echo ''"
        ]
      }
    }
  ]
}