module.exports = {
  run: [
    // Clean cache directories
    {
      method: "shell.run",
      params: {
        message: [
          "echo '🧹 Cleaning cache directories...'",
          "rm -rf cache/GRADIO_TEMP_DIR/* 2>/dev/null || rmdir /s /q cache\\GRADIO_TEMP_DIR 2>nul || echo 'Cache cleaned'",
          "rm -rf cache/HF_HOME/* 2>/dev/null || rmdir /s /q cache\\HF_HOME 2>nul || echo 'HF cache cleaned'",
          "rm -rf cache/TORCH_HOME/* 2>/dev/null || rmdir /s /q cache\\TORCH_HOME 2>nul || echo 'Torch cache cleaned'"
        ]
      }
    },
    
    // Clean temporary files
    {
      method: "shell.run",
      params: {
        message: [
          "echo '🗑️ Cleaning temporary files...'",
          "rm -rf temp_audio/* 2>/dev/null || rmdir /s /q temp_audio 2>nul || echo 'Temp audio cleaned'",
          "rm -rf batch_dubbed_videos/* 2>/dev/null || rmdir /s /q batch_dubbed_videos 2>nul || echo 'Batch videos cleaned'",
          "rm -f *.json 2>/dev/null || del *.json 2>nul || echo 'JSON files cleaned'",
          "rm -f *.wav 2>/dev/null || del *.wav 2>nul || echo 'WAV files cleaned'",
          "rm -f *.mp4 2>/dev/null || del *.mp4 2>nul || echo 'MP4 files cleaned'"
        ]
      }
    },
    
    // Recreate necessary directories
    {
      method: "shell.run",
      params: {
        message: [
          "echo '📁 Recreating directories...'",
          "mkdir -p cache/GRADIO_TEMP_DIR cache/HF_HOME cache/TORCH_HOME",
          "mkdir -p batch_dubbed_videos temp_audio"
        ]
      }
    },
    
    // Reset complete
    {
      method: "shell.run",
      params: {
        message: [
          "echo ''",
          "echo '✅ RESET COMPLETE!'",
          "echo '🧹 All temporary files cleaned'",
          "echo '📁 Directories recreated'",
          "echo '🚀 System ready for fresh start'",
          "echo ''"
        ]
      }
    }
  ]
}