#!/usr/bin/env python3
"""The workspaces on the bar (Waybar), shaped like the items on the right in every bar style: separate blocks, or
(Pill, Dark pill, Powerline) one strip whose ends are the first and last workspace's own ends - flush with the
numbers - with the workspace you are on a block inside it. With a one-sided block shape (Flag, Tag, Slanted, ...)
the left side is the mirror of the right side, and Powerline draws the workspaces as a chain pointing to the
middle like the items on the right: each one's end cuts into the next (a thin line where two in the same colour
meet).

Waybar's own workspace module cannot draw that: one look for all workspaces, and no workspace knows whether it is
the first or the last one. So the bar has one small item per workspace number (custom/ws1 ... custom/ws10, plus
custom/wsx for workspaces without a number and custom/wsmode for sway's mode, like "resize"), and this follows
sway and writes what each of them shows, for each screen, into $XDG_RUNTIME_DIR/swaydots-bar/SCREEN/ - then tells
Waybar to read them again (signal RTMIN+8). A workspace that does not exist is an empty file: its item hides.
(Waybar tells the items which screen their bar is on since version 0.10; an older one reads _any/, the screen
you are on.)
The look (colours, block ends, fonts) comes from ~/.config/waybar/workspaces.json, which the settings window writes
with the bar.

Only the workspaces on that screen plus urgent ones, sorted by number, "1:I" shown as "I"; click one to go there, scroll for the next / previous one; sway's mode (when not "default") at the end.
Needs nothing but python3: it talks to sway's IPC socket directly.

  BarWorkspaces.py                run (waybar/launch.sh starts it; only one copy runs)
  BarWorkspaces.py --once         write the files once and stop
  BarWorkspaces.py --show SCREEN  print what each item on SCREEN shows (for testing)
"""
import fcntl
import json
import os
import re
import select
import signal
import socket
import struct
import sys
import time

MAGIC = b"i3-ipc"
EVENT_BIT = 1 << 31
GET_WORKSPACES, SUBSCRIBE, GET_OUTPUTS, GET_BINDING_STATE = 1, 2, 3, 12
WORKSPACE_EVENT, OUTPUT_EVENT, MODE_EVENT, SHUTDOWN_EVENT = 0, 1, 2, 6
STATES = ("focused", "unfocused", "visible", "urgent", "mode")
SLOTS = [str(n) for n in range(1, 11)] + ["x", "mode"]
SIGNAL = 8                                   # Waybar's "signal" of the workspace items (RTMIN+8)
FONT = "FantasqueSansM Nerd Font Mono"
# used when workspaces.json cannot be read: the default look (Solid, rounded ends, white, the Large size)
DEFAULT_STYLE = {"shaped": True, "joined": False, "strip": None, "l": "\ue0b6", "r": "\ue0b4", "chain": False,
                 "thin": "#1c1c1c", "focused": ["#ffffff", "#000000"], "unfocused": ["#303030", "#e6e6e6"],
                 "visible": ["#303030", "#ffffff"], "urgent": ["#bfbfbf", "#000000"], "mode": ["#ffffff", "#000000"],
                 "cap_font": FONT + " 36.141px", "rise": 5500}
HEX = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
# each solid block end -> its thin outline (Nerd Font: the next code point), for two blocks of one colour in a chain
THIN = {chr(c): chr(c + 1) for c in range(0xe0b0, 0xe0c0, 2)}
CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
RUN_DIR = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
ANY = "_any"
OUT_DIR = os.path.join(RUN_DIR, "swaydots-bar")


# ------------------------------------------------------------------ the look
def style_path():
    return os.path.join(CONFIG_HOME, "waybar", "workspaces.json")


