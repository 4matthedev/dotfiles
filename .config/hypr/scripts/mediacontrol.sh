#!/usr/bin/env bash
PLAYER="$(~/.config/hypr/scripts/mediaplayer.sh current)"
action="$1"
case "$action" in
  prev)   playerctl -p "$PLAYER" previous ;;
  play)   playerctl -p "$PLAYER" play-pause ;;
  next)   playerctl -p "$PLAYER" next ;;
  stop)   playerctl -p "$PLAYER" stop ;;
  repeat)
    bus="org.mpris.MediaPlayer2.${PLAYER%%.*}"
    # map player name to dbus service (spotify -> org.mpris.MediaPlayer2.spotify)
    svc="org.mpris.MediaPlayer2.$PLAYER"
    # PLAYER may be "spotify" or "firefox.instance_..." ; use the base name
    base="${PLAYER%%.*}"
    svc="org.mpris.MediaPlayer2.$base"
    cur=$(dbus-send --print-reply --dest="$svc" /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:LoopStatus 2>/dev/null | awk -F'"' '/string/ {print $2}')
    case "$cur" in
      None) next="Track" ;;
      Track) next="Playlist" ;;
      Playlist) next="None" ;;
      *) next="Track" ;;
    esac
    dbus-send --print-reply --dest="$svc" /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Set string:org.mpris.MediaPlayer2.Player string:LoopStatus "variant:string:$next" >/dev/null 2>&1
    ;;
esac
