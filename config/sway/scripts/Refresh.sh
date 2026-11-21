#!/usr/bin/env bash
# Reload sway, the bar, notifications, terminal colours and the window effects. --colors: the same (kept for the
# settings window, which calls it after a colour change).
pkill -x rofi 2>/dev/null
pkill -USR1 -x kitty 2>/dev/null
pkill -USR2 -x ghostty 2>/dev/null
command -v dunstctl >/dev/null && dunstctl reload 2>/dev/null
# (the reload starts the bar again - exec_always - and puts back the effects)
swaymsg -q reload
