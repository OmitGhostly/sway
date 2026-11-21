#!/usr/bin/env bash
# GTK apps on Wayland take their theme, icons and cursor from GNOME's settings store (gsettings), not from
# ~/.config/gtk-3.0/settings.ini. This copies what settings.ini says - the cursor from Settings > Mouse > Mouse
# cursor, a theme or icon theme set there by hand - into it, so the pointer and the look are the same over every
# window. sway runs this at start and on reload; the settings window after a change.
# The values that were there before are saved once (~/.local/state/sway-dots/gsettings-before), so the uninstaller
# can put them back - GNOME, if you also use it, reads the same store.
command -v gsettings >/dev/null 2>&1 || exit 0
ini="${XDG_CONFIG_HOME:-$HOME/.config}/gtk-3.0/settings.ini"
[ -f "$ini" ] || exit 0
schema=org.gnome.desktop.interface
gsettings list-keys "$schema" >/dev/null 2>&1 || exit 0
before="${XDG_STATE_HOME:-$HOME/.local/state}/sway-dots/gsettings-before"
val() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$ini" | tail -n1 | tr -d "\"'"; }
set_key() {   # set_key KEY VALUE [int]: only when it differs (a change wakes up every GTK app)
  [ -n "$2" ] || return 0
  local now want
  now=$(gsettings get "$schema" "$1" 2>/dev/null) || return 0
  if [ "${3:-}" = int ]; then want="$2"; now=${now#int32 }; else want="'$2'"; fi
  [ "$now" = "$want" ] && return 0
  mkdir -p "$(dirname "$before")"
  grep -q "^$1=" "$before" 2>/dev/null || printf '%s=%s\n' "$1" "$now" >>"$before"
  gsettings set "$schema" "$1" "$2" 2>/dev/null
}
set_key gtk-theme "$(val gtk-theme-name)"
set_key icon-theme "$(val gtk-icon-theme-name)"
set_key cursor-theme "$(val gtk-cursor-theme-name)"
size=$(val gtk-cursor-theme-size); case "$size" in ''|*[!0-9]*) size="" ;; esac
set_key cursor-size "$size" int
exit 0
