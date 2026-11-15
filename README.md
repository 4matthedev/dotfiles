# Dotfiles

Personal configuration for an **Arch Linux** desktop running **Hyprland** (Wayland) on an **NVIDIA RTX 3060**, themed with the **Nord** color palette.

## Hardware / Environment

- **OS:** Arch Linux (rolling)
- **WM:** Hyprland 0.57.2
- **GPU:** NVIDIA GeForce RTX 3060 (12 GB VRAM)
- **Monitor:** HDMI-A-1 @ 1920x1080 180 Hz
- **Terminal:** kitty
- **Shell:** bash
- **Font:** JetBrainsMono Nerd Font

## Repository Layout

```
.
├── .bashrc / .bash_profile
├── .config/
│   ├── hypr/            # Hyprland config (Lua) + autostart scripts
│   ├── waybar/          # Waybar config + Nord CSS
│   ├── opencode/        # OpenCode config (local llama.cpp provider)
│   ├── form/            # accent color
│   └── systemd/user/    # user services
├── .local/bin/          # helper scripts
└── .gitignore
```

## Hyprland (`~/.config/hypr`)

- **Config format:** Lua (`hyprland.lua`), Hyprland 0.57.2.
- **Theme:** Nord — active border gradient `#88c0d0` → `#8fbcbc`, inactive `#4c566a`.
- **Gaps:** `gaps_in = 2`, `gaps_out = 6`. Rounding 8px, blur + shadows enabled.
- **Layout:** dwindle, preserve split, smart resizing.
- **Input:** German keyboard layout (`de`), tap-to-click touchpad, 3-finger workspace swipe.
- **Animations:** custom bezier/spring curves; pop-in windows, fade layers, workspace fade.

### Keybindings (Super = main modifier)

| Keys | Action |
| --- | --- |
| `Super + Return` | Open terminal (kitty) |
| `Super + D` | App launcher (wofi) |
| `Super + E` | File manager (thunar) |
| `Super + B` | Browser (Zen) |
| `Super + Q` | Close window |
| `Super + Shift + Q` | Exit Hyprland |
| `Super + F` | Fullscreen toggle |
| `Super + Shift + F` | Maximized |
| `Super + Space` | Toggle float |
| `Super + P` | Pseudo-tile |
| `Super + Shift + P` | Pin window |
| `Super + J` | Toggle split |
| `Super + G` | Toggle window group |
| `Super + Arrows` | Focus movement |
| `Super + Shift + Arrows` | Move window |
| `Super + Ctrl + Arrows` | Resize window (repeating) |
| `Super + 1..0` | Switch workspace |
| `Super + Shift + 1..0` | Move window to workspace |
| `Super + Tab` | Next workspace |
| `Super + Shift + Tab` | Previous workspace |
| `Super + U` | Scratchpad (magic workspace) |
| `Super + Shift + S` | Area screenshot → clipboard + file |
| `Print` | Full screenshot → clipboard + file |
| `Super + Shift + R` | Reload Hyprland config |
| `XF86Audio*` | Volume / mute / media keys |

### Autostart

- Waybar (with `GTK_MODULES=gail:atk-bridge` for AT-SPI)
- mako (notifications)
- hyprpaper (wallpaper)
- polkit-kde agent

## Waybar (`~/.config/waybar`)

Nord-themed bar, 30px height, top position.

**Modules:** workspaces (with taskbar icons) · clock · pulseaudio · network · cpu · memory · custom/media · custom/ai · tray

- **custom/media** — music-note glyph; hover opens a layer-shell media panel.
- **custom/ai** — llama.cpp status pill (model count / loaded model); hover shows VRAM, RAM, quant, context window; click opens a rofi menu.

## Local AI (`~/models` + llama.cpp)

Runs the **Prism ML fork** of llama.cpp (build `prism-b12128`) as a systemd user service on `127.0.0.1:8080` in router mode.

- Models directory: `~/models`
- Models:
  - `Gemma-4-26B` (Q4_K_M, 15.78 GB, 262k ctx)
  - `Qwen3.8-27B` (PTQ1_0, 5.54 GB, 164k ctx, KV cache q4_0)
- Per-model presets in `~/models/models.ini` (ctx-size, cache-type-k/v, n-gpu-layers).
- CUDA + Vulkan backends both available (RTX 3060).

### OpenCode integration

`~/.config/opencode/opencode.jsonc` registers a custom `localai` provider pointing at the llama.cpp server, exposing both models as `localai/Gemma-4-26B` and `localai/Qwen3.8-27B` (default: Qwen).

## Media Hover Panel (`mediapanel.py`)

A GTK layer-shell panel that appears when hovering the Waybar media pill:

- Cover art, track, artist, album, progress bar, time.
- Transport buttons: prev, play/pause, next, repeat.
- Repeat cycles None → Track → Playlist (via D-Bus `LoopStatus`), with matching icons.
- Player strip when multiple MPRIS players are running.
- Nord-themed, rounded corners, accent `#88c0d0`.

Requires `python-atspi`, `gtk-layer-shell`, `playerctl`. Runs as a systemd user service.

## Systemd User Services

- `llama-server.service` — starts llama.cpp router on login.
- `mediapanel.service` — starts the media hover panel on graphical session.

## Scripts (`~/.local/bin` / `~/.config/hypr/scripts`)

- `mediaplayer.sh` / `mediacontrol.sh` — MPRIS player selection & transport.
- `media-waybar.py` — Waybar media module (glyph + tooltip).
- `llama-waybar.py` — Waybar AI module (status, VRAM, RAM, quant, ctx).
- `llama-menu.sh` — rofi menu for the AI pill (details, web UI, restart/stop).
- `gguf-info.py` / `llama-details.sh` — full GGUF metadata dump.
- `llama-details.sh` — opens a terminal with complete model metadata.

## Installation

1. Install dependencies: `hyprland`, `waybar`, `kitty`, `wofi`, `thunar`, `mako`, `hyprpaper`, `playerctl`, `python-atspi`, `gtk-layer-shell`, `rofi`, `alacritty`, `grim`, `slurp`, `wl-copy`, `nvidia-utils`.
2. Install the Prism ML llama.cpp fork (prebuilt) to `~/.local/share/prism-llama/...` and symlink binaries into `~/.local/bin`.
3. Place models in `~/models` and create `~/models/models.ini`.
4. Copy dotfiles into place (or symlink).
5. Enable services: `systemctl --user enable --now llama-server.service mediapanel.service`.
6. Log into Hyprland.
