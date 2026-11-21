#!/usr/bin/env bash
# The lock screen (swaylock): your wallpaper, blurred, with a ring in your accent colour while you type.
# Runs in the background (-f), so swayidle can go on; a second call while it is up does nothing.
pgrep -u "$UID" -x swaylock >/dev/null && exit 0
ACCENT=ffffff; ACCENT_MUTED=8c8c8c; . "${XDG_CONFIG_HOME:-$HOME/.config}/sway/accent.conf" 2>/dev/null   # colour chosen in Settings > Colors
[[ $ACCENT =~ ^[0-9a-fA-F]{6}$ ]] || ACCENT=ffffff; [[ $ACCENT_MUTED =~ ^[0-9a-fA-F]{6}$ ]] || ACCENT_MUTED=8c8c8c
cache="${XDG_CACHE_HOME:-$HOME/.cache}/sway"; mkdir -p "$cache"
wall="$cache/current_wallpaper"; img="$cache/lock.png"
args=(-f -c 010102)
im=$(command -v magick || command -v convert)
if [ -e "$wall" ] && [ -n "$im" ]; then
  if [ ! -f "$img" ] || [ "$wall" -nt "$img" ]; then
    # the size of the biggest screen, so the picture fills every one
    res=$(swaymsg -t get_outputs -r 2>/dev/null | jq -r '[.[] | select(.active) | .current_mode | "\(.width)x\(.height)"] | max_by(split("x") | map(tonumber) | .[0] * .[1]) // empty' 2>/dev/null)
    res=${res:-1920x1080}
    "$im" "$wall" -resize "${res}^" -gravity center -extent "$res" -blur 0x6 "$img" 2>/dev/null
  fi
  [ -f "$img" ] && args=(-f -i "$img" -s fill)
fi
args+=(--indicator-radius 90 --indicator-thickness 6
  --inside-color 00000066 --ring-color "${ACCENT}ff" --line-color 00000000 --separator-color 00000000
  --key-hl-color "${ACCENT_MUTED}ff" --bs-hl-color "${ACCENT}55" --text-color "${ACCENT}ff"
  --inside-ver-color 00000066 --ring-ver-color "${ACCENT}ff" --text-ver-color "${ACCENT}ff"
  --inside-wrong-color 00000066 --ring-wrong-color "${ACCENT_MUTED}ff" --text-wrong-color "${ACCENT}ff"
  --inside-clear-color 00000066 --ring-clear-color "${ACCENT}ff" --text-clear-color "${ACCENT}ff"
  --line-ver-color 00000000 --line-wrong-color 00000000 --line-clear-color 00000000
  --font "FantasqueSansM Nerd Font Mono" --show-failed-attempts)
# swaylock-effects (some distros ship it under the same name): a clock in the ring as well
swaylock --help 2>&1 | grep -q -- '--clock' && args+=(--clock --timestr "%H:%M" --datestr "%A, %d %B")
exec swaylock "${args[@]}"
