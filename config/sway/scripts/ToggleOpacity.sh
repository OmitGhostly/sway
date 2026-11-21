#!/usr/bin/env bash
# The window you are in: see-through (85 %) or solid. It stays that way until you toggle it back (the window
# transparency from Settings > Appearance leaves it alone - AutoTiling.py sees the mark).
mark="_swaydots_opacity"
if swaymsg -t get_tree 2>/dev/null | jq -e --arg m "$mark" '.. | objects | select(.focused == true) | .marks // [] | index($m)' >/dev/null 2>&1; then
  swaymsg -q "unmark $mark, opacity 1"
  # (back to what Settings > Appearance says for the window you are in)
  pkill -USR1 -f "AutoTiling.py" 2>/dev/null
else
  swaymsg -q "mark --add $mark, opacity 0.85"
fi
