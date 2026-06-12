"""Runtime-generated pixel art: vendor POST logos and bench tool icons.

No binary image assets: every surface is drawn once with pygame.draw
plus the bundled VGA font, cached by key, and blitted by the Renderer
wherever a ScreenBuffer overlay references it (ScreenBuffer.image()).

Keys:
    logo_ami       blue AMI badge (AMI Aptio POST, top-right)
    logo_energy    Energy-Star-style emblem (Award POST, top-right)
    logo_phoenix   stylized phoenix bird (PhoenixBIOS POST, top-right)
    icon_battery   16x16 CR2032 coin cell (briefing toolbar)
    icon_jumper    16x16 CLR_CMOS jumper block (briefing toolbar)
"""

import math

import pygame

import font as _font

_CACHE = {}
_FONT = None


def get(key):
    """Return the cached Surface for `key`, building it on first use."""
    surf = _CACHE.get(key)
    if surf is None:
        surf = _BUILDERS[key]()
        _CACHE[key] = surf
    return surf


def _vga():
    global _FONT
    if _FONT is None:
        _FONT = _font.load_font()
    return _FONT


def _text(surf, x, y, s, color, scale=1):
    glyphs = _vga().render(s, False, color)
    if scale != 1:
        glyphs = pygame.transform.scale(
            glyphs, (glyphs.get_width() * scale, glyphs.get_height() * scale))
    surf.blit(glyphs, (x, y))


def _star(surf, cx, cy, r, color):
    """Filled 5-point star, tip up."""
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pygame.draw.polygon(surf, color, pts)


# ------------------------------------------------------------ POST logos

def _logo_ami():
    s = pygame.Surface((96, 48), pygame.SRCALPHA)
    s.fill((0, 0, 168))
    pygame.draw.rect(s, (255, 255, 255), s.get_rect(), 2)
    _text(s, 24, 4, "AMI", (255, 255, 255), scale=2)
    pygame.draw.rect(s, (200, 30, 30), (10, 40, 76, 3))
    return s


def _logo_energy():
    g = (192, 192, 192)
    s = pygame.Surface((104, 64), pygame.SRCALPHA)
    pygame.draw.rect(s, g, s.get_rect(), 1)
    _star(s, 24, 26, 17, g)
    _text(s, 46, 10, "ENERGY", (255, 255, 255))
    _text(s, 54, 28, "STAR", g)
    _text(s, 8, 46, "EPA SAVER", g)
    return s


def _logo_phoenix():
    orange = (255, 140, 0)
    red = (210, 40, 20)
    s = pygame.Surface((96, 56), pygame.SRCALPHA)
    # Swept wings
    pygame.draw.polygon(s, orange, [(10, 12), (44, 26), (24, 36)])
    pygame.draw.polygon(s, orange, [(86, 12), (52, 26), (72, 36)])
    # Rising flame body
    pygame.draw.polygon(s, red, [(48, 4), (56, 18), (52, 20), (60, 32),
                                 (48, 27), (36, 32), (44, 20), (40, 18)])
    _text(s, 20, 38, "PHOENIX", (192, 192, 192))
    return s


# ------------------------------------------------------------ tool icons

def _icon_battery():
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(s, (168, 168, 168), (8, 8), 7)
    pygame.draw.circle(s, (232, 232, 232), (8, 8), 7, 2)
    pygame.draw.line(s, (60, 60, 60), (5, 8), (11, 8))
    pygame.draw.line(s, (60, 60, 60), (8, 5), (8, 11))
    return s


def _icon_jumper():
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 110, 40), (1, 11, 14, 4))       # PCB strip
    for x in (3, 7, 11):
        pygame.draw.rect(s, (212, 175, 55), (x, 3, 2, 8))   # header pins
    pygame.draw.rect(s, (30, 30, 30), (2, 4, 8, 6))         # cap on 1-2
    return s


_BUILDERS = {
    "logo_ami": _logo_ami,
    "logo_energy": _logo_energy,
    "logo_phoenix": _logo_phoenix,
    "icon_battery": _icon_battery,
    "icon_jumper": _icon_jumper,
}
