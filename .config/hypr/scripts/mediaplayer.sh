#!/usr/bin/env bash
STATE="${XDG_CACHE_HOME:-$HOME/.cache}/form-media/current-player"
case "$1" in
  list)
    playerctl -l 2>/dev/null
    ;;
  current)
    if [ -f "$STATE" ]; then
      p=$(cat "$STATE")
      if playerctl -l 2>/dev/null | grep -qx "$p"; then
        echo "$p"; exit 0
      fi
    fi
    playerctl -l 2>/dev/null | head -n1
    ;;
  select)
    echo "$2" > "$STATE"
    ;;
esac
