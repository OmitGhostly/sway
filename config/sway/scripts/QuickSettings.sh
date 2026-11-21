#!/usr/bin/env bash
cfgd="${XDG_CONFIG_HOME:-$HOME/.config}"
source "$cfgd/sway/defaults.conf" 2>/dev/null
# (term / editor may hold extra words, e.g. editor="code -w", so they are split on purpose)
# shellcheck disable=SC2086
edit() { ${term:-kitty} -e ${editor:-nano} "$1"; }
pkill -x rofi 2>/dev/null
c=$(printf '%s\n' "Settings window" "Edit sway config" "Edit keyboard and touchpad" "Edit defaults (apps)" "Edit waybar" "Edit rofi config" "Edit dunst" "Change wallpaper" "Reload sway" "Refresh bar/colors" |
    rofi -dmenu -i -p "Quick settings" -config "$cfgd/sway/rofi/config.rasi")
case "$c" in
  "Settings window") "$cfgd/sway/scripts/SettingsGUI.py" ;;
  "Edit sway config") edit "$cfgd/sway/config" ;;
  "Edit keyboard and touchpad") edit "$cfgd/sway/input.conf" ;;
  "Edit defaults (apps)") edit "$cfgd/sway/defaults.conf" ;;
  "Edit waybar") edit "$cfgd/waybar/launch.sh" ;;
  "Edit rofi config") edit "$cfgd/sway/rofi/config.rasi" ;;
  "Edit dunst") edit "$cfgd/dunst/dunstrc" ;;
  "Change wallpaper") "$cfgd/sway/scripts/WallpaperSelect.sh" ;;
  "Reload sway") swaymsg -q reload ;;
  "Refresh bar/colors") "$cfgd/sway/scripts/Refresh.sh" ;;
esac
