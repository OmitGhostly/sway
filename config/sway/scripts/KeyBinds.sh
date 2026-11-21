#!/usr/bin/env bash
# Searchable cheat sheet built from the sway config: each "## text" line documents the bindsym below it.
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/sway/config"
pkill -x rofi 2>/dev/null
awk '
  /^## /      { d=substr($0,4); next }
  /^bindsym / { k=$2; if ($2 ~ /^--/) k=$3
                gsub(/\$mod/,"SUPER",k); gsub(/\$alt/,"ALT",k); gsub(/\+/," + ",k)
                if (d!="") printf "%-34s %s\n", k, d; d=""; next }
              { d="" }
' "$cfg" | rofi -dmenu -i -p "Keybinds" -config "${XDG_CONFIG_HOME:-$HOME/.config}/sway/rofi/config-keybinds.rasi" >/dev/null
