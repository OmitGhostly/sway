#!/usr/bin/env bash
# Screen lock and screen power-off when you are away, lock before the computer sleeps (swayidle):
# locked after 10 minutes, screens off after 12 (they come back on with the first key press or mouse move).
# "Stay awake" (Caffeine.sh, the mug on the bar) stops it; a video playing in fullscreen holds it off too (the
# inhibit_idle rule in the sway config).
#   Idle.sh          start it (sway runs this at login); one copy only
#   Idle.sh restart  start it again (Caffeine.sh, when stay awake goes off)
#   Idle.sh stop     stop it
LOCK_AFTER=${SWAYDOTS_LOCK_AFTER:-600}
OFF_AFTER=${SWAYDOTS_SCREEN_OFF_AFTER:-720}
lock="$(cd "$(dirname "$0")" && pwd)/LockScreen.sh"
command -v swayidle >/dev/null 2>&1 || exit 0
# this session's swayidle (one left over from another sway session - logged in twice - is not ours)
ours() {
  local p
  for p in $(pgrep -u "$UID" -x swayidle 2>/dev/null); do
    tr '\0' '\n' 2>/dev/null <"/proc/$p/environ" | grep -qx "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}" && echo "$p"
  done
}
mine() { [ -n "$(ours)" ]; }
stop() {
  local p
  for p in $(ours); do kill "$p" 2>/dev/null; done
  for _ in 1 2 3 4 5 6 7 8 9 10; do mine || return 0; sleep 0.1; done
  for p in $(ours); do kill -KILL "$p" 2>/dev/null; done
}
case "${1:-}" in
  stop) stop; exit 0 ;;
  restart) stop ;;
  '') mine && exit 0 ;;
  *) echo "usage: $0 [restart|stop]" >&2; exit 2 ;;
esac
# (stay awake is on: nothing to start)
[ "$(cat "${XDG_RUNTIME_DIR:-/tmp}/swaydots-caffeine" 2>/dev/null)" = on ] && exit 0
setsid swayidle -w \
  timeout "$LOCK_AFTER" "$lock" \
  timeout "$OFF_AFTER" 'swaymsg "output * power off"' resume 'swaymsg "output * power on"' \
  before-sleep "$lock" \
  lock "$lock" \
  >/dev/null 2>&1 </dev/null &
exit 0
