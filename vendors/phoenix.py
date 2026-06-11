"""PhoenixBIOS vendor skin — the classic laptop-era Setup Utility.

Look: blue title bar reading "PhoenixBIOS Setup Utility", a tab row over
the shared pages, black-on-gray item list on the left, a boxed "Item
Specific Help" panel on the right, and the famous two-row key legend at
the bottom. POST counts RAM in kilobytes and beeps in grouped patterns
(e.g. 1-3-3-1 for memory failure).
"""

import screen as sc
from renderer import word_wrap
from theme import GRID_W, GRID_H, BLACK

# Phoenix palette: gray body, navy chrome, white-on-blue selection.
PH_BG       = (192, 192, 192)    # body background
PH_FG       = (0, 0, 128)        # navy item text
PH_BAR_BG   = (0, 0, 128)        # title bar
PH_BAR_FG   = (255, 255, 255)
PH_SEL_FG   = (255, 255, 255)
PH_SEL_BG   = (0, 0, 128)
PH_DISABLED = (128, 128, 128)
PH_HELP_TI  = (0, 0, 128)

TITLE = "PhoenixBIOS Setup Utility"

# Drawing-only page title shortenings (the shared ids stay untouched).
PAGE_TITLE_OVERRIDES = {
    "Ai Tweaker": "Performance",
    "Save & Exit": "Exit",
}

TAB_ROW = 1
FRAME_TOP = 2
LEGEND_TOP = GRID_H - 3          # two legend rows + divider above them
FRAME_BOT = LEGEND_TOP - 1
HELP_X = 66                      # left edge of the Item Specific Help box
ITEM_X0 = 2
VALUE_X = 36
VISIBLE = FRAME_BOT - FRAME_TOP - 1

LEGEND = [
    ("F1", "Help"), ("↑↓", "Select Item"), ("-/+", "Change Values"),
    ("F9", "Setup Defaults"),
    ("Esc", "Exit"), ("←→", "Select Menu"), ("Enter", "Select ► Sub-Menu"),
    ("F10", "Save and Exit"),
]

KEY_LEGEND = [
    "F1 Help    ↑↓ Select Item",
    "Esc Exit   ←→ Select Menu",
    "-/+ Change Values   F9 Setup Defaults",
    "Enter Select Sub-Menu   F10 Save and Exit",
]


def _page_title(page):
    return PAGE_TITLE_OVERRIDES.get(page["title"], page["title"])


def draw_setup(buf, model):
    buf.clear(PH_FG, PH_BG)

    # Title bar
    buf.fill(0, 0, GRID_W, 1, " ", PH_BAR_FG, PH_BAR_BG)
    buf.text_center(0, TITLE, PH_BAR_FG, PH_BAR_BG)

    # Tab row
    buf.fill(0, TAB_ROW, GRID_W, 1, " ", PH_BAR_FG, PH_BAR_BG)
    x = 4
    for i, page in enumerate(model.pages):
        name = "  %s  " % _page_title(page)
        if i == model.page_idx:
            buf.text(x, TAB_ROW, name, PH_FG, PH_BG)
        else:
            buf.text(x, TAB_ROW, name, PH_BAR_FG, PH_BAR_BG)
        x += len(name)

    # Body frame with the help panel divider
    frame_h = FRAME_BOT - FRAME_TOP + 1
    buf.box(0, FRAME_TOP, GRID_W, frame_h, BLACK, PH_BG, fill=False)
    buf.vline(HELP_X, FRAME_TOP, frame_h, BLACK, PH_BG,
              top=sc.TJ, bottom=sc.BJ)
    help_title = " Item Specific Help "
    buf.text(HELP_X + (GRID_W - HELP_X - len(help_title)) // 2,
             FRAME_TOP, help_title, PH_HELP_TI, PH_BG)

    _draw_items(buf, model)
    _draw_help(buf, model)
    _draw_legend(buf)


