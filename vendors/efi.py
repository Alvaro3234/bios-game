"""EFI Shell vendor skin — text terminal: prompt + scrollback, no chrome.

This skin uses a dedicated `SETUP_SHELL` app state with a `ShellSession`
backing it. The drawing function reads scrollback + current input buffer
and renders them in a green-on-black terminal aesthetic.
"""

from theme import GRID_W, GRID_H, BLACK

# Classic EFI Shell colors: bright on black
EFI_BG = BLACK
EFI_FG = (192, 192, 192)
EFI_HI = (255, 255, 255)
EFI_PROMPT = (85, 255, 85)       # green prompt
EFI_ERR = (255, 85, 85)


HEADER = "UEFI Interactive Shell v2.2"
SUBHEADER = "Mapping table"
WELCOME = [
    HEADER,
    "EDK II",
    "UEFI v2.70 (American Megatrends, 0x0005000B)",
    "Mapping table",
    "      FS0: Alias(s):HD0a65535a1:;BLK1:",
    "          PciRoot(0x0)/Pci(0x17,0x0)/Sata(0x0,0xFFFF,0x0)/HD(...)",
    "Press ESC in 5 seconds to skip startup.nsh or any other key to continue.",
    "",
    "Type 'help' for a list of commands.",
]


def draw_setup(buf, shell):
    """Render the EFI shell terminal: scrollback + input prompt."""
    buf.clear(EFI_FG, EFI_BG)

    # Use the full screen; bottom row is the active input line.
    rows = GRID_H - 1
    # Combine welcome and scrollback, keep only the trailing `rows` lines.
    scroll = []
    if shell.scrollback:
        for line in shell.scrollback:
            scroll.append(line)
    visible = scroll[-rows:]
    for i, line in enumerate(visible):
        color, text = (EFI_FG, line) if not isinstance(line, tuple) \
            else line
        y = i
        buf.text(0, y, text[:GRID_W], color, EFI_BG)

    # Prompt at the bottom row
    y = GRID_H - 1
    prompt = "Shell> "
    buf.text(0, y, prompt, EFI_PROMPT, EFI_BG)
    line = shell.buffer
    max_width = GRID_W - len(prompt) - 1
    shown = line[-max_width:] if len(line) > max_width else line
    buf.text(len(prompt), y, shown, EFI_HI, EFI_BG)
    if shell.cursor_visible:
        cx = len(prompt) + len(shown)
        if cx < GRID_W:
            buf.put(cx, y, "_", EFI_HI, EFI_BG)


def draw_dialog(buf, title, lines, buttons, sel):
    """Non-modal in EFI: just append the prompt to scrollback."""
    buf.clear(EFI_FG, EFI_BG)
    y = GRID_H // 2 - len(lines) // 2
    buf.text_center(y - 1, "[ %s ]" % title, EFI_HI, EFI_BG)
    for i, line in enumerate(lines):
        buf.text_center(y + i, line, EFI_FG, EFI_BG)
    bx = (GRID_W - sum(len(b) + 6 for b in buttons)) // 2
    by = y + len(lines) + 2
    for i, b in enumerate(buttons):
        text = "[%s]" % b
        if i == sel:
            buf.text(bx, by, " " + text + " ", EFI_BG, EFI_HI)
        else:
            buf.text(bx + 1, by, text, EFI_FG, EFI_BG)
        bx += len(b) + 6


# Stubs for option/text/help popups — EFI shell drives input via the prompt,
# not modal popups. These are unused when vendor == "efi" but kept for
# interface uniformity in case the dispatcher reaches them.
def draw_option_popup(buf, item, sel, model=None):
    pass


def draw_text_popup(buf, title, buffer, masked):
    pass


def draw_help_popup(buf):
    pass


# --- POST data ---------------------------------------------------------

POST_BG = BLACK
POST_FG = (192, 192, 192)
POST_HI = (255, 255, 255)
POST_LINES = [
    (200,  "TianoCore EDK II"),
    (400,  "UEFI Firmware v2.70 - American Megatrends"),
    (600,  "Initializing PCH..."),
    (1000, "Memory training: DDR4 16384 MB @ 2666 MT/s"),
    (1800, "Enumerating PCIe lanes..."),
    (2200, "Loading Boot Services..."),
    (2600, "Loading Runtime Services..."),
    (3000, "DXE phase complete."),
    (3300, "BDS: enumerating boot options..."),
]
POST_PROMPT = "Press ESC to enter UEFI Shell"
POST_PROMPT_KEYS = "esc"


spec = {
    "id": "efi",
    "title": HEADER,
    "footer": "EFI Shell",
    "draw_setup_shell": draw_setup,    # special: takes ShellSession, not model
    "draw_dialog": draw_dialog,
    "draw_option_popup": draw_option_popup,
    "draw_text_popup": draw_text_popup,
    "draw_help_popup": draw_help_popup,
    "welcome": WELCOME,
    "post_lines": POST_LINES,
    "post_prompt": POST_PROMPT,
    "post_prompt_keys": POST_PROMPT_KEYS,
    "post_palette": (POST_BG, POST_FG, POST_HI),
    "beep_map": {
        "ok": [],   # EFI is silent by default
        "memory_fail": [(800, 200)] * 3,
        "video_fail": [(800, 200)] * 2,
    },
    "key_legend": ["Type 'help' for commands.  'exit' to quit shell."],
}
