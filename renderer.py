"""Glyph-cache compositor + vendor-agnostic helpers.

Vendor-specific chrome and popups live in `vendors/*.py`.
This module keeps the shared building blocks:

  - `Renderer`: ScreenBuffer -> native pixel surface (glyph cache).
  - `word_wrap`: simple paragraph wrap, reused across vendors and game screens.

Back-compat: a few thin facades re-export AMI draw functions so any
old `import renderer; renderer.draw_setup(...)` call still works.
"""

import pygame

from theme import NATIVE_W, NATIVE_H
from font import GlyphCache, load_font


def word_wrap(text, width):
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= width:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


class Renderer:
    """Glyph-cache compositor: ScreenBuffer -> native-resolution surface."""

    def __init__(self):
        self.cache = GlyphCache(load_font())
        self.surface = pygame.Surface((NATIVE_W, NATIVE_H))

    def render(self, buf):
        get, blit = self.cache.get, self.surface.blit
        from theme import CELL_W, CELL_H
        for y, row in enumerate(buf.cells):
            py = y * CELL_H
            for x, (ch, fg, bg) in enumerate(row):
                blit(get(ch, fg, bg), (x * CELL_W, py))
        return self.surface


# ------------------------------------------------------------ facades

def draw_setup(buf, model):
    from vendors import ami
    ami.draw_setup(buf, model)


def draw_option_popup(buf, item, sel, model=None):
    from vendors import ami
    ami.draw_option_popup(buf, item, sel, model=model)


def draw_dialog(buf, title, lines, buttons, sel):
    from vendors import ami
    ami.draw_dialog(buf, title, lines, buttons, sel)


def draw_text_popup(buf, title, buffer, masked):
    from vendors import ami
    ami.draw_text_popup(buf, title, buffer, masked)


def draw_help_popup(buf):
    from vendors import ami
    ami.draw_help_popup(buf)
