"""AMI Aptio vendor skin — the original blue/gray Setup Utility look."""

from theme import (GRID_W, BLUE, BODY, WHITE, DISABLED, SHADOW,
                   HEADER_ROW, TAB_ROW, FRAME_TOP, FRAME_BOT, FOOTER_ROW,
                   DIVIDER_X, ITEM_X0, VALUE_X, HELP_X0, HELP_X1,
                   LEGEND_DIV_ROW, ITEM_Y0, ITEM_Y1, VISIBLE_ROWS,
                   TITLE, FOOTER, KEY_LEGEND)
import screen as sc
from renderer import word_wrap


def draw_setup(buf, model):
    """Full Aptio setup screen: bars, tabs, frame, items, help, legend."""
    buf.clear(BLUE, BODY)

    buf.fill(0, HEADER_ROW, GRID_W, 1, " ", WHITE, BLUE)
    buf.text_center(HEADER_ROW, TITLE, WHITE, BLUE)
    buf.fill(0, FOOTER_ROW, GRID_W, 1, " ", WHITE, BLUE)
    buf.text_center(FOOTER_ROW, FOOTER, WHITE, BLUE)

    buf.fill(0, TAB_ROW, GRID_W, 1, " ", WHITE, BLUE)
    x = 2
    for i, page in enumerate(model.pages):
        name = " %s " % page["title"]
        if i == model.page_idx:
            buf.text(x, TAB_ROW, name, BLUE, BODY)
        else:
            buf.text(x, TAB_ROW, name, WHITE, BLUE)
        x += len(name) + 2

    frame_h = FRAME_BOT - FRAME_TOP + 1
    buf.box(0, FRAME_TOP, GRID_W, frame_h, BLUE, BODY, fill=False)
    buf.vline(DIVIDER_X, FRAME_TOP, frame_h, BLUE, BODY,
              top=sc.TJ, bottom=sc.BJ)
    buf.hline(DIVIDER_X, LEGEND_DIV_ROW, GRID_W - DIVIDER_X, BLUE, BODY,
              left=sc.LJ, right=sc.RJ)

    _draw_items(buf, model)
    _draw_help_pane(buf, model)


def _draw_items(buf, model):
    level = model.level
    items = level.items
    rows = items[level.scroll:level.scroll + VISIBLE_ROWS]

    for r, item in enumerate(rows):
        y = ITEM_Y0 + r
        idx = level.scroll + r
        selected = idx == level.cursor and model.is_selectable(item)
        enabled = model.is_enabled(item)

        if selected:
            fg, bg = WHITE, BLUE
            buf.fill(1, y, DIVIDER_X - 1, 1, " ", fg, bg)
        else:
            fg = BLUE if enabled else DISABLED
            bg = BODY

        label = model.display_label(item)
        if item["type"] == "submenu":
            label = "► " + label
        buf.text(ITEM_X0, y, label[:DIVIDER_X - ITEM_X0 - 1], fg, bg)

        value = model.display_value(item)
        if value:
            vfg = fg if (selected or not enabled) else BLUE
            buf.text(VALUE_X, y, value[:DIVIDER_X - VALUE_X - 1], vfg, bg)

    if level.scroll > 0:
        buf.put(DIVIDER_X - 1, ITEM_Y0, "▲", BLUE, BODY)
    if level.scroll + VISIBLE_ROWS < len(items):
        buf.put(DIVIDER_X - 1, ITEM_Y1, "▼", BLUE, BODY)


def _draw_help_pane(buf, model):
    item = model.current_item()
    if item and item.get("help"):
        width = HELP_X1 - HELP_X0 + 1
        for i, line in enumerate(word_wrap(item["help"], width)):
            y = ITEM_Y0 + i
            if y >= LEGEND_DIV_ROW:
                break
            buf.text(HELP_X0, y, line, BLUE, BODY)

    for i, line in enumerate(KEY_LEGEND):
        buf.text(HELP_X0, LEGEND_DIV_ROW + 1 + i, line, BLUE, BODY)