def _draw_items(buf, model):
    level = model.level
    items = level.items
    rows = items[level.scroll:level.scroll + VISIBLE]
    for r, item in enumerate(rows):
        y = FRAME_TOP + 1 + r
        idx = level.scroll + r
        selected = idx == level.cursor and model.is_selectable(item)
        enabled = model.is_enabled(item)

        if selected:
            fg, bg = PH_SEL_FG, PH_SEL_BG
            buf.fill(1, y, HELP_X - 1, 1, " ", fg, bg)
        else:
            fg = (BLACK if item["type"] == "info" else PH_FG) \
                if enabled else PH_DISABLED
            bg = PH_BG

        label = model.display_label(item)
        if item["type"] == "submenu":
            label = "► " + label
        buf.text(ITEM_X0, y, label[:VALUE_X - ITEM_X0 - 1], fg, bg)

        value = model.display_value(item)
        if value:
            buf.text(VALUE_X, y, value[:HELP_X - VALUE_X - 1], fg, bg)

    if level.scroll > 0:
        buf.put(HELP_X - 1, FRAME_TOP + 1, "▲", BLACK, PH_BG)
    if level.scroll + VISIBLE < len(items):
        buf.put(HELP_X - 1, FRAME_BOT - 1, "▼", BLACK, PH_BG)


def _draw_help(buf, model):
    item = model.current_item()
    if not (item and item.get("help")):
        return
    width = GRID_W - HELP_X - 4
    for i, line in enumerate(word_wrap(item["help"], width)):
        y = FRAME_TOP + 2 + i
        if y >= FRAME_BOT:
            break
        buf.text(HELP_X + 2, y, line, BLACK, PH_BG)


def _draw_legend(buf):
    buf.fill(0, LEGEND_TOP, GRID_W, 3, " ", PH_BAR_FG, PH_BAR_BG)
    half = len(LEGEND) // 2
    for row in range(2):
        x = 2
        for keycap, desc in LEGEND[row * half:(row + 1) * half]:
            buf.text(x, LEGEND_TOP + row + 1, keycap, PH_BAR_FG, PH_BAR_BG)
            buf.text(x + len(keycap) + 1, LEGEND_TOP + row + 1, desc,
                     (170, 170, 170), PH_BAR_BG)
            x += len(keycap) + len(desc) + 6


# --- Popups --------------------------------------------------------------

