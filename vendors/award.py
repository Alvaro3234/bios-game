"""Award BIOS vendor skin — early-2000s blue/cyan/red CMOS Setup look.

Layout: an authentic two-column home menu of categories (STANDARD CMOS
SETUP, ADVANCED BIOS FEATURES, ...) built from the shared menu_data item
dicts via `build_home_items()`. Enter opens a category (a submenu level
in MenuModel terms); Esc returns to the home grid.
"""

import menu_data as md
from menu_data import header, info, blank
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
AW_SEL_FG   = (255, 255, 255)
AW_SEL_BG   = (168, 0, 0)        # the classic red selection bar
AW_DISABLED = (85, 85, 85)

TITLE  = "ROM PCI/ISA BIOS (2A69KQ1C)"
SUBTITLE = "CMOS SETUP UTILITY"
COPYRIGHT = "AWARD SOFTWARE, INC."
HINT_LINE = "↑↓→← : Select Item   F1 : Help   (Shift)F2 : Color   F10 : Save"
HOME_HINT = "Esc : Quit   ↑↓→← : Select Item   F10 : Save & Exit Setup"

# CP437 double-line frame chars
DH, DV = "═", "║"
DTL, DTR, DBL, DBR = "╔", "╗", "╚", "╝"


# --- Home menu (category grid) ------------------------------------------

def _settings_of(*sections):
    """Flatten the persistable/submenu items of the given menu_data
    sections, dropping the UEFI-flavored info chrome."""
    out = []
    for sec in sections:
        for it in sec["items"]:
            if it.get("id") or it["type"] in ("submenu", "action"):
                out.append(it)
    return out


def build_home_items():
    """Award main-menu categories referencing the shared item dicts."""
    main = md.MAIN_PAGE["items"]
    dt = [it for it in main if it.get("id") in ("sys_date", "sys_time")]
    std_cmos = ([header("Standard CMOS Setup"), blank()] + dt + [
        blank(),
        info("Primary Master", "Samsung SSD 860 (500.1GB)"),
        info("Primary Slave", "ST2000DM008-2FR1 (2000.3GB)"),
        info("Secondary Master", "None"),
        info("Secondary Slave", "None"),
        blank(),
        info("Base Memory", "640K"),
        info("Extended Memory", "523264K"),
        info("Total Memory", "524288K"),
    ])
    adv_bios = ([header("Advanced BIOS Features"), blank()]
                + _settings_of(md.CPU_CONFIG) + [blank()]
                + [it for it in md.BOOT_PAGE["items"]
                   if it.get("id") in ("numlock", "quiet_boot", "fast_boot",
                                       "boot1", "boot2", "boot3")])
    chipset = ([header("Chipset Features Setup"), blank()]
               + _settings_of(md.SA_CONFIG))
    pnp_pci = ([header("PnP/PCI Configurations"), blank()]
               + _settings_of(md.NETWORK_STACK)
               + [it for it in md.PCH_CONFIG["items"]
                  if it.get("id") == "pcie_clock_gating"])
    integrated = (md.SATA_CONFIG["items"] + [blank()]
                  + md.USB_CONFIG["items"] + [blank()]
                  + md.PCH_CONFIG["items"])
    return [
        {"type": "submenu", "label": "STANDARD CMOS SETUP",
         "items": std_cmos,
         "help": "Time, Date, Hard Disk Type..."},
        {"type": "submenu", "label": "ADVANCED BIOS FEATURES",
         "items": adv_bios,
         "help": "Boot sequence, CPU features..."},
        {"type": "submenu", "label": "CHIPSET FEATURES SETUP",
         "items": chipset,
         "help": "North bridge, graphics, DRAM info..."},
        {"type": "submenu", "label": "POWER MANAGEMENT SETUP",
         "items": md.APM_CONFIG["items"],
         "help": "AC power loss, RTC alarm wake-up..."},
        {"type": "submenu", "label": "PNP/PCI CONFIGURATIONS",
         "items": pnp_pci,
         "help": "Network boot ROM, PCI resources..."},
        {"type": "submenu", "label": "INTEGRATED PERIPHERALS",
         "items": integrated,
         "help": "IDE/SATA, USB, onboard audio and LAN..."},
        {"type": "submenu", "label": "PC HEALTH STATUS",
         "items": md.MONITOR_PAGE["items"],
         "help": "Temperatures, fan speeds, voltages..."},
        {"type": "submenu", "label": "FREQUENCY/VOLTAGE CONTROL",
         "items": md.OC_PAGE["items"],
         "help": "CPU ratio, DRAM frequency and voltage..."},
        {"type": "action", "action": "load_defaults",
         "label": "LOAD SETUP DEFAULTS",
         "help": "Load the factory default values."},
        {"type": "password", "id": "admin_pwd",
         "label": "SET SUPERVISOR PASSWORD",
         "help": "Change, set, or disable the supervisor password."},
        {"type": "password", "id": "user_pwd",
         "label": "SET USER PASSWORD",
         "help": "Change, set, or disable the user password."},
        {"type": "action", "action": "ide_autodetect",
         "label": "IDE HDD AUTO DETECTION",
         "help": "Auto-detect the IDE hard disk parameters."},
        {"type": "action", "action": "save_exit",
         "label": "SAVE & EXIT SETUP",
         "help": "Save CMOS values and exit Setup."},
        {"type": "action", "action": "discard_exit",
         "label": "EXIT WITHOUT SAVING",
         "help": "Abandon all CMOS changes and exit Setup."},
    ]


