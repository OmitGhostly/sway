#!/usr/bin/env bash
# Game mode: no gaps, no window effects (SwayFX blur, shadows, rounded corners; transparency), no bar - all the
# screen and all the GPU for the game. Again: everything back as it was.
f="${XDG_CACHE_HOME:-$HOME/.cache}/sway/gamemode"; mkdir -p "$(dirname "$f")"
icon="${XDG_CONFIG_HOME:-$HOME/.config}/sway/icons/gamepad.png"
s="$(dirname "$0")"
if [ -e "$f" ]; then
  rm -f "$f"
  # the reload brings back your gaps, the effects (Effects.sh) and the bar (exec_always)
  swaymsg -q reload
  notify-send -u low -i "$icon" "Game mode" "off"
else
  touch "$f"
  swaymsg -q 'gaps inner all set 0; gaps outer all set 0'
  "$s/Effects.sh" --off
  pkill -USR1 -f "AutoTiling.py" 2>/dev/null           # (it sees game mode: every window solid)
  pkill -x waybar 2>/dev/null
  notify-send -u low -i "$icon" "Game mode" "on"
fi
