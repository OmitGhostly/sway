#!/usr/bin/env bash
# Point ~/.config/sway/rofi/.current_wallpaper_focused at the current wallpaper (rofi themes use it as a background).
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
cur="${XDG_CACHE_HOME:-$HOME/.cache}/sway/current_wallpaper"
[ -e "$cur" ] || exit 0
mkdir -p "$cfg/sway/rofi"
ln -sf "$(readlink -f "$cur")" "$cfg/sway/rofi/.current_wallpaper_focused"
