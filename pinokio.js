module.exports = {
  version: "3.7",
  title: "Video Dubbing Pipeline",
  description: "🎬 Professional Video Dubbing Pipeline with Parakeet-TDT-0.6b-v2, Gemini AI, and Edge TTS. Complete solution for automated video dubbing with step-by-step processing and batch video creation from multiple audio files.",
  icon: "icon.png",
  menu: async (kernel, info) => {
    let installed = info.exists("env")
    let running = {
      install: info.running("install.js"),
      start: info.running("start.js"),
      update: info.running("update.js"),
      reset: info.running("reset.js")
    }
    
    if (running.install) {
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Installing...",
        href: "install.js"
      }]
    } else if (installed) {
      if (running.start) {
        let local = info.local("start.js")
        if (local && local.url) {
          return [{
            default: true,
            icon: "fa-solid fa-external-link-alt",
            text: "Open Interface",
            href: local.url
          }, {
            icon: "fa-solid fa-terminal",
            text: "View Terminal",
            href: "start.js"
          }]
        } else {
          return [{
            default: true,
            icon: "fa-solid fa-terminal",
            text: "Starting...",
            href: "start.js"
          }]
        }
      } else if (running.update) {
        return [{
          default: true,
          icon: "fa-solid fa-sync",
          text: "Updating...",
          href: "update.js"
        }]
      } else if (running.reset) {
        return [{
          default: true,
          icon: "fa-solid fa-broom",
          text: "Resetting...",
          href: "reset.js"
        }]
      } else {
        return [{
          default: true,
          icon: "fa-solid fa-play",
          text: "Start Application",
          href: "start.js"
        }, {
          icon: "fa-solid fa-sync-alt",
          text: "Update Dependencies",
          href: "update.js"
        }, {
          icon: "fa-solid fa-redo",
          text: "Reinstall",
          href: "install.js"
        }, {
          icon: "fa-solid fa-trash-restore",
          text: "Reset & Clean",
          href: "reset.js",
          confirm: "This will clean all temporary files and cache. Continue?"
        }]
      }
    } else {
      return [{
        default: true,
        icon: "fa-solid fa-download",
        text: "Install",
        href: "install.js"
      }]
    }
  }
}
