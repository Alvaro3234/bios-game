"""Font loading (with fallback chain) and per-cell glyph cache."""

import os

import pygame

from paths import resource
from theme import CELL_W, CELL_H

# Preference order: authentic VGA ROM font first, then stock monospace
# fonts that still carry CP437 box-drawing glyphs.
_CANDIDATES = [
    resource("assets", "fonts", "PxPlus_IBM_VGA_8x16.ttf"),
    resource("assets", "fonts", "Px437_IBM_VGA_8x16.ttf"),
    r"C:\Windows\Fonts\lucon.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\cour.ttf",
]


def load_font():
    """Walk the fallback chain; return a pygame Font sized for 8x16 cells."""
    for path in _CANDIDATES:
        if os.path.isfile(path):
            try:
                return pygame.font.Font(path, CELL_H)
            except Exception:
                continue
    return pygame.font.SysFont("couriernew", CELL_H)


class GlyphCache:
    """Pre-rendered (char, fg, bg) cell surfaces; antialias off for crisp pixels."""

    def __init__(self, font):
        self.font = font
        self._cache = {}

    def get(self, ch, fg, bg):
        key = (ch, fg, bg)
        surf = self._cache.get(key)
        if surf is None:
            surf = pygame.Surface((CELL_W, CELL_H))
            surf.fill(bg)
            if ch != " ":
                try:
                    glyph = self.font.render(ch, False, fg)
                except (pygame.error, ValueError):
                    glyph = None
                if glyph is not None:
                    # Center in the cell so non-8x16 fallback fonts stay aligned
                    surf.blit(glyph, ((CELL_W - glyph.get_width()) // 2,
                                      (CELL_H - glyph.get_height()) // 2))
            self._cache[key] = surf
        return surf
