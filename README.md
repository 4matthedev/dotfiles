# Dotfiles

Personal configuration files for my Arch Linux + Hyprland setup.

## Contents

- `.bashrc` / `.bash_profile` — shell config
- `.config/hypr` — Hyprland config (lua + conf), scripts, gaps, animations
- `.config/waybar` — Waybar config & Nord-themed CSS
- `.config/opencode` — OpenCode config (local llama.cpp provider)
- `.config/form` — accent color
- `.config/systemd/user` — user services (llama-server, mediapanel)
- `.local/bin` — helper scripts (media panel, llama waybar, gguf info, etc.)

## Notes

- Local AI models live in `~/models` and are served by the Prism ML llama.cpp fork via `llama-server` (systemd user service).
- Waybar's media hover panel (`mediapanel.py`) requires `python-atspi` and `gtk-layer-shell`.
- Secrets and large model files are excluded via `.gitignore`.