def draw_setup(buf, model):
    if model.home_items is not None and not model.in_submenu:
        _draw_home(buf, model)
    else:
        _draw_category(buf, model)


def _draw_home(buf, model):
    buf.clear(AW_TEXT, AW_BG)
    buf.text_center(0, TITLE, AW_TITLE, AW_BG)
    buf.text_center(1, SUBTITLE, AW_TITLE, AW_BG)
    buf.text_center(2, COPYRIGHT, AW_TEXT, AW_BG)

    box_x, box_y = 8, 4
    box_w, box_h = GRID_W - 16, GRID_H - 9
    _frame(buf, box_x, box_y, box_w, box_h, AW_TEXT, AW_BG)

    items = model.level.items
    half = (len(items) + 1) // 2
    col_w = (box_w - 4) // 2
    for i, item in enumerate(items):
        col = 0 if i < half else 1
        row = i if i < half else i - half
        x = box_x + 2 + col * (col_w + 1)
        y = box_y + 2 + row * 2
        selected = i == model.level.cursor
        fg, bg = (AW_SEL_FG, AW_SEL_BG) if selected else (AW_TEXT, AW_BG)
        if selected:
            buf.fill(x - 1, y, col_w, 1, " ", fg, bg)
        buf.text(x, y, item["label"][:col_w - 2], fg, bg)

    # Divider between columns
    mid_x = box_x + 2 + col_w
    for yy in range(box_y + 1, box_y + box_h - 1):
        buf.put(mid_x, yy, DV, AW_TEXT, AW_BG)

    buf.text_center(GRID_H - 3, HOME_HINT, AW_TEXT, AW_BG)
    item = model.current_item()
    if item and item.get("help"):
        buf.text_center(GRID_H - 2, item["help"][:GRID_W - 4],
                        AW_TITLE, AW_BG)


def _frame(buf, x, y, w, h, fg, bg):
    buf.hline(x, y, w, fg, bg, left=DTL, mid=DH, right=DTR)
    buf.hline(x, y + h - 1, w, fg, bg, left=DBL, mid=DH, right=DBR)
    for yy in range(y + 1, y + h - 1):
        buf.put(x, yy, DV, fg, bg)
        buf.put(x + w - 1, yy, DV, fg, bg)


def _draw_category(buf, model):
    buf.clear(AW_TEXT, AW_BG)

    # Title block (top 3 rows): yellow centered headers
    buf.text_center(0, TITLE, AW_TITLE, AW_BG)
    buf.text_center(1, SUBTITLE, AW_TITLE, AW_BG)
    buf.text_center(2, COPYRIGHT, AW_TEXT, AW_BG)

    # Body: a single cyan box that holds the current level's items
    box_x, box_y = 6, 4
    box_w, box_h = GRID_W - 12, GRID_H - 8
    buf.fill(box_x, box_y, box_w, box_h, " ", AW_BOX_FG, AW_BOX_BG)
    _frame(buf, box_x, box_y, box_w, box_h, AW_BOX_FG, AW_BOX_BG)

    # Level title at the top of the box, in yellow
    title = (model.level.title if model.home_items is not None
             else model.pages[model.page_idx]["title"])
    buf.text(box_x + 2, box_y, " %s " % title, AW_TITLE, AW_BG)

    if model.home_items is None:
        # Legacy paged mode (freeplay/screenshots without a home grid)
        paging = " Page %d/%d " % (model.page_idx + 1, len(model.pages))
        buf.text(box_x + box_w - len(paging) - 2, box_y, paging,
                 AW_TITLE, AW_BG)
    else:
        esc = " Esc : Back "
        buf.text(box_x + box_w - len(esc) - 2, box_y, esc, AW_TITLE, AW_BG)

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
    (2200, "Award Plug and Play BIOS Extension v1.0A"),
    (2400, "Copyright (C) 1999, Award Software, Inc."),
    (2700, "Initialize Plug and Play Cards..."),
    (3000, "PNP Init Completed"),
    (3300, ""),
    (3400, "Detecting IDE drives ..."),
]
# Era-correct kilobyte count: 512 MB tested in 4 MB increments.
POST_MEMCOUNT = {"t0": 900, "dur": 1300, "after": 4,
                 "total": 524288, "step": 4096,
                 "fmt": "Memory Testing :  %dK", "ok_suffix": " OK"}

POST_PROMPT = "Press DEL to enter SETUP"
POST_PROMPT_KEYS = "del"


spec = {
    "id": "award",
    "title": TITLE,
    "footer": HINT_LINE,
    "home_items_fn": build_home_items,
    "draw_setup": draw_setup,
    "draw_option_popup": draw_option_popup,
    "draw_dialog": draw_dialog,
    "draw_text_popup": draw_text_popup,
    "draw_help_popup": draw_help_popup,
    "post_lines": POST_LINES,
    "post_prompt": POST_PROMPT,
    "post_prompt_keys": POST_PROMPT_KEYS,
    "post_palette": (POST_BG, POST_FG, POST_HI),
    "post_memcount": POST_MEMCOUNT,
    "post_show_code": False,    # no on-screen debug code in the Award era
    # "An Energy Star Ally": the era-defining emblem sat top-right.
    "post_logo": {"key": "logo_energy", "t": 200},
    # Award POST: 1 short = OK; 1 long + 2 short = video error;
    # continuous beeping = memory error.
    "beep_map": {
        "ok": [(700, 120)],
        "memory_fail": [(700, 250)] * 5,
        "video_fail": [(700, 400), (700, 150), (700, 150)],
    },
    "key_legend": [HINT_LINE],
}
