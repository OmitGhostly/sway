#!/usr/bin/env bash
# Night light: a warmer screen (gammastep, replaces hyprsunset). Usage: toggle | init | status | apply
# It shares the screens' colour ramp with the software brightness of screens without a backlight (Brightness.sh),
# so the two are always applied together: "apply" sets both from what is saved (Brightness.sh calls it).
# On Wayland the colour ramp lasts only as long as the program that set it, so gammastep keeps running while
# either is in use (and is stopped when neither is).
state="${XDG_CACHE_HOME:-$HOME/.cache}/sway/nightlight"; mkdir -p "$(dirname "$state")"
bright="${XDG_STATE_HOME:-$HOME/.local/state}/sway-dots/brightness"
temp="${NIGHT_TEMP:-4000}"

stop_gammastep() {
  pkill -u "$UID" -x gammastep 2>/dev/null || return 0
  for _ in 1 2 3 4 5 6 7 8 9 10; do pgrep -u "$UID" -x gammastep >/dev/null || return 0; sleep 0.1; done
  pkill -KILL -u "$UID" -x gammastep 2>/dev/null
}

apply() {
  local t=6500 b f
  [ "$(cat "$state" 2>/dev/null)" = on ] && t="$temp"
  b="$(cat "$bright" 2>/dev/null)"
  case "$b" in ''|*[!0-9]*) b=100 ;; esac
  [ "$b" -lt 5 ] && b=5
  [ "$b" -gt 100 ] && b=100
  f="$(awk -v b="$b" 'BEGIN { printf "%.2f", b / 100 }')"
  stop_gammastep
  [ "$t" = 6500 ] && [ "$b" -eq 100 ] && return 0          # (neither in use: the normal picture)
  command -v gammastep >/dev/null 2>&1 || return 1
  setsid gammastep -m wayland -P -O "$t" -b "$f:$f" >/dev/null 2>&1 </dev/null &
}

case "$1" in
  toggle) icon="${XDG_CONFIG_HOME:-$HOME/.config}/sway/icons/moon.png"
          if [ "$(cat "$state" 2>/dev/null)" = on ]; then echo off > "$state"; apply; notify-send -u low -i "$icon" "Night light" "off"
          else echo on > "$state"; apply || notify-send -u low -i "$icon" "Night light" "needs gammastep (install it)"
               notify-send -u low -i "$icon" "Night light" "on (${temp}K)"; fi
          pkill -RTMIN+10 -x waybar 2>/dev/null ;;      # (the bar shows it right away)
  init)   # (login: put back the night light and the software brightness, if either is in use)
          if [ "$(cat "$state" 2>/dev/null)" = on ] || [ -s "$bright" ]; then apply; fi ;;
  apply)  apply ;;
  status) # for the bar (Waybar, JSON): the text, and "on" / "off" so the bar's style can colour it
          if [ "$(cat "$state" 2>/dev/null)" = on ]; then printf '{"text": "󰖔 %sK", "class": "on", "tooltip": "Night light is on: click to turn it off"}\n' "$temp"
          else printf '{"text": "󰖙", "class": "off", "tooltip": "Night light: click to make the screen warmer"}\n'; fi ;;
  *) echo "usage: $0 toggle|init|status|apply" >&2; exit 2 ;;
esac
