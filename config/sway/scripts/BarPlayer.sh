#!/usr/bin/env bash
# What is playing, for the bar (at most 40 characters); nothing when nothing plays (the item hides).
s=$(playerctl status 2>/dev/null) || exit 0
[ "$s" = Stopped ] && exit 0
icon="󰐊"; [ "$s" = Playing ] && icon="󰏤"
t="$(playerctl metadata artist 2>/dev/null) - $(playerctl metadata title 2>/dev/null)"
[ "${#t}" -gt 38 ] && t="${t:0:37}…"
printf '%s %s\n' "$icon" "$t"
