#!/usr/bin/env python3
import json, subprocess, os
GLYPH = "\U000f075a"
def run(*a):
    try:
        return subprocess.check_output(list(a), stderr=subprocess.DEVNULL, text=True, timeout=2).strip()
    except Exception:
        return ""
player = run(os.path.expanduser("~/.config/hypr/scripts/mediaplayer.sh"), "current")
meta = ""
if player:
    try:
        out = subprocess.check_output(["playerctl","-p",player,"metadata","--format","{{artist}} - {{title}}"], stderr=subprocess.DEVNULL, text=True, timeout=2).strip()
        meta = out
    except Exception:
        meta = ""
status = run("playerctl","-p",player,"status") if player else ""
text = GLYPH
tooltip = f"{player}\n{meta}\n{status}" if player else "No media player"
print(json.dumps({"text": text, "tooltip": tooltip}))
