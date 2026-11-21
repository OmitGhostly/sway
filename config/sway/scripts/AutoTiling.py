#!/usr/bin/env python3
"""Spiral ("dwindle") tiling for sway, the way Hyprland tiles by default.

Whenever a window gets focus, sway is told to split it along its longer side: a wide window is split side by
side, a tall one top and bottom. Opening windows one after another fills the screen like Hyprland:

    [ 1 ]  ->  [ 1 | 2 ]  ->  [ 1 | 2 ]  ->  [ 1 |  2  ]
                              [   | 3 ]      [   | 3|4 ]

Tabbed / stacked containers (SUPER+ALT+2/3), floating and fullscreen windows are left alone.
Turn it on or off with SUPER+ALT+T, or in Settings > Appearance > Window tiling.

It also keeps the focus ring (the border in your accent colour) on every window: apps that draw their own title
bar - GNOME apps, Chrome, Electron apps like VS Code, Discord - can ask for no border after they have opened. Such
a border is put back. (To really hide a window's border, give it `border pixel 0` in the sway config: that is left
alone.)

And it makes the windows you are not in see-through, as much as Settings > Appearance > Window opacity says
(the focused window, video players and fullscreen windows stay solid; SUPER+CTRL+O sets one window by hand).
Game mode and SUPER+ALT+O (effects off) make every window solid. `kill -USR1` makes it look at every window again.
Needs nothing but python3: it talks to sway's IPC socket directly.

  AutoTiling.py            run (started by the sway config; only one copy ever runs)
  AutoTiling.py --toggle   switch between spiral and classic (side by side) tiling
  AutoTiling.py --status   print the current mode
"""
import fcntl
import json
import os
import re
import select
import signal
import socket
import struct
import subprocess
import sys
import time

MAGIC = b"i3-ipc"
RUN_COMMAND, GET_WORKSPACES, SUBSCRIBE, GET_TREE, GET_CONFIG = 0, 1, 2, 4, 9
EVENT_BIT = 1 << 31
MODES = ("dwindle", "classic")          # dwindle = Hyprland-style spiral, classic = plain sway (side by side)
DEFAULT_MODE = "dwindle"
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "sway")
SETTINGS = os.environ.get("SWAYDOTS_SETTINGS") or os.path.join(CONFIG_DIR, "settings.json")
RECONNECT_FOR = 30                       # seconds to wait for sway to answer again before exiting (logged out)
RING_WIDTH = 3                           # the border width the sway config gives every window
RING_RECHECK = (0.4, 1.2, 3.0, 6.0)      # seconds after a window opens to look again (apps drop it a bit later)
RING_POLL = 1.0                          # seconds between looks at every window (an app can drop it at any time)
WORKSPACE_EVENT = 0                      # sway IPC event: a workspace was made / focused / renamed ...
OPACITY_DEFAULT = {"active": 100, "inactive": 95}
OPACITY_MARK = "_swaydots_opacity"       # ToggleOpacity.sh: a window made see-through by hand (left alone)
SOLID_APPS = re.compile(r"(?i)^(mpv|vlc|org\.videolan\.vlc|swappy|com\.github\.rafostar\.clapper|"
                        r"gamescope|steam_app_.*)$")       # video players, the screenshot editor, games: always solid
STATE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "sway")


# ------------------------------------------------------------------ mode (stored in settings.json)
def _load():
    try:
        with open(SETTINGS) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


_cache = {"mtime": None, "mode": DEFAULT_MODE, "opacity": (1.0, 0.95)}


def _pct(v, default):
    try:
        return min(100, max(20, int(v))) / 100.0       # (20 %: lower would make windows practically invisible)
    except (TypeError, ValueError):
        return default / 100.0