def _popup_frame(buf, w, h, title):
    """Centered blue box with white border + shadow; returns (x, y)."""
    x = (GRID_W - w) // 2
    y = (FRAME_TOP + FRAME_BOT - h) // 2
    buf.shadow(x, y, w, h, SHADOW)
    buf.fill(x, y, w, h, " ", WHITE, BLUE)
    buf.box(x, y, w, h, WHITE, BLUE, fill=False)
    if title:
        buf.text(x + (w - len(title)) // 2, y + 1, title, WHITE, BLUE)
        buf.hline(x, y + 2, w, WHITE, BLUE, left=sc.LJ, right=sc.RJ)
    return x, y


def draw_option_popup(buf, item, sel, model=None):
    values = item["values"]
    label = model.display_label(item) if model else item.get("label", "")
    w = max(len(label), max(len(v) for v in values)) + 6
    w = min(max(w, 24), GRID_W - 8)
    h = len(values) + 4
    x, y = _popup_frame(buf, w, h, label)
    for i, v in enumerate(values):
        fg, bg = (BLUE, WHITE) if i == sel else (WHITE, BLUE)
        if i == sel:
            buf.fill(x + 1, y + 3 + i, w - 2, 1, " ", fg, bg)
        buf.text(x + 2, y + 3 + i, v[:w - 4], fg, bg)


def draw_dialog(buf, title, lines, buttons, sel):
    w = max([len(title)] + [len(l) for l in lines]) + 8
    w = max(w, sum(len(b) + 6 for b in buttons) + 4)
    w = min(max(w, 34), GRID_W - 8)
    h = len(lines) + 6
    x, y = _popup_frame(buf, w, h, title)
    for i, line in enumerate(lines):
        buf.text(x + (w - len(line)) // 2, y + 3 + i, line, WHITE, BLUE)
    total = sum(len(b) + 4 for b in buttons) + 2 * (len(buttons) - 1)
    bx = x + (w - total) // 2
    by = y + h - 2
    for i, b in enumerate(buttons):
        text = "[%s]" % b
        if i == sel:
            buf.text(bx, by, " " + text + " ", BLUE, WHITE)
        else:
            buf.text(bx + 1, by, text, WHITE, BLUE)
        bx += len(b) + 6


def draw_text_popup(buf, title, buffer, masked):
    w = max(len(title) + 6, 30)
    h = 5
    x, y = _popup_frame(buf, w, h, title)
    field_w = w - 6
    shown = ("*" * len(buffer)) if masked else buffer
    shown = shown[-field_w:]
    buf.fill(x + 3, y + 3, field_w, 1, " ", BLUE, WHITE)
    buf.text(x + 3, y + 3, shown, BLUE, WHITE)
    buf.put(x + 3 + min(len(shown), field_w - 1), y + 3, "_", BLUE, WHITE)


def draw_help_popup(buf):
    lines = KEY_LEGEND
    w = max(len(l) for l in lines) + 10
    h = len(lines) + 6
    x, y = _popup_frame(buf, w, h, "General Help")
    for i, line in enumerate(lines):
        buf.text(x + 3, y + 3 + i, line, WHITE, BLUE)
    buf.text(x + (w - 8) // 2, y + h - 2, "  [Ok]  ", BLUE, WHITE)


spec = {
    "id": "ami",
    "title": TITLE,
    "footer": FOOTER,
    "draw_setup": draw_setup,
    "draw_option_popup": draw_option_popup,
    "draw_dialog": draw_dialog,
    "draw_text_popup": draw_text_popup,
    "draw_help_popup": draw_help_popup,
    # POST and beep info: filled in by post_screen / audio later.
    # AMI POST: 1 long = OK, 1 long + 2 short = video error, etc.
    "beep_map": {
        "ok": [(900, 350)],
        "memory_fail": [(900, 150)] * 3,
        "video_fail": [(900, 350), (900, 150), (900, 150)],
    },
    "key_legend": KEY_LEGEND,
}
