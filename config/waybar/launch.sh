#!/usr/bin/env bash
# The bar (Waybar). sway runs this at start and on every reload; the settings window after a bar change.
# Its look comes from the settings window (~/.config/sway/settings.json): SettingsGUI.py --bar-env writes Waybar's
# config.jsonc and style.css and the workspaces' look (workspaces.json) for the saved choices, then BarWorkspaces.py
# keeps the workspace items up to date. If the settings cannot be asked (python missing, a damaged settings file),
# the files written last time are used - or the ones the installer put here.
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
dir="$cfg/waybar"; scripts="$cfg/sway/scripts"
state="${XDG_STATE_HOME:-$HOME/.local/state}/sway-dots"; mkdir -p "$state"
exec 9>"${XDG_RUNTIME_DIR:-/tmp}/waybar-launch-$(id -u).lock"
flock -w 20 9   # one launch at a time (the settings window and a sway reload may both ask)
# stop the running bar. One still starting up can miss the first signal, so ask again and after 3 seconds force it
for ((try = 0; try < 15; try++)); do
  pgrep -u "$UID" -x waybar >/dev/null || break
  pkill -u "$UID" -x waybar 2>/dev/null
  sleep 0.2
done
pkill -KILL -u "$UID" -x waybar 2>/dev/null
while pgrep -u "$UID" -x waybar >/dev/null; do sleep 0.1; done
pkill -u "$UID" -f "sway/scripts/BarWorkspaces.py" 2>/dev/null
# game mode: no bar until it is switched off again
[ -e "${XDG_CACHE_HOME:-$HOME/.cache}/sway/gamemode" ] && exit 0
command -v waybar >/dev/null 2>&1 || exit 0

BAR_ICON_FONT="FantasqueSansM Nerd Font Mono 22px"
bar_env=$(python3 "$scripts/SettingsGUI.py" --bar-env 2>/dev/null)
if printf '%s\n' "$bar_env" | grep -q '^BAR_ICON_FONT='; then
  printf '%s\n' "$bar_env" >"$state/bar-env.tmp" && mv -f "$state/bar-env.tmp" "$state/bar-env"
elif [ -f "$state/bar-env" ]; then
  bar_env=$(cat "$state/bar-env")
fi
eval "$bar_env"
export BAR_ICON_FONT          # (Caffeine.sh draws its mug in it)

config="$dir/config.jsonc"
# the workspaces: written by BarWorkspaces.py (once now, so the bar starts with them; then whenever they change).
# Without a working python3 the bar uses Waybar's own workspace item instead (config-fallback.jsonc).
if python3 "$scripts/BarWorkspaces.py" --once >/dev/null 2>&1; then
  setsid python3 "$scripts/BarWorkspaces.py" >/dev/null 2>&1 </dev/null 9>&- &
else
  config="$dir/config-fallback.jsonc"
fi
[ -f "$config" ] || config="$dir/config-fallback.jsonc"
# SwayFX: the bar's blurred background is a rule sway applies when the bar appears - so it is set first
"$scripts/Effects.sh" 9>&- || true
# (9>&-: the bar and the workspaces must not keep the lock - the next launch would wait for it forever)
setsid waybar -c "$config" -s "$dir/style.css" >"$state/waybar.log" 2>&1 </dev/null 9>&- &
exit 0