def read_style(path=None):
    """The look from workspaces.json (anything missing or damaged: the default)."""
    st = json.loads(json.dumps(DEFAULT_STYLE))
    try:
        with open(path or style_path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return st
    if not isinstance(data, dict):
        return st
    for k in ("shaped", "joined", "chain"):
        if isinstance(data.get(k), bool):
            st[k] = data[k]
    for k in ("strip", "thin"):
        if data.get(k) is None and k == "strip":
            st[k] = None
        elif isinstance(data.get(k), str) and HEX.match(data[k]):
            st[k] = data[k]
    for side in ("l", "r"):
        if isinstance(data.get(side), str) and len(data[side]) <= 1:
            st[side] = data[side]
    for state in STATES:
        pair = data.get(state)
        if isinstance(pair, list) and len(pair) == 2 and HEX.match(str(pair[1])) \
                and (pair[0] is None or HEX.match(str(pair[0]))):
            st[state] = pair
    if isinstance(data.get("cap_font"), str) and re.match(r"^[A-Za-z0-9 .]+px$", data["cap_font"]):
        st["cap_font"] = data["cap_font"]
    if isinstance(data.get("rise"), int):
        st["rise"] = data["rise"]
    if not st["joined"]:
        st["strip"] = None
    return st


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;")


def plan(items, st):
    """What to draw for [(text, state)], item by item: a list of pieces for each one -
        ("cap", glyph, colour, colour behind it or None = the bar)   a block end
        ("room", colour)                                              a gap as wide as a block end
        ("text", text, colour, block colour or None = just text)
    Nothing moves when you switch workspaces: every item takes the same room whatever its state.
      separate blocks: each workspace its own block with both ends
      strip (pill, dark pill, symmetric shapes): room for an end on either side of each item - inside the strip
        that is the strip, or the ends of a block that sits in it; at the two outer ends it is the first / last
        item's own end, on the bar
      chain (powerline with a one-sided shape): the first item's start, then each item's end cutting into the
        next one (a thin line between two in one colour), the last one's end on the bar"""
    strip, left, right = st["strip"], st["l"], st["r"]
    colours = [st[state] for _, state in items]
    out = []
    for i, (text, state) in enumerate(items):
        bg, fg = colours[i]
        pieces = []
        if bg is None:                                       # text only (the underline / glow / flat styles)
            pieces.append(("text", text, fg, None))
        elif not st["joined"]:
            if left:
                pieces.append(("cap", left, bg, None))
            pieces.append(("text", text, fg, bg))
            if right:
                pieces.append(("cap", right, bg, None))
        elif st.get("chain"):
            if i == 0 and left:
                pieces.append(("cap", left, bg, None))
            pieces.append(("text", text, fg, bg))
            if i < len(items) - 1:
                after = colours[i + 1][0] or strip
                if not right:
                    pieces.append(("room", bg))               # flat ends: the blocks just meet
                elif after != bg:
                    pieces.append(("cap", right, bg, after))
                else:
                    pieces.append(("cap", THIN.get(right, right), st["thin"], bg))
            elif right:
                pieces.append(("cap", right, bg, None))
        else:
            inner = bg != strip
            for side, glyph in (("l", left), ("r", right)):
                if side == "r":
                    pieces.append(("text", text, fg, bg))
                if not glyph:
                    continue
                if (i == 0) if side == "l" else (i == len(items) - 1):
                    pieces.append(("cap", glyph, bg, None))  # the end of the whole strip, on the bar
                elif inner:
                    pieces.append(("cap", glyph, bg, strip))  # a block's end cutting into the strip
                else:
                    pieces.append(("room", strip))           # just the strip
        out.append(pieces)
    return out


def markup(pieces, st):
    """Pango markup for one item's pieces."""
    pad = " " if st["shaped"] else "  "
    out = ""
    if st["shaped"] and not any(p[0] in ("cap", "room") for p in pieces):
        # no ends (the Square shape): a zero-width character in the ends' font makes the block as tall as the bar
        out += "<span font_desc='%s'>\u200b</span>" % st["cap_font"]
    for p in pieces:
        if p[0] == "cap":
            out += "<span font_desc='%s' foreground='%s'%s>%s</span>" % (
                st["cap_font"], p[2], " background='%s'" % p[3] if p[3] else "", p[1])
        elif p[0] == "room":
            out += "<span font_desc='%s' background='%s'> </span>" % (st["cap_font"], p[1])
        else:
            # (without block ends - Underline, Glow, Flat - the bar's style sheet gives the item its background:
            # that one fills the whole height of the bar)
            bg = p[3] if st["shaped"] else None
            out += "<span foreground='%s'%s rise='%d'>%s%s%s</span>" % (
                p[2], " background='%s'" % bg if bg else "", st["rise"], pad, esc(p[1]), pad)
    return out


# ------------------------------------------------------------------ sway
def socket_path():
    path = os.environ.get("SWAYSOCK")
    if path and os.path.exists(path):
        return path
    try:
        socks = [os.path.join(RUN_DIR, n) for n in os.listdir(RUN_DIR)
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
            if not t & EVENT_BIT:
                return data


def shown_name(name):
    """"1:I" -> "I" (everything up to the first ":" goes)."""
    return name.split(":", 1)[-1].strip(" ")


def slot_of(ws):
    num = ws.get("num")
    if isinstance(num, int) and 1 <= num <= 10 and re.match(r"^%d(:|$)" % num, ws.get("name", "")):
        return str(num)
    return "x"


def items_for(workspaces, mode, output):
    """[(slot, text, state)] for one screen, in bar order."""
    mine = [w for w in workspaces if w.get("output") == output or w.get("urgent")]
    if not any(w.get("output") == output for w in workspaces):
        mine = list(workspaces)                     # (a screen with no workspaces of its own: show them all)
    mine.sort(key=lambda w: (slot_of(w) == "x", w.get("num", -1) if isinstance(w.get("num"), int) else -1,
                             w.get("name", "")))
    items = []
    for w in mine:
        if w.get("focused"):
            state = "focused"
        elif w.get("urgent"):
            state = "urgent"
        elif w.get("visible"):
            state = "visible"
        else:
            state = "unfocused"
        items.append((slot_of(w), shown_name(w.get("name", "")), state))
    if mode and mode != "default":
        items.append(("mode", mode, "mode"))
    return items


def slots_for(items, st):
    """{slot: (markup, state)}: what each item on the bar shows (several unnumbered workspaces share "x")."""
    out = {s: ("", "") for s in SLOTS}
    for (slot, _text, state), pieces in zip(items, plan([(t, s) for _, t, s in items], st)):
        text, old_state = out[slot]
        out[slot] = (text + markup(pieces, st), old_state or state)
    return out


def tooltip(slot, items):
    names = [t for s, t, _ in items if s == slot]
    return ", ".join(names)


def write_slots(output, slots, items, written):
    """Write the files of one screen that changed; True when something did."""
    if not re.match(r"^[A-Za-z0-9_.:-]+$", output or "") or output.startswith("."):
        return False
    d = os.path.join(OUT_DIR, output)
    os.makedirs(d, exist_ok=True)
    changed = False
    for slot, (text, state) in slots.items():
        line = json.dumps({"text": text, "class": state or "empty", "tooltip": tooltip(slot, items)}) + "\n"
        key = (output, slot)
        if written.get(key) == line and os.path.exists(os.path.join(d, slot)):
            continue
        tmp = os.path.join(d, ".%s.tmp" % slot)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(line)
        os.replace(tmp, os.path.join(d, slot))
        written[key] = line
        changed = True
    return changed


WAYBAR_SETTLE = 3.0       # seconds: a Waybar younger than this may not handle the signal yet (it would quit on it)


def _age(pid):
    """How long a process has been running, in seconds (None if it cannot be told)."""
    try:
        with open("/proc/%s/stat" % pid) as f:
            start = int(f.read().rsplit(")", 1)[1].split()[19])
        with open("/proc/uptime") as f:
            up = float(f.read().split()[0])
        return up - start / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError):
        return None


def tell_waybar():
    """Waybar reads the files again (signal RTMIN+8 to this user's waybar). A Waybar that has only just started is
    not told: until it has set itself up, that signal would end it (it reads the files as it starts anyway).
    Returns True when one was left out (ask again in a moment)."""
    sig = signal.SIGRTMIN + SIGNAL
    uid = os.getuid()
    skipped = False
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open("/proc/%s/comm" % pid) as f:
                if f.read().strip() != "waybar":
                    continue
            if os.stat("/proc/%s" % pid).st_uid != uid:
                continue
            age = _age(pid)
            if age is None or age < WAYBAR_SETTLE:
                skipped = True
                continue
            os.kill(int(pid), sig)
        except (OSError, ValueError):
            pass
    return skipped


def current_mode(ipc):
    try:
        return (ipc.request(GET_BINDING_STATE) or {}).get("name", "default")
    except (ConnectionError, OSError, ValueError, AttributeError):
        return "default"


def outputs_of(ipc):
    outs = ipc.request(GET_OUTPUTS) or []
    return [o.get("name") for o in outs if isinstance(o, dict) and o.get("active") and o.get("name")]


def update(query, mode, st, written, tell=True):
    """Write what changed; True when a Waybar still has to be told (it had only just started)."""
    spaces = query.request(GET_WORKSPACES) or []
    changed = False
    for output in outputs_of(query):
        items = items_for(spaces, mode, output)
        changed |= write_slots(output, slots_for(items, st), items, written)
    # ANY: the screen you are on, for a Waybar too old to say which screen its bar is on (before 0.10)
    focused = next((w.get("output") for w in spaces if w.get("focused")), None)
    if focused:
        items = items_for(spaces, mode, focused)
        changed |= write_slots(ANY, slots_for(items, st), items, written)
    return tell_waybar() if changed and tell else False


def main(argv):
    if argv[:1] == ["--show"] and len(argv) == 2:
        st = read_style()
        ipc = IPC(socket_path())
        items = items_for(ipc.request(GET_WORKSPACES) or [], current_mode(ipc), argv[1])
        for slot, (text, state) in slots_for(items, st).items():
            print("%-5s %-9s %s" % (slot, state, text))
        return 0
    once = "--once" in argv
    if not once:
        lock = open(os.path.join(RUN_DIR, "swaydots-barworkspaces-%d.lock" % os.getuid()), "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return 0                                # already running
    # kill -USR1: read the look again (the settings window changed the bar)
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_w, False)
    signal.set_wakeup_fd(wake_w)
    signal.signal(signal.SIGUSR1, lambda *_: None)
    st = read_style()
    written = {}
    last_ok = time.monotonic()
    while True:
        query = events = None
        try:
            path = socket_path()
            if not path:
                raise ConnectionError("sway is not running")
            query, events = IPC(path), IPC(path)
            mode = current_mode(query)
            events.send(SUBSCRIBE, json.dumps(["workspace", "mode", "output", "shutdown"]))
            last_ok = time.monotonic()
            pending = False                             # a Waybar that was too young to be told
            while True:
                pending = update(query, mode, st, written, tell=not once) or pending
                if once:
                    return 0
                ready, _, _ = select.select([events.sock, wake_r], [], [], WAYBAR_SETTLE if pending else None)
                if not ready and pending:
                    pending = tell_waybar()
                    continue
                if wake_r in ready:
                    try:
                        os.read(wake_r, 64)
                    except OSError:
                        pass
                    st = read_style()
                    written.clear()
                if events.sock not in ready:
                    continue
                t, data = events.recv()
                if not t & EVENT_BIT:                   # (the reply to the subscription)
                    continue
                if t == EVENT_BIT | MODE_EVENT and isinstance(data, dict):
                    mode = data.get("change", "default")
                elif t == EVENT_BIT | SHUTDOWN_EVENT:
                    raise ConnectionError("sway is quitting")
                last_ok = time.monotonic()
        except (OSError, ConnectionError, ValueError):
            if once:
                return 1
        finally:
            for c in (query, events):
                if c:
                    c.close()
        if time.monotonic() - last_ok > 30:
            return 0                                    # sway is gone (logged out)
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(0)
