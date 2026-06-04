"""POST / boot splash: timed text reveal, memory count, blinking prompt."""

import pygame

from theme import GRID_W, GRID_H, POST_BG, POST_FG, POST_HI

MEM_TOTAL = 16384
MEM_T0, MEM_DUR = 1000, 1200    # memory count window (ms after reset)

# (time_ms, text) — revealed sequentially
_LINES = [
    (300,  "AMIBIOS(C)2019 American Megatrends, Inc."),
    (300,  "BIOS Date: 04/12/2019 14:33:08 Ver: Z390M 2.60"),
    (700,  "CPU : Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz"),
    (700,  " Speed : 3.60 GHz"),
    (2400, "USB Devices total: 1 Drive, 1 Keyboard, 1 Mouse, 2 Hubs"),
    (2800, "Detected ATA/ATAPI Devices..."),
    (3000, "  SATA Port 0 : Samsung SSD 860  500GB"),
    (3200, "  SATA Port 1 : ST2000DM008-2FR102"),
]
PROMPT_T = 3600


class PostScreen:
    def __init__(self):
        self.t0 = 0

    def reset(self, now):
        self.t0 = now

    def handle_key(self, key):
        """Returns 'setup' when the user requests Setup."""
        if key in (pygame.K_DELETE, pygame.K_F2):
            return "setup"
        return None

    def draw(self, buf, now):
        t = now - self.t0
        buf.clear(POST_FG, POST_BG)

        y = 1
        for reveal, text in _LINES[:4]:
            if t >= reveal:
                buf.text(1, y, text, POST_FG, POST_BG)
            y += 1

        # Memory count
        if t >= MEM_T0:
            frac = min(1.0, (t - MEM_T0) / MEM_DUR)
            mb = int(MEM_TOTAL * frac) // 64 * 64
            line = "Memory Testing : %d MB" % mb
            if frac >= 1.0:
                line += " OK"
            buf.text(1, y + 1, line, POST_FG, POST_BG)

        y += 3
        for reveal, text in _LINES[4:]:
            if t >= reveal:
                buf.text(1, y, text, POST_FG, POST_BG)
            y += 1

        # Blinking setup prompt
        if t >= PROMPT_T and (t // 530) % 2 == 0:
            buf.text(1, y + 1, "Press DEL or F2 to enter UEFI BIOS Setup",
                     POST_HI, POST_BG)

        # POST code (bottom-right, like a real board)
        code = "A2" if t >= PROMPT_T else ("99" if t >= MEM_T0 else "4F")
        buf.text(GRID_W - 3, GRID_H - 1, code, POST_HI, POST_BG)
