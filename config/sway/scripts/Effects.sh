#!/usr/bin/env bash
# The window effects. SwayFX (sway with eye candy) draws rounded corners, shadows, blur behind see-through windows
# and the bar, and dims the windows you are not in - as Settings > Appearance says. Plain sway has none of these:
# then this does nothing (the window transparency works on both: AutoTiling.py).
#   Effects.sh            put on the saved effects (sway runs this at start and on every reload)
#   Effects.sh --toggle   effects off / back on (SUPER+ALT+O); off also makes every window solid
#   Effects.sh --off      every effect off for now (game mode)
#   Effects.sh --is-fx    exit status 0 when this is SwayFX
s="$(cd "$(dirname "$0")" && pwd)"
off_file="${XDG_CACHE_HOME:-$HOME/.cache}/sway/effects-off"
game_file="${XDG_CACHE_HOME:-$HOME/.cache}/sway/gamemode"
icon="${XDG_CONFIG_HOME:-$HOME/.config}/sway/icons/gamepad.png"
OFF='corner_radius 0; shadows disable; blur disable; default_dim_inactive 0.0'

# SwayFX knows "shadows"; plain sway answers that with an error. (Asked for every time: sway may have been swapped.)
is_fx() { swaymsg -t get_version 2>/dev/null | grep -qi swayfx && return 0
          swaymsg -q "shadow_blur_radius $(saved_shadow_radius)" >/dev/null 2>&1; }
saved_shadow_radius() { echo 8; }
apply_saved() {
  local cmds
  cmds=$(python3 "$s/SettingsGUI.py" --effects 2>/dev/null)
  [ -n "$cmds" ] || cmds='corner_radius 8; shadows enable; shadow_blur_radius 8; shadow_color #00000073; blur enable; blur_passes 3; blur_radius 5; default_dim_inactive 0.1; dim_inactive_colors.unfocused #000000FF; dim_inactive_colors.urgent #000000FF'
  swaymsg -q "$cmds" >/dev/null 2>&1 || {
    # (an older SwayFX that lacks one of the commands: send them one by one, so the rest still works)
    local c; IFS=';' read -ra parts <<<"$cmds"
    for c in "${parts[@]}"; do swaymsg -q "$c" >/dev/null 2>&1; done
  }
}
redo_opacity() { pkill -USR1 -f "sway/scripts/AutoTiling.py" 2>/dev/null; }

case "${1:-}" in
  --is-fx) is_fx; exit ;;
  --off)   is_fx && swaymsg -q "$OFF" >/dev/null 2>&1; redo_opacity; exit 0 ;;
  --toggle)
    mkdir -p "$(dirname "$off_file")"
    if [ -e "$off_file" ]; then
      rm -f "$off_file"; is_fx && apply_saved; redo_opacity
      notify-send -u low -i "$icon" "Effects" "on" 2>/dev/null
    else
      : >"$off_file"; is_fx && swaymsg -q "$OFF" >/dev/null 2>&1; redo_opacity
      notify-send -u low -i "$icon" "Effects" "off - every window solid, no rounding, blur or shadows" 2>/dev/null
    fi
    exit 0 ;;
  '') ;;
  *) echo "usage: $0 [--toggle|--off|--is-fx]" >&2; exit 2 ;;
esac
is_fx || exit 0
if [ -e "$off_file" ] || [ -e "$game_file" ]; then swaymsg -q "$OFF" >/dev/null 2>&1; else apply_saved; fi
exit 0
