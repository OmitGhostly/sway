#!/usr/bin/env bash
# The clipboard history: cliphist keeps what you copy (text and pictures; wl-paste watches the clipboard), or
# CopyQ where cliphist is not packaged. sway runs this at login; one copy only.
if command -v cliphist >/dev/null 2>&1 && command -v wl-paste >/dev/null 2>&1; then
  pgrep -u "$UID" -f "wl-paste --type (text|image) --watch cliphist" >/dev/null 2>&1 && exit 0
  setsid wl-paste --type text --watch cliphist store >/dev/null 2>&1 </dev/null &
  setsid wl-paste --type image --watch cliphist store >/dev/null 2>&1 </dev/null &
elif command -v copyq >/dev/null 2>&1; then
  pgrep -u "$UID" -x copyq >/dev/null 2>&1 || exec copyq --start-server
fi
exit 0