def _reread():
    """Re-read settings.json only when it changed (cheap to call on every event)."""
    try:
        mtime = os.stat(SETTINGS).st_mtime_ns
    except OSError:
        mtime = None
    if mtime != _cache["mtime"]:
        data = _load()
        t = data.get("tiling")
        mode = t.get("mode") if isinstance(t, dict) else None
        o = data.get("opacity") if isinstance(data.get("opacity"), dict) else {}
        _cache.update(mtime=mtime, mode=mode if mode in MODES else DEFAULT_MODE,
                      opacity=(_pct(o.get("active"), OPACITY_DEFAULT["active"]),
                               _pct(o.get("inactive"), OPACITY_DEFAULT["inactive"])))
        return True
    return False


def read_mode():
    """The saved tiling mode."""
    _reread()
    return _cache["mode"]


def read_opacity():
    """(focused, other windows) opacity, 0.2-1.0 - all 1.0 in game mode and with the effects off (SUPER+ALT+O)."""
    _reread()
    if os.path.exists(os.path.join(STATE_DIR, "gamemode")) or os.path.exists(os.path.join(STATE_DIR, "effects-off")):
        return 1.0, 1.0
    return _cache["opacity"]


def save_mode(mode):
    data = _load()
    data["tiling"] = {"mode": mode}
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    tmp = SETTINGS + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, SETTINGS)


