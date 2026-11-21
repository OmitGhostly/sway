#!/usr/bin/env bash
# Bluetooth for the bar: off / on / the connected device's name. Prints nothing without an adapter (the item hides).
command -v bluetoothctl >/dev/null 2>&1 || exit 0
show=$(timeout 3 bluetoothctl show 2>/dev/null) || exit 0
[ -n "$show" ] || exit 0
if ! grep -q 'Powered: yes' <<<"$show"; then echo "󰂲"; exit 0; fi
name=$(timeout 3 bluetoothctl devices Connected 2>/dev/null | head -n1 | cut -d' ' -f3-)
if [ -n "$name" ]; then echo "󰂱 ${name:0:18}"; else echo "󰂯"; fi
