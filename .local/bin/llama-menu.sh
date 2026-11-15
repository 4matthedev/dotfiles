#!/usr/bin/env bash
JSON=$(python3 /home/turker/.local/bin/llama-waybar.py)
TEXT=$(echo "$JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)["tooltip"])')
CHOICE=$(printf 'Show details\nOpen web UI\nRestart server\nStop server\n' | rofi -dmenu -p "llama.cpp")
case "$CHOICE" in
  "Show details") alacritty -e bash -c "/home/turker/.local/bin/llama-details.sh" ;;
  "Open web UI") xdg-open http://127.0.0.1:8080 ;;
  "Restart server") systemctl --user restart llama-server.service ;;
  "Stop server") systemctl --user stop llama-server.service ;;
esac
