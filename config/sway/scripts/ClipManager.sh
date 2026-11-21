#!/usr/bin/env bash
# Clipboard history (SUPER+ALT+V): pick something you copied earlier and it is on the clipboard again.
# cliphist in rofi (Alt+Delete forgets an entry), else CopyQ's own window.
pkill -x rofi 2>/dev/null
theme="${XDG_CONFIG_HOME:-$HOME/.config}/sway/rofi/config-clipboard.rasi"
if command -v cliphist >/dev/null 2>&1; then
  while :; do
    pick=$(cliphist list | rofi -dmenu -i -p "Clipboard" -config "$theme" -display-columns 2 \
           -kb-custom-1 "Alt+Delete" -mesg "Enter: copy   Alt+Delete: forget it")
    rc=$?
    [ -n "$pick" ] || exit 0
    case $rc in
      0) printf '%s' "$pick" | cliphist decode | wl-copy; exit 0 ;;
      10) printf '%s' "$pick" | cliphist delete ;;          # (and show the list again)
      *) exit 0 ;;
    esac
  done
elif command -v copyq >/dev/null 2>&1; then
  copyq toggle
else
  notify-send "Clipboard" "install cliphist (or copyq)"
fi
