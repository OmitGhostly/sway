#!/usr/bin/env python3
"""Go to the next or previous workspace by number: 1 -> 2 -> 3 ... and back, also to an empty one (it is created,
like pressing SUPER+2). Stops at 1 and at 10.
Also moves the focused window to another workspace (SUPER+SHIFT+1..0, SUPER+CTRL+1..0, SUPER+SHIFT/CTRL+[ ]).

  Workspace.py next                  the workspace with the next number
  Workspace.py prev                  the workspace with the previous number
  Workspace.py move WS [follow]      move the focused window (or group) to workspace WS ("2:II", next, prev);
                                     with follow, go there too

When the focused thing is a workspace itself that holds nothing but floating windows (SUPER+CTRL+H on a floating
window), its floating windows are moved one by one; everything else is moved by sway's own command.
"""
import json
import re
import subprocess
import sys

FIRST, LAST = 1, 10


def sway(*args):
    """swaymsg (raw JSON replies)."""
    try:
        return subprocess.run(["swaymsg", "-r"] + list(args), capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def name_for(num):
    """The name the sway config gives workspace `num` (set $ws2 "2:II"), so a new one looks like SUPER+2 made it."""
    out = sway("-t", "get_config")
    try:
        config = json.loads(out).get("config", "")      # ({"config": "..."})
    except (ValueError, AttributeError):
        config = out
    m = re.search(r'^[ \t]*set[ \t]+\$ws%d[ \t]+"?([^"\n]*?)"?[ \t]*$' % num, config, re.M)
    name = m.group(1) if m else ""
    # only a plain "2" or "2:something" without quotes or backslashes goes into the sway command
    return name if re.fullmatch(r'%d(:[^"\\]{1,40})?' % num, name) else str(num)


MOVE_TARGET_RE = re.compile(r'(next|prev|(10|[1-9])(:[^"\\]{1,40})?)\Z')


def find_focused(node):
    if not isinstance(node, dict):
        return None
    if node.get("focused"):
        return node
    for child in (node.get("nodes") or []) + (node.get("floating_nodes") or []):
        hit = find_focused(child)
        if hit:
            return hit
    return None


def floating_only_windows(tree):
    """The window ids to move one by one when the focused thing is a workspace with nothing but floating windows on
    it (see the top of this file); None in every other case."""
    node = find_focused(tree)
    if not node or node.get("type") != "workspace" or node.get("nodes") or not node.get("floating_nodes"):
        return None
    ids = []
    for fcon in node["floating_nodes"]:
        for win in (fcon.get("nodes") or []) if isinstance(fcon, dict) else []:
            if isinstance(win, dict) and isinstance(win.get("id"), int):
                ids.append(win["id"])
    return ids


def move(target, follow):
    where = "workspace " + target if target in ("next", "prev") else 'workspace number "%s"' % target
    try:
        tree = json.loads(sway("-t", "get_tree") or "null")
    except ValueError:
        tree = None
    ids = floating_only_windows(tree)
    if ids is None:
        cmds = ["move container to " + where]
    else:
        cmds = ["[con_id=%d] move container to %s" % (i, where) for i in ids]
    if follow:
        cmds.append(where)
    sway("; ".join(cmds))
    return 0


def main(argv):
    if argv[:1] == ["move"] and len(argv) in (2, 3) and MOVE_TARGET_RE.match(argv[1]) \
            and (len(argv) == 2 or argv[2] == "follow"):
        return move(argv[1], len(argv) == 3)
    if len(argv) != 1 or argv[0] not in ("next", "prev"):
        print(__doc__.strip())
        return 2
    try:
        spaces = json.loads(sway("-t", "get_workspaces") or "[]")
    except ValueError:
        return 1
    if not isinstance(spaces, list):
        return 1
    cur = next((w for w in spaces if isinstance(w, dict) and w.get("focused")), None)
    if cur is None:
        return 1
    num = cur.get("num") if isinstance(cur.get("num"), int) else -1
    if num < FIRST:                                     # a workspace without a number: start from the first
        want = FIRST
    else:
        want = num + 1 if argv[0] == "next" else num - 1
    if not FIRST <= want <= LAST or want == num:
        return 0
    if any(isinstance(w, dict) and w.get("num") == want for w in spaces):
        sway("workspace number %d" % want)                # it exists (whatever its name)
    else:
        sway('workspace number "%s"' % name_for(want))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
