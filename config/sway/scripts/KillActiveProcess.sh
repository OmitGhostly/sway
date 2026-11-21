#!/usr/bin/env bash
# Kill the program of the window you are in (it does not get to ask "save changes?").
pid=$(swaymsg -t get_tree 2>/dev/null | jq -r '.. | objects | select(.focused == true) | .pid // empty' 2>/dev/null | head -n1)
case "$pid" in ''|*[!0-9]*|0|1) exit 1 ;; esac
name=$(ps -p "$pid" -o comm= 2>/dev/null)
kill -9 "$pid" && notify-send -u low "Terminated" "$name ($pid)"
