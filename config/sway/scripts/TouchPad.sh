#!/usr/bin/env bash
# The touchpad on / off (the touchpad key).
icon="${XDG_CONFIG_HOME:-$HOME/.config}/sway/icons/touchpad.png"
state=$(swaymsg -t get_inputs -r 2>/dev/null | jq -r '[.[] | select(.type == "touchpad")][0].libinput.send_events // empty' 2>/dev/null)
[ -z "$state" ] && { notify-send -i "$icon" "Touchpad" "none found"; exit 1; }
if [ "$state" = enabled ]; then swaymsg -q input type:touchpad events disabled; notify-send -u low -i "$icon" "Touchpad" "disabled"
else swaymsg -q input type:touchpad events enabled; notify-send -u low -i "$icon" "Touchpad" "enabled"; fi
