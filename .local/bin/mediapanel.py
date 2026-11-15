#!/usr/bin/env python3
"""FORM — media hover panel.

Waybar tooltips are plain Pango text: they cannot hold buttons or notice the
pointer. This daemon draws a real layer-shell panel under the media pill:

  * the pill's screen rectangle is read from Waybar through AT-SPI,
  * the pointer is polled through Hyprland's IPC socket,
  * hovering the pill opens the panel, moving into it keeps it open,
    moving away hides it within ~40 ms.

The panel shows the cover, track, progress and big transport buttons. With more
than one MPRIS player around it also grows a strip of player buttons along the
bottom, so the app the transport row talks to can be picked right here instead
of guessing which one `playerctl` resolved to. The choice lives in
mediaplayer.sh, the same file the bar pill reads.
"""

import fcntl
import hashlib
import os
import shutil
import socket
import subprocess
import time
import urllib.request

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GtkLayerShell", "0.1")

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, GtkLayerShell, Pango  # noqa: E402
import pyatspi  # noqa: E402

HOME = os.path.expanduser("~")
SCRIPTS = os.path.join(HOME, ".config/hypr/scripts")
PLAYERS_SH = os.path.join(SCRIPTS, "mediaplayer.sh")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.join(HOME, ".cache")), "form-media")
ACCENT_FILE = os.path.join(HOME, ".config/form/accent")
GLYPH = "\U000f075a"
SEP = "\x1f"
BAR_H = 30
PANEL_W = 392
POLL_MS = 40
FIND_EVERY = 5.0

os.makedirs(CACHE, exist_ok=True)


# ---------------------------------------------------------------- utilities

def accent():
    try:
        with open(ACCENT_FILE) as f:
            return f.read().strip() or "#ff4d00"
    except OSError:
        return "#ff4d00"


def rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def clock(seconds):
    seconds = max(0, int(seconds))
    if seconds >= 3600:
        return "%d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)
    return "%d:%02d" % (seconds // 60, seconds % 60)


def in_rect(x, y, rect):
    if not rect:
        return False
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


def cursor():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/%d" % os.getuid())
    path = os.path.join(runtime, "hypr", sig, ".socket.sock")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            s.connect(path)
            s.sendall(b"cursorpos")
            data = s.recv(64).decode()
        x, y = data.strip().split(",")
        return int(x), int(y)
    except Exception:
        return None


# ------------------------------------------------------------- player state

def short_name(player):
    """'firefox.instance_1_154' -> 'FIREFOX': what the pills and buttons show."""
    return player.split(".")[0].upper()


def run_sh(*args):
    try:
        return subprocess.check_output(
            [PLAYERS_SH] + list(args),
            stderr=subprocess.DEVNULL, text=True, timeout=3,
        ).strip()
    except Exception:
        return ""


def players_state():
    """(every player, the one being controlled) as mediaplayer.sh reports them."""
    names = [n for n in run_sh("list").splitlines() if n.strip()]
    active = run_sh("current") or None
    return names, active


def pctl(*args, player=None):
    """playerctl pinned to the selected player.

    Bare `playerctl` picks whichever MPRIS name it happens to see first, which
    with a browser tab and Spotify open is a coin toss.
    """
    cmd = ["playerctl"]
    if player:
        cmd += ["-p", player]
    return cmd + list(args)


def player_meta(player):
    try:
        out = subprocess.check_output(
            pctl("metadata", "--format", SEP.join([
                "{{status}}", "{{artist}}", "{{title}}", "{{album}}",
                "{{position}}", "{{mpris:length}}", "{{mpris:artUrl}}",
            ]), player=player),
            stderr=subprocess.DEVNULL, text=True, timeout=2,
        )
    except Exception:
        return None
    parts = out.rstrip("\n").split(SEP)
    if len(parts) < 7:
        return None
    return dict(zip(("status", "artist", "title", "album",
                     "position", "length", "art"), parts))


def player_loop(player):
    base = (player or "").split(".")[0]
    svc = "org.mpris.MediaPlayer2." + base
    try:
        out = subprocess.check_output(
            ["dbus-send", "--print-reply", "--dest=" + svc, "/org/mpris/MediaPlayer2",
             "org.freedesktop.DBus.Properties.Get", "string:org.mpris.MediaPlayer2.Player",
             "string:LoopStatus"],
            stderr=subprocess.DEVNULL, text=True, timeout=2,
        )
        for line in out.splitlines():
            if "string" in line:
                return line.split('"')[1] if '"' in line else ""
    except Exception:
        pass
    # fallback
    try:
        return subprocess.check_output(
            pctl("loop", player=player),
            stderr=subprocess.DEVNULL, text=True, timeout=2,
        ).strip()
    except Exception:
        return ""


def cover(url):
    if not url:
        return None
    key = hashlib.sha1(url.encode()).hexdigest()
    img = os.path.join(CACHE, key + ".img")
    if os.path.isfile(img) and os.path.getsize(img) > 0:
        return img
    try:
        if url.startswith("file://"):
            shutil.copy(url[7:], img)
        elif url.startswith("/"):
            shutil.copy(url, img)
        elif url.startswith(("http://", "https://")):
            with urllib.request.urlopen(url, timeout=3) as r, open(img + ".tmp", "wb") as f:
                f.write(r.read())
            os.replace(img + ".tmp", img)
        else:
            return None
    except Exception:
        return None
    return img if os.path.isfile(img) else None


def find_media_nodes():
    """Locate the Waybar labels of the media group.

    The note glyph and the player pill next to it are both labels; their names
    are the only stable handle Waybar gives us through AT-SPI. Both are returned
    so the hover region covers the whole group.
    """
    wanted = {GLYPH}
    for name in players_state()[0]:
        wanted.add(short_name(name))

    try:
        desk = pyatspi.Registry.getDesktop(0)
    except Exception:
        return []
    for app in desk:
        try:
            if "waybar" not in (app.name or "").lower():
                continue
        except Exception:
            continue
        found = []

        def walk(node, depth):
            if depth > 9:
                return
            try:
                role = node.getRoleName()
                name = node.name
            except Exception:
                return
            if role == "label" and name in wanted:
                if node not in found:
                    found.append(node)
                return
            try:
                for child in node:
                    walk(child, depth + 1)
            except Exception:
                pass

        for child in app:
            walk(child, 0)
        if found:
            return found
    return []


# ------------------------------------------------------------------- panel

class MediaPanel(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        self.accent = accent()
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        self.screen_w = monitor.get_geometry().width

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, BAR_H)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_namespace(self, "form-media")

        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame.get_style_context().add_class("panel")
        self.add(frame)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top.set_border_width(8)
        frame.pack_start(top, False, False, 0)

        self.cover = Gtk.Image()
        self.cover.set_size_request(80, 80)
        top.pack_start(self.cover, False, False, 0)

        meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        top.pack_start(meta, True, True, 0)

        self.status = Gtk.Label(label="", xalign=0)
        self.status.get_style_context().add_class("status")
        meta.pack_start(self.status, False, False, 0)

        self.track = Gtk.Label(label="", xalign=0)
        self.track.get_style_context().add_class("track")
        self.track.set_ellipsize(Pango.EllipsizeMode.END)
        self.track.set_max_width_chars(26)
        meta.pack_start(self.track, False, False, 0)

        self.detail = Gtk.Label(label="", xalign=0)
        self.detail.get_style_context().add_class("detail")
        self.detail.set_ellipsize(Pango.EllipsizeMode.END)
        self.detail.set_max_width_chars(26)
        meta.pack_start(self.detail, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.set_border_width(8)
        frame.pack_start(row, False, False, 0)

        self.progress = Gtk.DrawingArea()
        self.progress.set_size_request(-1, 8)
        self.progress.connect("draw", self.draw_progress)
        row.pack_start(self.progress, True, True, 0)

        self.time = Gtk.Label(label="")
        self.time.get_style_context().add_class("time")
        row.pack_start(self.time, False, False, 0)

        # One button per MPRIS player, sitting right above the transport row.
        # The box hides itself while only one player exists — a single button
        # would just repeat the cover that is already up there.
        self.players_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.players_box.set_homogeneous(True)
        self.players_box.get_style_context().add_class("players")
        self.players_box.set_no_show_all(True)
        frame.pack_start(self.players_box, False, False, 0)
        self.player_buttons = {}
        self.player_names = []

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        controls.set_homogeneous(True)
        frame.pack_start(controls, False, False, 0)

        self.buttons = {}
        for key, glyph, action, tooltip in (
            ("prev", "󰒮", "prev", "previous"),
            ("play", "󰐊", "play", "play / pause"),
            ("next", "󰒭", "next", "next"),
            ("repeat", "󰑗", "repeat", "repeat"),
        ):
            btn = Gtk.Button(label=glyph)
            btn.get_style_context().add_class("transport")
            btn.set_tooltip_text(tooltip)
            btn.connect("clicked", self.on_button, action)
            controls.pack_start(btn, True, True, 0)
            self.buttons[key] = btn

        self.set_size_request(PANEL_W, -1)
        self.connect("destroy", Gtk.main_quit)
        self.connect("size-allocate", self.on_size_allocate)

        self.media_rect = None
        self.pos_x = self.screen_w - PANEL_W
        self.placed_width = PANEL_W
        self.nodes = []
        self.last_find = 0.0
        self.pct = 0.0
        self.cover_key = None
        self.status_now = ""
        self.active_player = None

        self.apply_css()

        GLib.timeout_add(POLL_MS, self.pointer_tick)
        GLib.timeout_add(250, self.rect_tick)
        GLib.timeout_add(500, self.refresh_tick)

    # ------------------------------------------------------------------ css

    def apply_css(self):
        css = f"""
        window {{
            background-color: transparent;
        }}
        .panel {{
            background-color: #2e3440;
            border: 1px solid #4c566a;
            border-radius: 0;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
            padding: 4px;
        }}
        .panel label {{
            color: #d8dee9;
            font-family: "JetBrainsMono Nerd Font Mono";
        }}
        .panel .status {{
            color: #81a1c1;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        .panel .status.on {{
            color: {self.accent};
        }}
        .panel .track {{
            font-size: 15px;
            font-weight: 800;
            color: #eceff4;
        }}
        .panel .detail {{
            color: #81a1c1;
            font-size: 11px;
        }}
        .panel .time {{
            color: #81a1c1;
            font-size: 10px;
        }}
        .panel button.transport {{
            background-color: transparent;
            background-image: none;
            border: none;
            border-top: 1px solid #4c566a;
            border-radius: 0;
            box-shadow: none;
            color: #d8dee9;
            font-family: "JetBrainsMono Nerd Font Mono";
            font-size: 22px;
            padding: 8px 0;
            min-height: 0;
        }}
        .panel button.transport:hover {{
            background-color: {self.accent};
            color: #2e3440;
        }}
        .panel button.transport.on {{
            color: {self.accent};
        }}
        .panel button.transport.on:hover {{
            color: #2e3440;
        }}
        .panel .players button {{
            background-color: transparent;
            background-image: none;
            border: none;
            border-top: 1px solid #4c566a;
            border-right: 1px solid #4c566a;
            border-radius: 0;
            box-shadow: none;
            color: #81a1c1;
            font-family: "JetBrainsMono Nerd Font Mono";
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 6px 0;
            min-height: 0;
        }}
        .panel .players button:last-child {{
            border-right: none;
        }}
        .panel .players button:hover {{
            color: #d8dee9;
            background-color: #3b4252;
        }}
        .panel .players button.on {{
            background-color: {self.accent};
            color: #2e3440;
        }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ---------------------------------------------------------------- layout

    def panel_width(self):
        """Width used for positioning.

        GtkWindow answers 1 for a window that was never mapped, and the old code
        trusted that number: the panel was placed as if it were 1 px wide, hung
        off the right screen edge and only snapped under the pill on the next
        rect tick — that snap was the opening animation. The requested width is
        known up front, so use it and the panel is simply there.
        """
        width = self.get_allocated_width()
        if width <= 1:
            width = self.get_preferred_width()[1]
        return max(PANEL_W, width)

    def panel_rect(self):
        h = self.get_allocated_height()
        if h <= 0:
            h = self.get_preferred_height()[1]
        # extend upward to bridge the gap between bar and panel
        return (self.pos_x, BAR_H - 8, self.panel_width(), h + 8)

    def place(self):
        """Centre the panel under the media pill, clamped to the screen."""
        if not self.media_rect:
            return
        x, y, w, h = self.media_rect
        width = self.panel_width()
        self.placed_width = width
        centre = x + w / 2.0
        left = int(round(centre - width / 2.0))
        left = max(0, min(left, self.screen_w - width))
        self.pos_x = left
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, left)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, BAR_H)

    def on_size_allocate(self, _widget, alloc):
        """Keep the hidden panel centred if its width turned out different."""
        if self.get_visible() or not self.media_rect:
            return
        if abs(alloc.width - self.placed_width) > 0.5:
            self.place()

    # --------------------------------------------------------------- pointer

    def rect_tick(self):
        now = time.time()
        if not self.nodes or now - self.last_find > FIND_EVERY:
            if now - self.last_find < 1.0:
                return True
            self.last_find = now
            self.nodes = find_media_nodes()

        rects = []
        alive = []
        for node in self.nodes:
            try:
                ext = node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
            except Exception:
                continue
            if ext.width <= 1 or ext.x < 0 or ext.y < 0:
                continue
            alive.append(node)
            rects.append((ext.x, ext.y, ext.width, ext.height))
        self.nodes = alive

        if not rects:
            self.media_rect = None
            return True
        x0 = min(r[0] for r in rects)
        y0 = min(r[1] for r in rects)
        x1 = max(r[0] + r[2] for r in rects)
        y1 = max(r[1] + r[3] for r in rects)
        self.media_rect = (x0, y0, x1 - x0, y1 - y0)
        if self.get_visible():
            self.place()
        return True

    def pointer_tick(self):
        pos = cursor()
        if pos is None:
            return True
        x, y = pos
        if self.get_visible():
            bridge = (self.pos_x - 20, BAR_H - 8, self.panel_width() + 40, 16)
            if not (in_rect(x, y, self.media_rect) or in_rect(x, y, self.panel_rect()) or in_rect(x, y, bridge)):
                self.hide()
        elif in_rect(x, y, self.media_rect):
            if self.refresh():
                self.place()
                self.show_all()
        return True

    # ---------------------------------------------------------------- update

    def sync_players(self, names, active):
        """Player strip: rebuilt only when the set of players changes."""
        if names != self.player_names:
            for child in self.players_box.get_children():
                self.players_box.remove(child)
            self.player_buttons = {}
            for name in names:
                btn = Gtk.Button(label=short_name(name))
                btn.get_style_context().add_class("player")
                btn.set_tooltip_text(name)
                btn.connect("clicked", self.on_player, name)
                btn.show()
                self.players_box.pack_start(btn, True, True, 0)
                self.player_buttons[name] = btn
            self.player_names = list(names)
            # With a single player the cover above already says who it is.
            self.players_box.set_visible(len(names) > 1)

        for name, btn in self.player_buttons.items():
            ctx = btn.get_style_context()
            if name == active:
                ctx.add_class("on")
            else:
                ctx.remove_class("on")

    def on_player(self, _button, name):
        """Switch to the clicked player."""
        subprocess.Popen([PLAYERS_SH, "select", name])
        GLib.timeout_add(150, lambda: (self.refresh(), False)[1])

    def refresh_tick(self):
        if self.get_visible():
            self.refresh()
        return True

    def refresh(self):
        """Redraw from the selected player. False means nothing is playing."""
        names, active = players_state()
        self.active_player = active
        self.sync_players(names, active)

        meta = player_meta(active) if active else None
        if not meta or meta.get("status") in ("", "Stopped"):
            self.status_now = ""
            self.hide()
            return False

        status = meta["status"]
        self.status_now = status
        self.status.set_text("PLAYING" if status == "Playing" else "PAUSED")
        self.status.get_style_context().remove_class("on")
        if status == "Playing":
            self.status.get_style_context().add_class("on")

        self.track.set_text(meta.get("title") or "Unknown track")
        artist = meta.get("artist") or ""
        album = meta.get("album") or ""
        detail = " · ".join(p for p in (artist, album) if p)
        self.detail.set_text(detail or " ")
        self.detail.set_visible(bool(detail))

        art = meta.get("art") or ""
        if art != self.cover_key:
            self.cover_key = art
            path = cover(art)
            if path:
                try:
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 96, 96, True)
                    self.cover.set_from_pixbuf(pix)
                except Exception:
                    self.cover.clear()
            else:
                self.cover.clear()

        position = "".join(ch for ch in (meta.get("position") or "") if ch.isdigit())
        length = "".join(ch for ch in (meta.get("length") or "") if ch.isdigit())
        pos_s = int(position or 0) / 1_000_000
        len_s = int(length or 0) / 1_000_000
        self.pct = min(100.0, pos_s * 100.0 / len_s) if len_s > 0 else 0.0
        self.time.set_text(
            ("%s / %s" % (clock(pos_s), clock(len_s))) if len_s > 0 else ""
        )
        self.progress.queue_draw()

        self.buttons["play"].set_label("󰏤" if status == "Playing" else "󰐊")
        loop = player_loop(active)
        repeat = self.buttons["repeat"].get_style_context()
        if loop == "Track":
            self.buttons["repeat"].set_label("\U000f0458")
            self.buttons["repeat"].set_tooltip_text("repeat: track")
            repeat.add_class("on")
        elif loop == "Playlist":
            self.buttons["repeat"].set_label("\U000f0456")
            self.buttons["repeat"].set_tooltip_text("repeat: playlist")
            repeat.add_class("on")
        else:
            self.buttons["repeat"].set_label("\U000f0457")
            self.buttons["repeat"].set_tooltip_text("repeat: off")
            repeat.remove_class("on")
        return True

    def draw_progress(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        if width <= 0:
            return False
        cells = 20
        gap = 2
        cw = (width - gap * (cells - 1)) / cells
        filled = int(round(self.pct * cells / 100))
        if self.pct > 0 and filled < 1:
            filled = 1
        for i in range(cells):
            cr.set_source_rgb(*rgb(self.accent if i < filled else "#4c566a"))
            cr.rectangle(i * (cw + gap), 0, cw, height)
            cr.fill()
        return False

    # --------------------------------------------------------------- actions

    def on_button(self, _button, action):
        try:
            # Always use mediacontrol.sh so the pinned player (mediaplayer.sh current) is respected
            subprocess.Popen(["/home/turker/.config/hypr/scripts/mediacontrol.sh", action])
        except Exception:
            pass
        GLib.timeout_add(150, lambda: (self.refresh(), False)[1])


def main():
    lock = open(os.path.join(CACHE, "panel.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return
    panel = MediaPanel()  # noqa: F841
    Gtk.main()


if __name__ == "__main__":
    main()
