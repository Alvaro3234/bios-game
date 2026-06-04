"""Award/Phoenix BIOS vendor skin — early-2000s cyan/yellow look.

Layout: single vertical list per page with a double-line frame, no tab bar.
Pages cycle with LEFT/RIGHT but the active page is drawn as a header strip.
"""

from theme import (GRID_W, GRID_H, FRAME_TOP, FRAME_BOT, ITEM_X0,
                   VISIBLE_ROWS, BLACK)
import screen as sc

# Award palette (DOS classic): blue background, cyan body box, yellow titles.
AW_BG       = (0, 0, 168)        # screen background
AW_BOX_BG   = (0, 168, 168)      # cyan body
AW_BOX_FG   = (0, 0, 0)
AW_BOX_HI   = (255, 255, 255)
AW_TITLE    = (255, 255, 85)     # bright yellow
AW_TEXT     = (255, 255, 255)
AW_VAL      = (85, 255, 255)
AW_SEL_FG   = (0, 0, 0)
AW_SEL_BG   = (255, 255, 255)
AW_DISABLED = (85, 85, 85)

TITLE  = "ROM PCI/ISA BIOS (2A69KQ1C)"
SUBTITLE = "CMOS SETUP UTILITY"
COPYRIGHT = "AWARD SOFTWARE, INC."
HINT_LINE = "↑↓→← : Select Item   F1 : Help   (Shift)F2 : Color   F10 : Save"

# CP437 double-line frame chars
DH, DV = "═", "║"
DTL, DTR, DBL, DBR = "╔", "╗", "╚", "╝"


def draw_setup(buf, model):
    buf.clear(AW_TEXT, AW_BG)

    # Title block (top 3 rows): yellow centered headers
    buf.text_center(0, TITLE, AW_TITLE, AW_BG)
    buf.text_center(1, SUBTITLE, AW_TITLE, AW_BG)
    buf.text_center(2, COPYRIGHT, AW_TEXT, AW_BG)

    # Body: a single cyan box that holds the current page items
    box_x, box_y = 6, 4
    box_w, box_h = GRID_W - 12, GRID_H - 8
    buf.fill(box_x, box_y, box_w, box_h, " ", AW_BOX_FG, AW_BOX_BG)
    # Double-line frame
    buf.hline(box_x, box_y, box_w, AW_BOX_FG, AW_BOX_BG,
              left=DTL, mid=DH, right=DTR)
    buf.hline(box_x, box_y + box_h - 1, box_w, AW_BOX_FG, AW_BOX_BG,
              left=DBL, mid=DH, right=DBR)
    for yy in range(box_y + 1, box_y + box_h - 1):
        buf.put(box_x, yy, DV, AW_BOX_FG, AW_BOX_BG)
        buf.put(box_x + box_w - 1, yy, DV, AW_BOX_FG, AW_BOX_BG)

    # Page title at the top of the box, in yellow
    page = model.pages[model.page_idx]
    page_label = " %s " % page["title"]
    buf.text(box_x + 2, box_y, page_label, AW_TITLE, AW_BG)

    # Page count indicator
    paging = " Page %d/%d " % (model.page_idx + 1, len(model.pages))
    buf.text(box_x + box_w - len(paging) - 2, box_y, paging,
             AW_TITLE, AW_BG)

    # Items
    level = model.level
    items = level.items
    inner_x = box_x + 2
    inner_y = box_y + 2
    value_x = box_x + box_w // 2 + 4
    rows = items[level.scroll:level.scroll + min(VISIBLE_ROWS, box_h - 5)]

    for r, item in enumerate(rows):
        y = inner_y + r
        idx = level.scroll + r
        selected = idx == level.cursor and model.is_selectable(item)
        enabled = model.is_enabled(item)

        if selected:
            buf.fill(box_x + 1, y, box_w - 2, 1, " ", AW_SEL_FG, AW_SEL_BG)
            fg, bg = AW_SEL_FG, AW_SEL_BG
        else:
            fg = AW_BOX_FG if enabled else AW_DISABLED
            bg = AW_BOX_BG

        label = model.display_label(item)
        if item["type"] == "submenu":
            label = "► " + label
        buf.text(inner_x, y, label[:value_x - inner_x - 1], fg, bg)

        value = model.display_value(item)
        if value:
            vfg = fg if (selected or not enabled) else AW_VAL
            buf.text(value_x, y, value[:box_x + box_w - value_x - 2], vfg, bg)

    # Footer with key hints
    buf.text_center(GRID_H - 2, HINT_LINE, AW_TEXT, AW_BG)
    item = model.current_item()
    if item and item.get("help"):
        help_text = "F1->Help: " + item["help"][:GRID_W - 14]
        buf.text_center(GRID_H - 3, help_text, AW_TITLE, AW_BG)


