#!/usr/bin/env bash
# Power the bluetooth adapter on/off (a click on the bar).
command -v bluetoothctl >/dev/null 2>&1 || exit 0
if bluetoothctl show 2>/dev/null | grep -q 'Powered: yes'; then bluetoothctl power off; else rfkill unblock bluetooth 2>/dev/null; bluetoothctl power on; fi
pkill -RTMIN+11 -x waybar 2>/dev/null