def notify(text):
    try:
        subprocess.run(["notify-send", "-u", "low", "Window tiling", text], capture_output=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        pass


# ------------------------------------------------------------------ sway IPC
def socket_path():
    """sway's socket: $SWAYSOCK, else the newest of this user's in $XDG_RUNTIME_DIR (started from elsewhere)."""
    path = os.environ.get("SWAYSOCK")
    if path and os.path.exists(path):
        return path
    run_dir = os.environ.get("XDG_RUNTIME_DIR") or "/run/user/%d" % os.getuid()
    try:
        socks = [os.path.join(run_dir, n) for n in os.listdir(run_dir)
                 if n.startswith("sway-ipc.%d." % os.getuid()) and n.endswith(".sock")]
    except OSError:
        socks = []
    socks.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    return socks[-1] if socks else ""


class IPC:
    def __init__(self, path):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(path)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("sway closed the connection")
            buf += chunk
        return buf

    def send(self, mtype, payload=""):
        body = payload.encode()
        self.sock.sendall(MAGIC + struct.pack("=II", len(body), mtype) + body)

    def recv(self):
        head = self._read(14)
        if head[:6] != MAGIC:
            raise ConnectionError("not a sway IPC reply")
        length, mtype = struct.unpack("=II", head[6:])
        return mtype, json.loads(self._read(length) or b"null")

    def request(self, mtype, payload=""):
        self.send(mtype, payload)
        while True:
            t, data = self.recv()
            if not t & EVENT_BIT:          # (this socket is not subscribed, but never mistake an event for the reply)
                return data


def find_focused(node, parent=None):
    if node.get("focused"):
        return node, parent
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        hit = find_focused(child, node)
        if hit:
            return hit
    return None


def is_window(con):
    """A real window (sway calls it a view): a Wayland app (app_id) or one running through XWayland."""
    return isinstance(con, dict) and con.get("type") in ("con", "floating_con") \
        and ("shell" in con or con.get("app_id") is not None or con.get("window"))


def keep_ring(cmd, con):
    """Put the border back on a window that drew its own instead (see the top of this file)."""
    if not is_window(con) or con.get("border") not in ("none", "csd"):
        return
    width = con.get("current_border_width")
    width = width if isinstance(width, int) and 1 <= width <= 20 else RING_WIDTH
    cmd.request(RUN_COMMAND, "[con_id=%d] border pixel %d" % (con["id"], width))


def workspace_names(cmd):
    """{2: "2:II", ...}: the names the sway config gives workspaces 1-10 (set $ws2 "2:II")."""
    cfg = cmd.request(GET_CONFIG)
    text = cfg.get("config", "") if isinstance(cfg, dict) else ""
    names = {}
    for num, name in re.findall(r'^[ \t]*set[ \t]+\$ws(\d+)[ \t]+"?([^"\n]*?)"?[ \t]*$', text, re.M):
        n = int(num)
        if 1 <= n <= 10 and re.fullmatch(r'%d(:[^"\\]{1,40})?' % n, name):
            names[n] = name
    return names


def name_workspaces(cmd):
    """Give a workspace that is called just "1" (sway makes one like that for each screen when it starts) its proper
    name, "1:I" - the bar shows "I" for it, the same as after SUPER+1. Without this the bar looked different right
    after logging in."""
    spaces = cmd.request(GET_WORKSPACES)
    if not isinstance(spaces, list):
        return
    taken = {w.get("name") for w in spaces if isinstance(w, dict)}
    names = None
    for w in spaces:
        name = w.get("name") if isinstance(w, dict) else None
        if not (isinstance(name, str) and name.isdigit()):
            continue
        if names is None:
            names = workspace_names(cmd)
        want = names.get(int(name))
        if want and want != name and want not in taken:
            cmd.request(RUN_COMMAND, 'rename workspace "%s" to "%s"' % (name, want))
            taken.add(want)


def all_windows(node):
    """Every window below `node` (tiled and floating)."""
    if is_window(node):
        yield node
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        yield from all_windows(child)


def check_all_rings(cmd):
    """Look at every window once. An app can change its mind about its title bar at any time (Chrome and Electron
    when you switch the "system title bar" setting, GTK apps when they are maximised or tiled, a window that
    finishes loading late) and sway does not tell anybody when the border goes: only looking finds out."""
    for con in all_windows(cmd.request(GET_TREE)):
        keep_ring(cmd, con)


def retile(cmd):
    """Set the split direction of the focused window to its longer side (what Hyprland's dwindle does)."""
    if read_mode() != "dwindle":
        return
    hit = find_focused(cmd.request(GET_TREE))
    if not hit:
        return
    con, parent = hit
    if con.get("type") != "con" or not is_window(con) or parent is None:
        return                                          # an empty workspace, a floating window or no window
    if parent.get("type") == "floating_con":
        return                                          # floating windows are placed by hand
    if con.get("fullscreen_mode") or parent.get("layout") in ("tabbed", "stacked"):
        return                                          # keep tabs / stacks the user asked for
    rect = con.get("rect") or {}
    width, height = rect.get("width", 0), rect.get("height", 0)
    if not width or not height:
        return
    want = "splitv" if height > width else "splith"
    if parent.get("layout") != want:
        cmd.request(RUN_COMMAND, "split vertical" if want == "splitv" else "split horizontal")


def window_opacity(con, focused_id, active, inactive):
    """How see-through a window should be: None = leave it (made see-through by hand: SUPER+CTRL+O)."""
    if OPACITY_MARK in (con.get("marks") or []):
        return None
    props = con.get("window_properties") or {}
    app = con.get("app_id") or props.get("class") or ""
    if con.get("fullscreen_mode") or SOLID_APPS.match(app):
        return 1.0
    return active if con.get("id") == focused_id else inactive


class Opacity:
    """The windows you are not in are see-through (Settings > Appearance > Window opacity). Only windows whose
    opacity should change get a command, so a focus change costs two commands, not one per window."""

    def __init__(self):
        self.set = {}                                   # con_id -> opacity sent last

    def update(self, cmd, tree=None):
        active, inactive = read_opacity()
        tree = tree if tree is not None else cmd.request(GET_TREE)
        wins = list(all_windows(tree)) if isinstance(tree, dict) else []
        focused = next((w["id"] for w in wins if w.get("focused")), None)
        todo, seen = [], set()
        for w in wins:
            cid = w.get("id")
            if not isinstance(cid, int):
                continue
            seen.add(cid)
            want = window_opacity(w, focused, active, inactive)
            if want is None:
                self.set.pop(cid, None)
                continue
            have = self.set.get(cid)
            if have is None:
                have = w.get("opacity") if isinstance(w.get("opacity"), (int, float)) else 1.0
            if abs(have - want) > 0.004:
                todo.append("[con_id=%d] opacity %.2f" % (cid, want))
            self.set[cid] = want
        for cid in list(self.set):
            if cid not in seen:
                del self.set[cid]                       # (closed)
        if todo:
            cmd.request(RUN_COMMAND, "; ".join(todo))


def run():
    lock_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    lock = open(os.path.join(lock_dir, "swaydots-autotiling-%d.lock" % os.getuid()), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0                                        # already running (a sway reload starts it again)
    # kill -USR1: look at every window's opacity again (game mode, effects toggled, SUPER+CTRL+O undone)
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_w, False)
    signal.set_wakeup_fd(wake_w)
    signal.signal(signal.SIGUSR1, lambda *_: None)
    opacity = Opacity()
    last_ok = time.monotonic()
    while True:
        events = cmd = None
        try:
            path = socket_path()
            if not path:
                raise ConnectionError("sway is not running")
            events, cmd = IPC(path), IPC(path)
            events.send(SUBSCRIBE, json.dumps(["window", "workspace"]))
            events.recv()                               # {"success": true}
            last_ok = time.monotonic()
            name_workspaces(cmd)
            retile(cmd)
            opacity.set.clear()
            opacity.update(cmd)
            later = []                                  # times to look at the windows again (just after one opened)
            checked = 0.0                               # when every window was last looked at
            while True:
                now = time.monotonic()
                if later and min(later) <= now or now - checked >= RING_POLL:
                    later = [t for t in later if t > now]
                    tree = cmd.request(GET_TREE)
                    for con in all_windows(tree):
                        keep_ring(cmd, con)
                    if _reread():                       # (Settings changed the opacity)
                        opacity.update(cmd, tree)
                    checked = last_ok = now
                wait = min([max(0.0, checked + RING_POLL - now)] + [max(0.0, t - now) for t in later])
                ready, _, _ = select.select([events.sock, wake_r], [], [], wait)
                if wake_r in ready:
                    try:
                        os.read(wake_r, 64)
                    except OSError:
                        pass
                    opacity.update(cmd)
                if events.sock not in ready:
                    continue
                mtype, ev = events.recv()
                if not (mtype & EVENT_BIT and isinstance(ev, dict)):
                    continue
                if mtype & ~EVENT_BIT == WORKSPACE_EVENT:
                    if ev.get("change") == "init":
                        name_workspaces(cmd)
                    continue
                change, con = ev.get("change"), ev.get("container")
                if change in ("new", "focus", "title", "floating", "move", "fullscreen_mode"):
                    keep_ring(cmd, con)
                if change == "new" and isinstance(con, dict) and isinstance(con.get("id"), int):
                    later += [time.monotonic() + d for d in RING_RECHECK]
                if change in ("focus", "new", "move", "floating"):
                    retile(cmd)
                    last_ok = time.monotonic()
                if change in ("focus", "new", "fullscreen_mode", "mark", "close"):
                    opacity.update(cmd)
        except (OSError, ConnectionError, ValueError):
            pass                                        # sway is reloading, or quit: try again for a while
        finally:
            for s in (events, cmd):
                if s:
                    s.close()
        if time.monotonic() - last_ok > RECONNECT_FOR:
            return 0                                    # sway is gone (logged out)
        time.sleep(0.5)


def ensure_running():
    """Start the tiler in the background if it is not running (e.g. after it was killed)."""
    path = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", "swaydots-autotiling-%d.lock" % os.getuid())
    try:
        with open(path, "w") as probe:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(probe, fcntl.LOCK_UN)
    except OSError:
        return                                          # it is running (it holds the lock)
    subprocess.Popen([sys.executable, os.path.abspath(__file__)], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv):
    if "--status" in argv:
        print(read_mode())
        return 0
    if "--toggle" in argv:
        new = "classic" if read_mode() == "dwindle" else "dwindle"
        save_mode(new)
        notify("Spiral (like Hyprland): new windows split the focused one" if new == "dwindle"
               else "Classic: new windows open side by side")
        ensure_running()
        print(new)
        return 0
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