def _award_popup(buf, w, h, title):
    x = (GRID_W - w) // 2
    y = (FRAME_TOP + FRAME_BOT - h) // 2
    buf.fill(x, y, w, h, " ", AW_BOX_FG, AW_BOX_HI)
    buf.hline(x, y, w, AW_BOX_FG, AW_BOX_HI, left=DTL, mid=DH, right=DTR)
    buf.hline(x, y + h - 1, w, AW_BOX_FG, AW_BOX_HI,
              left=DBL, mid=DH, right=DBR)
    for yy in range(y + 1, y + h - 1):
        buf.put(x, yy, DV, AW_BOX_FG, AW_BOX_HI)
        buf.put(x + w - 1, yy, DV, AW_BOX_FG, AW_BOX_HI)
    if title:
        buf.text(x + (w - len(title)) // 2, y, " %s " % title,
                 AW_TITLE, AW_BG)
    return x, y


def draw_option_popup(buf, item, sel, model=None):
    values = item["values"]
    label = model.display_label(item) if model else item.get("label", "")
    w = max(len(label), max(len(v) for v in values)) + 6
    w = min(max(w, 24), GRID_W - 8)
    h = len(values) + 4
    x, y = _award_popup(buf, w, h, label)
    for i, v in enumerate(values):
        if i == sel:
            buf.fill(x + 1, y + 2 + i, w - 2, 1, " ",
                     AW_SEL_FG, AW_SEL_BG)
            buf.text(x + 3, y + 2 + i, v[:w - 4], AW_SEL_FG, AW_SEL_BG)
        else:
            buf.text(x + 3, y + 2 + i, v[:w - 4], AW_BOX_FG, AW_BOX_HI)


def draw_dialog(buf, title, lines, buttons, sel):
    w = max([len(title)] + [len(l) for l in lines]) + 8
    w = max(w, sum(len(b) + 6 for b in buttons) + 4)
    w = min(max(w, 34), GRID_W - 8)
    h = len(lines) + 6
    x, y = _award_popup(buf, w, h, title)
    for i, line in enumerate(lines):
        buf.text(x + (w - len(line)) // 2, y + 2 + i, line,
                 AW_BOX_FG, AW_BOX_HI)
    total = sum(len(b) + 4 for b in buttons) + 2 * (len(buttons) - 1)
    bx = x + (w - total) // 2
    by = y + h - 2
    for i, b in enumerate(buttons):
        text = "[%s]" % b
        if i == sel:
            buf.text(bx, by, " " + text + " ", AW_SEL_FG, AW_SEL_BG)
        else:
            buf.text(bx + 1, by, text, AW_BOX_FG, AW_BOX_HI)
        bx += len(b) + 6


def draw_text_popup(buf, title, buffer, masked):
    w = max(len(title) + 6, 30)
    h = 5
    x, y = _award_popup(buf, w, h, title)
    field_w = w - 6
    shown = ("*" * len(buffer)) if masked else buffer
    shown = shown[-field_w:]
    buf.fill(x + 3, y + 2, field_w, 1, " ", AW_BOX_HI, AW_BOX_FG)
    buf.text(x + 3, y + 2, shown, AW_BOX_HI, AW_BOX_FG)
    buf.put(x + 3 + min(len(shown), field_w - 1), y + 2, "_",
            AW_BOX_HI, AW_BOX_FG)


def draw_help_popup(buf):
    lines = [
        "↑/↓/←/→ : Select Item",
        "Enter   : Select",
        "PgUp/+/-: Change Value",
        "F1      : Help",
        "F10     : Save & Exit",
        "ESC     : Quit",
    ]
    w = max(len(l) for l in lines) + 10
    h = len(lines) + 4
    x, y = _award_popup(buf, w, h, "Help")
    for i, line in enumerate(lines):
        buf.text(x + 3, y + 2 + i, line, AW_BOX_FG, AW_BOX_HI)


# --- POST data ---------------------------------------------------------

POST_BG = BLACK
POST_FG = (192, 192, 192)
POST_HI = (255, 255, 255)
POST_LINES = [
    (200,  "Award Modular BIOS v6.00PG, An Energy Star Ally"),
    (350,  "Copyright (C) 1984-2000, Award Software, Inc."),
    (600,  ""),
    (700,  "Main Processor : AMD Athlon(tm) XP 3000+"),
    (900,  "Memory Testing :"),
    (2200, "Award Plug and Play BIOS Extension v1.0A"),
    (2400, "Copyright (C) 1999, Award Software, Inc."),
    (2700, "Initialize Plug and Play Cards..."),
    (3000, "PNP Init Completed"),
    (3300, ""),
    (3400, "Detecting IDE drives ..."),
]

POST_PROMPT = "Press DEL to enter SETUP"
POST_PROMPT_KEYS = "del"


spec = {
    "id": "award",
    "title": TITLE,
    "footer": HINT_LINE,
    "draw_setup": draw_setup,
    "draw_option_popup": draw_option_popup,
    "draw_dialog": draw_dialog,
    "draw_text_popup": draw_text_popup,
    "draw_help_popup": draw_help_popup,
    "post_lines": POST_LINES,
    "post_prompt": POST_PROMPT,
    "post_prompt_keys": POST_PROMPT_KEYS,
    "post_palette": (POST_BG, POST_FG, POST_HI),
    # Award POST: 1 short = OK; 2 short = generic error; continuous = power
    "beep_map": {
        "ok": [(700, 120)],
        "memory_fail": [(700, 120), (700, 120)],
        "video_fail": [(700, 120), (700, 120), (700, 120)],
    },
    "key_legend": [HINT_LINE],
}
