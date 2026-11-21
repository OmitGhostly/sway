#!/usr/bin/env bash
# Drop-down terminal on sway's scratchpad (the window rules in the sway config float it, size it and hide it there).
# Uses ghostty when installed, otherwise kitty.
if command -v ghostty >/dev/null 2>&1; then
  id="com.swaydots.dropterm"; start=(ghostty --class="$id" --gtk-single-instance=false)
else
  id="kitty-dropterm"; start=(kitty --class "$id")
fi
# (shown or hidden: there already, so just toggle it)
if swaymsg -t get_tree 2>/dev/null | grep -q "\"app_id\": \"$id\""; then
  swaymsg -q "[app_id=\"^$id\$\"] scratchpad show"
else
  setsid "${start[@]}" >/dev/null 2>&1 &
fi
