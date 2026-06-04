"""Aptio TSE theme: grid dimensions, palette, layout metrics.

Single tuning point for visual accuracy. Colors derived from the
classic AMI Aptio Setup Utility (blue/gray TSE theme).
"""

# Character grid (cells) and cell size in pixels (8x16 VGA glyphs)
GRID_W, GRID_H = 100, 31
CELL_W, CELL_H = 8, 16

# Native pixel size of the rendered text screen
NATIVE_W = GRID_W * CELL_W   # 800
NATIVE_H = GRID_H * CELL_H   # 496

# ---------------------------------------------------------------- palette
BLUE = (0, 0, 168)         # Aptio signature blue (bars, text, borders)
BODY = (198, 198, 198)     # light gray body background
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DISABLED = (128, 128, 128)  # grayed-out items
SHADOW = (64, 64, 64)       # popup drop shadow

# POST screen
POST_BG = (0, 0, 0)
POST_FG = (192, 192, 192)
POST_HI = (255, 255, 255)

# ---------------------------------------------------------------- layout
HEADER_ROW = 0          # blue bar: "Aptio Setup Utility - Copyright ..."
TAB_ROW = 1             # blue bar: Main  Advanced  Chipset ...
FRAME_TOP = 2           # top border row of the body frame
FRAME_BOT = GRID_H - 2  # bottom border row of the body frame (29)
FOOTER_ROW = GRID_H - 1 # blue bar: "Version ... Copyright ..."

DIVIDER_X = 68          # vertical line between item pane and help pane
ITEM_X0 = 2             # first column of item labels
ITEM_X1 = DIVIDER_X - 1 # last usable column of the item pane
VALUE_X = 38            # column where values start
HELP_X0 = DIVIDER_X + 2 # first column of help text
HELP_X1 = GRID_W - 2    # last usable column of help text
LEGEND_DIV_ROW = FRAME_BOT - 10  # horizontal divider above the key legend

ITEM_Y0 = FRAME_TOP + 1          # first item row (3)
ITEM_Y1 = FRAME_BOT - 1          # last item row (28)
VISIBLE_ROWS = ITEM_Y1 - ITEM_Y0 + 1

# ---------------------------------------------------------------- strings
TITLE = "Aptio Setup Utility - Copyright (C) 2019 American Megatrends, Inc."
FOOTER = "Version 2.20.1271. Copyright (C) 2019 American Megatrends, Inc."

KEY_LEGEND = [
    "→←: Select Screen",
    "↑↓: Select Item",
    "Enter: Select",
    "+/-: Change Opt.",
    "F1: General Help",
    "F2: Previous Values",
    "F9: Optimized Defaults",
    "F10: Save & Exit",
    "ESC: Exit",
]