def _popup_frame(buf, w, h, title):
    x = (GRID_W - w) // 2
    y = (FRAME_TOP + FRAME_BOT - h) // 2
    buf.fill(x, y, w, h, " ", PH_FG, PH_BG)
    buf.box(x, y, w, h, BLACK, PH_BG, fill=False)
    if title:
        buf.text(x + (w - len(title)) // 2, y + 1, title, BLACK, PH_BG)
        buf.hline(x, y + 2, w, BLACK, PH_BG, left=sc.LJ, right=sc.RJ)
    return x, y


def draw_option_popup(buf, item, sel, model=None):
    values = item["values"]
    label = model.display_label(item) if model else item.get("label", "")
    w = max(len(label), max(len(v) for v in values)) + 6
    w = min(max(w, 24), GRID_W - 8)
    h = len(values) + 4
    x, y = _popup_frame(buf, w, h, label)
    for i, v in enumerate(values):
        if i == sel:
            buf.fill(x + 1, y + 3 + i, w - 2, 1, " ", PH_SEL_FG, PH_SEL_BG)
            buf.text(x + 2, y + 3 + i, v[:w - 4], PH_SEL_FG, PH_SEL_BG)
        else:
            buf.text(x + 2, y + 3 + i, v[:w - 4], PH_FG, PH_BG)


def draw_dialog(buf, title, lines, buttons, sel):
    w = max([len(title)] + [len(l) for l in lines]) + 8
    w = max(w, sum(len(b) + 6 for b in buttons) + 4)
    w = min(max(w, 34), GRID_W - 8)
    h = len(lines) + 6
    x, y = _popup_frame(buf, w, h, title)
    for i, line in enumerate(lines):
        buf.text(x + (w - len(line)) // 2, y + 3 + i, line, PH_FG, PH_BG)
    total = sum(len(b) + 4 for b in buttons) + 2 * (len(buttons) - 1)
    bx = x + (w - total) // 2
    by = y + h - 2
    for i, b in enumerate(buttons):
        text = "[%s]" % b
        if i == sel:
            buf.text(bx, by, " " + text + " ", PH_SEL_FG, PH_SEL_BG)
        else:
            buf.text(bx + 1, by, text, PH_FG, PH_BG)
        bx += len(b) + 6


def draw_text_popup(buf, title, buffer, masked):
    w = max(len(title) + 6, 30)
    h = 5
    x, y = _popup_frame(buf, w, h, title)
    field_w = w - 6
    shown = ("*" * len(buffer)) if masked else buffer
    shown = shown[-field_w:]
    buf.fill(x + 3, y + 3, field_w, 1, " ", PH_SEL_FG, PH_SEL_BG)
    buf.text(x + 3, y + 3, shown, PH_SEL_FG, PH_SEL_BG)
    buf.put(x + 3 + min(len(shown), field_w - 1), y + 3, "_",
            PH_SEL_FG, PH_SEL_BG)


def draw_help_popup(buf):
    lines = KEY_LEGEND
    w = max(len(l) for l in lines) + 10
    h = len(lines) + 6
    x, y = _popup_frame(buf, w, h, "General Help")
    for i, line in enumerate(lines):
        buf.text(x + 3, y + 3 + i, line, PH_FG, PH_BG)
    buf.text(x + (w - 8) // 2, y + h - 2, "  [Ok]  ", PH_SEL_FG, PH_SEL_BG)


# --- POST data -----------------------------------------------------------

POST_BG = BLACK
POST_FG = (192, 192, 192)
POST_HI = (255, 255, 255)
POST_LINES = [
    (200,  "PhoenixBIOS 4.0 Release 6.0"),
    (350,  "Copyright 1985-2003 Phoenix Technologies Ltd."),
    (500,  "All Rights Reserved"),
    (700,  ""),
    (900,  "CPU = Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz"),
    (1100, "640K System RAM Passed"),
    (2700, "ATAPI CD-ROM: TSSTcorp CDDVDW SN-208"),
    (2950, "Mouse initialized"),
    (3200, "Fixed Disk 0: Samsung SSD 860"),
]
# Era-correct: extended RAM counted in K (1024K steps, exact total).
POST_MEMCOUNT = {"t0": 1100, "dur": 1300, "after": 6,
                 "total": 523264, "step": 1024,
                 "fmt": "%dK Extended RAM Passed", "ok_suffix": ""}

_B = 750  # Phoenix beep base frequency
_PAUSE = (0, 260)


def _groups(*counts):
    """Phoenix beep codes are groups of short beeps: 1-3-3-1 etc."""
    pattern = []
    for i, c in enumerate(counts):
        if i:
            pattern.append(_PAUSE)
        pattern.extend([(_B, 160)] * c)
    return pattern


spec = {
    "id": "phoenix",
    "title": TITLE,
    "footer": "Phoenix Technologies Ltd.",
    "home_items_fn": None,
    "draw_setup": draw_setup,
    "draw_option_popup": draw_option_popup,
    "draw_dialog": draw_dialog,
    "draw_text_popup": draw_text_popup,
    "draw_help_popup": draw_help_popup,
    "post_lines": POST_LINES,
    "post_prompt": "Press <F2> to enter SETUP",
    "post_prompt_keys": "f2",
    "post_palette": (POST_BG, POST_FG, POST_HI),
    "post_memcount": POST_MEMCOUNT,
    "post_show_code": False,
    # Phoenix beep codes: grouped patterns (memory failure = 1-3-3-1,
    # video failure = 1-2-2-3). POST OK is a single short beep.
    "beep_map": {
        "ok": [(_B, 150)],
        "memory_fail": _groups(1, 3, 3, 1),
        "video_fail": _groups(1, 2, 2, 3),
    },
    "key_legend": KEY_LEGEND,
}
