"""Main menu, endless prompt, and options screen.

These live outside the BIOS chrome (they are pre-game / between-mode UI).
They share the POST screen's palette so the visual transition stays
consistent: black background, light grey text, accent on the active row.
"""

import os

import settings
from theme import GRID_W, GRID_H, POST_BG, POST_FG, POST_HI, WHITE


# ---------------------------------------------------------- shared helpers

def _box(buf, x, y, w, h, title=None):
    buf.box(x, y, w, h, WHITE, POST_BG, fill=False)
    if title:
        s = " %s " % title
        buf.text(x + (w - len(s)) // 2, y, s, POST_HI, POST_BG)


def _draw_centered_menu(buf, title, items, sel, footer=None):
    buf.clear(POST_FG, POST_BG)
    buf.text_center(2, "BIOS REPAIR SERVICE", POST_HI, POST_BG)
    buf.text_center(3, "main menu", POST_FG, POST_BG)

    w = max(36, max(len(label) for label, _ in items) + 16)
    h = len(items) * 2 + 4
    x = (GRID_W - w) // 2
    y = (GRID_H - h) // 2
    _box(buf, x, y, w, h, title)

    for i, (label, _) in enumerate(items):
        row_y = y + 2 + i * 2
        if i == sel:
            buf.fill(x + 2, row_y, w - 4, 1, " ", POST_BG, POST_HI)
            buf.text(x + (w - len(label)) // 2, row_y, label,
                     POST_BG, POST_HI)
        else:
            buf.text(x + (w - len(label)) // 2, row_y, label,
                     POST_FG, POST_BG)

    if footer:
        buf.text_center(GRID_H - 2, footer, POST_FG, POST_BG)
    else:
        buf.text_center(GRID_H - 2,
                        "↑↓: select   Enter: confirm   ESC: back",
                        POST_FG, POST_BG)


# ---------------------------------------------------------- screen objects

class MainMenu:
    """Top-level menu: Challenge / Endless / Options / Quit."""

    ITEMS = [
        ("Challenge Mode",   "challenge"),
        ("Endless Shift",    "endless"),
        ("Options",          "options"),
        ("Quit",             "quit"),
    ]

    def __init__(self):
        self.sel = 0

    def move(self, delta):
        self.sel = (self.sel + delta) % len(self.ITEMS)

    def chosen(self):
        return self.ITEMS[self.sel][1]

    def draw(self, buf, now, has_progress=False):
        labels = list(self.ITEMS)
        if has_progress:
            labels = [("Continue Campaign", "challenge")] + labels[1:]
        _draw_centered_menu(buf, "MAIN MENU",
                            [(l, k) for l, k in labels], self.sel,
                            footer=None)
        # If a save exists, the user is "continuing" rather than restarting.
        if has_progress and self.sel == 0:
            from game import GameManager
            try:
                gm = GameManager()
                tag = "Resume at level %d/%d" % (
                    gm.level + 1, len(gm.challenges))
                buf.text_center(GRID_H - 4, tag, POST_HI, POST_BG)
            except Exception:
                pass


class EndlessPrompt:
    """Endless mode setup: choose seed (random / fixed) and confirm."""

    def __init__(self):
        self.sel = 0
        self.seed_mode = "random"   # "random" | "daily"
        self.size = 5

    def items(self):
        seed_label = ("Seed: random each run"
                      if self.seed_mode == "random"
                      else "Seed: today (daily challenge)")
        return [
            (seed_label,                           "toggle_seed"),
            ("Tickets per shift: %d" % self.size,  "toggle_size"),
            ("Start shift",                         "start"),
            ("Back",                                "back"),
        ]

    def move(self, delta):
        items = self.items()
        self.sel = (self.sel + delta) % len(items)

    def activate(self):
        action = self.items()[self.sel][1]
        if action == "toggle_seed":
            self.seed_mode = ("daily" if self.seed_mode == "random"
                              else "random")
            return None
        if action == "toggle_size":
            order = [3, 5, 7, 10]
            i = order.index(self.size) if self.size in order else 0
            self.size = order[(i + 1) % len(order)]
            return None
        return action

    def picked_seed(self):
        if self.seed_mode == "daily":
            import datetime
            return int(datetime.date.today().strftime("%Y%m%d"))
        import random
        return random.randint(1, 1 << 30)

    def draw(self, buf, now):
        _draw_centered_menu(buf, "ENDLESS SHIFT", self.items(), self.sel,
                            footer="Generates a procedural queue of tickets")


class OptionsMenu:
    """Toggleable settings, persisted in settings.json with `_` prefix."""

    def __init__(self):
        self.sel = 0
        cur = settings.load()
        self.audio = bool(cur.get("_audio", True))
        self.scanlines = bool(cur.get("_scanlines", False))

    def items(self):
        return [
            ("Audio: %s" % ("ON" if self.audio else "OFF"),
             "toggle_audio"),
            ("CRT scanlines: %s" % ("ON" if self.scanlines else "OFF"),
             "toggle_scanlines"),
            ("Reset campaign progress",  "reset"),
            ("Back",                     "back"),
        ]

    def move(self, delta):
        items = self.items()
        self.sel = (self.sel + delta) % len(items)

    def activate(self):
        action = self.items()[self.sel][1]
        if action == "toggle_audio":
            self.audio = not self.audio
            self._persist()
            return None
        if action == "toggle_scanlines":
            self.scanlines = not self.scanlines
            self._persist()
            return None
        return action   # "reset" or "back" handled by App

    def _persist(self):
        cur = settings.load()
        cur["_audio"] = self.audio
        cur["_scanlines"] = self.scanlines
        settings.save(cur)

    def draw(self, buf, now):
        _draw_centered_menu(buf, "OPTIONS", self.items(), self.sel,
                            footer="Changes saved automatically")


class ConfirmDialog:
    """Yes/No confirmation, used by the Reset action."""

    def __init__(self, title, lines, on_yes):
        self.title = title
        self.lines = lines
        self.on_yes = on_yes
        self.sel = 1   # default to No for safety

    def move(self, delta):
        self.sel = (self.sel + delta) % 2

    def activate(self):
        if self.sel == 0:
            self.on_yes()
        return "back"

    def draw(self, buf, now):
        buf.clear(POST_FG, POST_BG)
        w = max(40, max(len(l) for l in self.lines) + 8)
        h = len(self.lines) + 6
        x = (GRID_W - w) // 2
        y = (GRID_H - h) // 2
        _box(buf, x, y, w, h, self.title)
        for i, line in enumerate(self.lines):
            buf.text(x + (w - len(line)) // 2, y + 2 + i, line,
                     POST_FG, POST_BG)
        buttons = ["Yes", "No"]
        bx = x + (w - 16) // 2
        by = y + h - 2
        for i, b in enumerate(buttons):
            text = "[%s]" % b
            if i == self.sel:
                buf.text(bx, by, " " + text + " ", POST_BG, POST_HI)
            else:
                buf.text(bx + 1, by, text, POST_FG, POST_BG)
            bx += 10
