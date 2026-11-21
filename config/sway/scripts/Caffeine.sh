#!/usr/bin/env bash
# Stay awake: stops the screen from blanking / locking and blocks idle suspend until you turn it off or log out.
# Usage: toggle | on | off | status   (the coffee mug on the bar calls this)
tag='--who=swaydots-caffeine'
s="$(cd "$(dirname "$0")" && pwd)"
is_on() { pgrep -u "$UID" -f -- "systemd-inhibit .*$tag" >/dev/null 2>&1 || [ "$(cat "${XDG_RUNTIME_DIR:-/tmp}/swaydots-caffeine" 2>/dev/null)" = on ]; }
on() {
  is_on && return 0
  echo on > "${XDG_RUNTIME_DIR:-/tmp}/swaydots-caffeine"
  "$s/Idle.sh" stop                             # no auto-lock, no screen power-off
  if command -v systemd-inhibit >/dev/null 2>&1; then
    setsid systemd-inhibit --what=idle:sleep "$tag" --why="Stay awake (the bar)" --mode=block sleep infinity >/dev/null 2>&1 &
  fi
}
off() {
  for p in $(pgrep -u "$UID" -f -- "systemd-inhibit .*$tag" 2>/dev/null); do
    pkill -P "$p" 2>/dev/null; kill "$p" 2>/dev/null     # the 'sleep' it started, then the inhibitor itself
  done
  rm -f "${XDG_RUNTIME_DIR:-/tmp}/swaydots-caffeine"
  "$s/Idle.sh" restart                          # back to locking after 10 minutes
}
case "$1" in
  toggle) icon="${XDG_CONFIG_HOME:-$HOME/.config}/sway/icons/coffee.png"
          if is_on; then off; notify-send -u low -i "$icon" "Stay awake" "off - the screen can sleep again" 2>/dev/null
          else on; notify-send -u low -i "$icon" "Stay awake" "on - the screen will not sleep or lock" 2>/dev/null; fi
          pkill -RTMIN+9 -x waybar 2>/dev/null ;;       # (the mug on the bar changes right away)
  on)  on ;;
  off) off ;;
  status)
    # for the bar (Waybar, JSON): the text - the mug a little bigger, like the power button ($BAR_ICON_FONT, set
    # by waybar/launch.sh) - and "on" / "off", so the bar's style can colour it
    mug() { if [ -n "${BAR_ICON_FONT:-}" ]; then printf "<span font_desc='%s'>%s</span>" "$BAR_ICON_FONT" "$1"; else printf '%s' "$1"; fi; }
    if is_on; then printf '{"text": "%s awake", "class": "on", "tooltip": "Stay awake is on: click to let the screen sleep"}\n' "$(mug 󰅶)"
    else printf '{"text": "%s", "class": "off", "tooltip": "Stay awake: click to keep the screen on"}\n' "$(mug 󰛊)"; fi ;;
  *) echo "usage: $0 toggle|on|off|status" >&2; exit 1 ;;
esac
