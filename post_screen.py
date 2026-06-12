"""POST / boot splash: timed text reveal, memory count, blinking prompt.

Data-driven by the active vendor's spec:
    post_lines        [(ms, text), ...] revealed sequentially
    post_prompt       blinking "Press X to enter Setup" line
    post_prompt_keys  space-separated key names accepted ("del f2", "esc")
    post_palette      (bg, fg, hi)
    post_memcount     optional animated memory count:
                      {"t0", "dur", "after", "total", "step", "fmt",
                       "ok_suffix"} — drawn between line index `after`-1
                      and `after`, counting up to `total` in `step`s.
    post_show_code    show the 2-digit POST code bottom-right (default True)
    post_logo         optional pixel-art logo blitted top-right:
                      {"key": images.py key, "t": reveal ms (default 0)}

plus an optional per-ticket context:
    extra_lines       [(ms, text), ...] appended to the timeline
    post_code         stuck POST debug code (overrides the progression)
    variant           "ok" (default) | "no_video" (black screen, beeps only)
    beep              beep_map kind to play instead of "ok"
"""

import pygame

from theme import GRID_W, GRID_H, POST_BG, POST_FG, POST_HI

# Key names accepted in a vendor's `post_prompt_keys` string.
_KEY_NAMES = {
    "del": pygame.K_DELETE,
    "f1": pygame.K_F1,
    "f2": pygame.K_F2,
    "esc": pygame.K_ESCAPE,
}

# Fallback spec for a bare PostScreen with no vendor attached (the app
# always passes one; this guards direct/legacy use).
_FALLBACK = {
    "post_lines": [(300, "BIOS POST...")],
    "post_prompt": "Press DEL or F2 to enter Setup",
    "post_prompt_keys": "del f2",
    "post_palette": (POST_BG, POST_FG, POST_HI),
    "post_memcount": None,
    "post_show_code": True,
    "post_logo": None,
}

_SPEC_KEYS = tuple(_FALLBACK)

# 2-digit POST debug codes (Dr.-Debug style). Constraint/ticket `post_code`
# values come from this family so the code doubles as a diagnostic clue.
DEBUG_CODES = {
    "00": "CPU not executing / power cycling",
    "4F": "DXE IPL started",
    "55": "memory not installed or training failure",
    "94": "PCI bus enumeration",
    "99": "Super I/O initialization",
    "A0": "IDE initialization started",
    "A2": "IDE detect / boot device ready",
    "Eb": "thermal protection event",
    "d6": "no console output device found",
}

BLINK_MS = 530
NO_VIDEO_HINT_T = 3000          # ms before the accessibility line appears
_DEFAULT_BEEP_T = 2400          # OK-beep time when there is no memory count


class PostScreen:
    def __init__(self):
        self.t0 = 0
        self.spec = dict(_FALLBACK)
        self.context = {}
        self._beep_sent = False

    def reset(self, now, vendor_spec=None, context=None):
        self.t0 = now
        src = vendor_spec or {}
        self.spec = {k: src.get(k, _FALLBACK[k]) for k in _SPEC_KEYS}
        self.context = dict(context or {})
        self._beep_sent = False

    # ------------------------------------------------------------ timeline
    def timeline(self):
        lines = list(self.spec["post_lines"] or [])
        lines.extend(self.context.get("extra_lines") or [])
        return lines

    def prompt_t(self):
        times = [t for t, _ in self.timeline()] or [0]
        mc = self.spec.get("post_memcount")
        if mc:
            times.append(mc["t0"] + mc["dur"])
        return max(times) + 400

    # ------------------------------------------------------------ input
    def handle_key(self, key):
        """Returns 'setup' when the user requests Setup, 'off' to power
        down (no-video variant), else None."""
        if self.context.get("variant") == "no_video":
            return "off" if key == pygame.K_ESCAPE else None
        names = (self.spec.get("post_prompt_keys") or "del f2").split()
        accepted = tuple(_KEY_NAMES[n] for n in names if n in _KEY_NAMES)
        if key in accepted:
            return "setup"
        return None

    # ------------------------------------------------------------ audio
    def pending_beep(self, now):
        """Beep_map kind to play, exactly once per reset, when due."""
        if self._beep_sent:
            return None
        if self.context.get("variant") == "no_video":
            due = 600
        else:
            mc = self.spec.get("post_memcount")
            due = (mc["t0"] + mc["dur"]) if mc else _DEFAULT_BEEP_T
        if now - self.t0 >= due:
            self._beep_sent = True
            return self.context.get("beep", "ok")
        return None

    # ------------------------------------------------------------ render
    def draw(self, buf, now):
        t = now - self.t0
        bg, fg, hi = self.spec.get("post_palette") or _FALLBACK["post_palette"]
        buf.clear(fg, bg)

        if self.context.get("variant") == "no_video":
            self._draw_no_video(buf, t, bg)
            return

        logo = self.spec.get("post_logo")
        if logo and t >= logo.get("t", 0):
            buf.image(logo["key"], 8, 8, anchor="topright")

        lines = self.timeline()
        mc = self.spec.get("post_memcount")
        mem_after = mc.get("after", len(lines)) if mc else None

        y = 1
        for i, (reveal, text) in enumerate(lines):
            if mc is not None and i == mem_after:
                y = self._draw_memcount(buf, t, y, mc, fg, bg)
            if t >= reveal:
                buf.text(1, y, text, fg, bg)
            y += 1
        if mc is not None and mem_after >= len(lines):
            y = self._draw_memcount(buf, t, y, mc, fg, bg)

        if t >= self.prompt_t() and (t // BLINK_MS) % 2 == 0:
            prompt = self.spec.get("post_prompt") or ""
            buf.text(1, y + 1, prompt, hi, bg)

        if self.spec.get("post_show_code", True):
            code = self.context.get("post_code")
            if not code:
                mem_t0 = mc["t0"] if mc else 1000
                code = ("A2" if t >= self.prompt_t()
                        else ("99" if t >= mem_t0 else "4F"))
            buf.text(GRID_W - 3, GRID_H - 1, code, hi, bg)

    def _draw_memcount(self, buf, t, y, mc, fg, bg):
        """Animated count between two timeline lines; returns the next y."""
        if t >= mc["t0"]:
            frac = min(1.0, (t - mc["t0"]) / mc["dur"])
            step = mc.get("step", 64)
            n = int(mc["total"] * frac) // step * step
            line = mc.get("fmt", "Memory Testing : %d MB") % n
            if frac >= 1.0:
                line += mc.get("ok_suffix", " OK")
            buf.text(1, y + 1, line, fg, bg)
        return y + 3

    def _draw_no_video(self, buf, t, bg):
        """Dead-video POST: black screen; a dim accessibility transcript
        of the beep pattern appears after a few seconds."""
        if t < NO_VIDEO_HINT_T:
            return
        dim = (64, 64, 64)
        hint = self.context.get("no_video_hint",
                                "(no video signal — the board only beeps)")
        buf.text_center(GRID_H // 2, hint, dim, bg)
        if (t // BLINK_MS) % 2 == 0:
            buf.text_center(GRID_H // 2 + 2, "ESC: power off", dim, bg)
