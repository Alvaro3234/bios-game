"""ScreenBuffer: a grid of (char, fg, bg) cells plus drawing primitives."""

from theme import GRID_W, GRID_H

# CP437 box-drawing characters (single line)
H, V = "─", "│"
TL, TR, BL, BR = "┌", "┐", "└", "┘"
TJ, BJ, LJ, RJ = "┬", "┴", "├", "┤"


class ScreenBuffer:
    def __init__(self):
        self.cells = [[(" ", (0, 0, 0), (0, 0, 0)) for _ in range(GRID_W)]
                      for _ in range(GRID_H)]
        # Pixel-art overlays blitted on top of the cell grid by the
        # Renderer: (image_key, x_px, y_px, anchor). See images.py.
        self.overlays = []

    def clear(self, fg, bg):
        cell = (" ", fg, bg)
        for row in self.cells:
            for x in range(GRID_W):
                row[x] = cell
        self.overlays = []

    def image(self, key, x, y, anchor="topleft"):
        """Queue the pixel-art image `key` (an images.py key) on top of
        the grid. x/y are pixel offsets from the anchored corner
        (anchor: "topleft" or "topright")."""
        self.overlays.append((key, x, y, anchor))

    def put(self, x, y, ch, fg, bg):
        if 0 <= x < GRID_W and 0 <= y < GRID_H:
            self.cells[y][x] = (ch, fg, bg)

    def text(self, x, y, s, fg, bg):
        for i, ch in enumerate(s):
            self.put(x + i, y, ch, fg, bg)

    def text_center(self, y, s, fg, bg):
        self.text((GRID_W - len(s)) // 2, y, s, fg, bg)

    def fill(self, x, y, w, h, ch, fg, bg):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, ch, fg, bg)

    def hline(self, x, y, w, fg, bg, left=H, mid=H, right=H):
        self.put(x, y, left, fg, bg)
        for xx in range(x + 1, x + w - 1):
            self.put(xx, y, mid, fg, bg)
        self.put(x + w - 1, y, right, fg, bg)

    def vline(self, x, y, h, fg, bg, top=V, mid=V, bottom=V):
        self.put(x, y, top, fg, bg)
        for yy in range(y + 1, y + h - 1):
            self.put(x, yy, mid, fg, bg)
        self.put(x, y + h - 1, bottom, fg, bg)

    def box(self, x, y, w, h, fg, bg, fill=True):
        if fill:
            self.fill(x + 1, y + 1, w - 2, h - 2, " ", fg, bg)
        self.hline(x, y, w, fg, bg, TL, H, TR)
        self.hline(x, y + h - 1, w, fg, bg, BL, H, BR)
        for yy in range(y + 1, y + h - 1):
            self.put(x, yy, V, fg, bg)
            self.put(x + w - 1, yy, V, fg, bg)

    def shadow(self, x, y, w, h, color):
        """Paint a drop shadow (right edge + bottom edge) behind a box."""
        for yy in range(y + 1, y + h + 1):
            for xx in (x + w, x + w + 1):
                self._darken(xx, yy, color)
        for xx in range(x + 2, x + w + 2):
            self._darken(xx, y + h, color)

    def _darken(self, x, y, color):
        if 0 <= x < GRID_W and 0 <= y < GRID_H:
            ch, _fg, _bg = self.cells[y][x]
            self.cells[y][x] = (ch, color, (0, 0, 0))
