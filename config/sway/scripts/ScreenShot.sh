#!/usr/bin/env bash
# Screenshots on Wayland. Needs: grim slurp wl-clipboard jq (optional: swappy to draw on the picture)
#   --now --in5 --in10   every screen     --area   a box you drag     --active   the window you are in
#   --swappy             a box you drag, opened in the editor (swappy)
dir="${XDG_PICTURES_DIR:-$HOME/Pictures}/Screenshots"; mkdir -p "$dir"
f="$dir/Screenshot_$(date +%d-%b_%H-%M-%S)_$RANDOM.png"
finish() {
  [ -s "$f" ] || { rm -f "$f"; notify-send -u low "Screenshot" "cancelled"; exit 1; }
  command -v wl-copy >/dev/null 2>&1 && wl-copy --type image/png <"$f"
  "${XDG_CONFIG_HOME:-$HOME/.config}/sway/scripts/Sounds.sh" --screenshot 2>/dev/null
  notify-send -i "$f" "Screenshot saved" "$f (also copied to clipboard)"
}
countdown() { for ((i=$1;i>0;i--)); do notify-send -t 900 -h string:x-dunst-stack-tag:shot "Screenshot in $i"; sleep 1; done; }
# the box you drag (nothing when you press Esc); the notification of a countdown is gone before the picture
area() { slurp -d -b '#00000055' -c '#ffffffff' -w 2 2>/dev/null; }
# the window you are in: its place on the screen, border included ("X,Y WxH" for grim)
active() {
  swaymsg -t get_tree 2>/dev/null | jq -r '.. | objects | select(.focused == true and (.type == "con" or .type == "floating_con"))
    | .rect | "\(.x),\(.y) \(.width)x\(.height)"' 2>/dev/null | head -n1
}
shot() { sleep 0.2; grim "$@" "$f" 2>/dev/null; }      # (a moment for the notification / the box to go away)
case "$1" in
  --now)    shot; finish ;;
  --in5)    countdown 5;  shot; finish ;;
  --in10)   countdown 10; shot; finish ;;
  --active) g=$(active); if [ -n "$g" ]; then shot -g "$g"; else shot; fi; finish ;;
  --area)   g=$(area); [ -n "$g" ] || { notify-send -u low "Screenshot" "cancelled"; exit 1; }; shot -g "$g"; finish ;;
  --swappy)
    if command -v swappy >/dev/null; then
      g=$(area); [ -n "$g" ] || exit 0           # (cancelled: Esc)
      snap="$(mktemp "${TMPDIR:-/tmp}/snip.XXXXXX.png")" || exit 1
      trap 'rm -f "$snap"' EXIT
      sleep 0.2; grim -g "$g" "$snap" 2>/dev/null
      [ -s "$snap" ] || exit 0
      swappy -f "$snap" & editor=$!
      # swappy opens small and then grows to fit the picture: center it again once it has its size
      ( for _ in 1 2 3 4 5 6; do sleep 0.25; swaymsg -q '[app_id="(?i)^swappy$"] move position center' 2>/dev/null; done ) &
      wait "$editor"
    else notify-send "Screenshot" "install swappy to draw on screenshots"; fi ;;
  *) echo "usage: $0 --now|--area|--active|--in5|--in10|--swappy"; exit 1 ;;
esac
