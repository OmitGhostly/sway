#!/usr/bin/env bash
#  KoolDots (2026)
# Airplane Mode: all Wi-Fi off, or back on (rfkill, through Platform.sh).

notif="${XDG_CONFIG_HOME:-$HOME/.config}/sway/icons/airplane.png"
P="${XDG_CONFIG_HOME:-$HOME/.config}/sway/scripts/Platform.sh"

if state=$("$P" airplane toggle); then
    if [ "$state" = on ]; then
        notify-send -u low -i "$notif" " Airplane" " mode: ON"
    else
        notify-send -u low -i "$notif" " Airplane" " mode: OFF"
    fi
else
    notify-send -u low -i "$notif" " Airplane" " could not switch Wi-Fi (no Wi-Fi, or no permission)"
fi
