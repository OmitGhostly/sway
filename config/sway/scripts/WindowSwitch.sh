#!/usr/bin/env bash
# The window switcher ($mod+a): every open window, on every workspace; pick one to go to it.
# rofi 2.0 and newer (Fedora, Arch) runs on Wayland itself and lists sway's windows on its own. An older rofi (1.7 on
# Debian, Ubuntu, Mint) runs through XWayland and would only see the X11 programs - so there the list comes from sway.
pkill -x rofi && exit 0
cfg="${XDG_CONFIG_HOME:-$HOME/.config}/sway/rofi/config.rasi"
ver="$(rofi -version 2>/dev/null)"
if ! printf '%s' "$ver" | grep -qE 'Version: 1\.' || printf '%s' "$ver" | grep -qi wayland; then
  exec rofi -show window -config "$cfg"          # (rofi 2.x, or the 1.7 Wayland fork "rofi-wayland")
fi

command -v jq >/dev/null || exec rofi -show window -config "$cfg"
# one line per window: its id, then "workspace   program   title" (the scratchpad's hidden windows left out)
mapfile -t rows < <(swaymsg -t get_tree -r 2>/dev/null | jq -r '
  .nodes[] | select(.name != "__i3") | .nodes[] | select(.type == "workspace") | . as $ws
  | [.. | objects | select((.type == "con" or .type == "floating_con") and (.pid // 0) > 0)][]
  | [.id, ($ws.name | sub("^[0-9]+:"; "")), (.app_id // .window_properties.class // "?"), (.name // "")] | @tsv' 2>/dev/null)
[ "${#rows[@]}" -gt 0 ] || exit 0
labels=()
for r in "${rows[@]}"; do
  IFS=$'\t' read -r _ ws app title <<<"$r"
  labels+=("$(printf '%-6s %-18.18s %s' "$ws" "$app" "$title")")
done
i="$(printf '%s\n' "${labels[@]}" | rofi -dmenu -i -format i -p window -config "$cfg")" || exit 0
[[ $i =~ ^[0-9]+$ ]] && [ "$i" -lt "${#rows[@]}" ] || exit 0
swaymsg "[con_id=${rows[$i]%%$'\t'*}] focus" >/dev/null
