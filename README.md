# UEFI BIOS Simulator — AMI Aptio Setup Utility

A graphically accurate simulator of the classic AMI **Aptio Setup Utility**
(the blue/gray UEFI BIOS setup screen), written in Python + Pygame.
It is a simulator — it doesn't touch real firmware.

![setup](assets/reference/sim_setup.png)

## Run

```
python main.py              # challenge game (default)
python main.py --freeplay   # sandbox: just the BIOS, no game
```

Requires Python 3 and `pygame` (tested with pygame-ce 2.5.7).

## Challenge mode

A linear campaign of 20 repair tickets. Each level shows a briefing
describing a broken machine (wrong boot order, BSOD after a SATA mode
change, Secure Boot blocking a live USB, dead CMOS clock, Windows 11
TPM requirements, PXE imaging, legacy GPU needing CSM…). Power on,
enter Setup, fix the firmware configuration, and Save & Exit: the
machine reboots and shows the realistic consequence — success boots the
OS, failure shows the matching error screen and sends you back to the
briefing with one more hint revealed. Progress persists in
`progress.json` and resumes at the last unsolved level.

Levels 11–20 are the **senior technician tier**: vague symptom-only
tickets, no hints, and multi-setting fixes (performance tuning chains,
Wake-on-LAN, IOMMU passthrough, TPM clearing, custom Secure Boot
policy, kiosk hardening).

## Keys

| Key | Action |
|---|---|
| `DEL` / `F2` | Enter Setup from the POST screen |
| `↑` `↓` | Select item |
| `←` `→` | Select screen (tab) |
| `Enter` | Open submenu / option popup / edit field |
| `+` / `-` | Change option value in place |
| `Tab` | Switch date/time element |
| `ESC` | Back out of submenu / exit dialog |
| `F1` | General help |
| `F2` | Load previous values |
| `F9` | Load optimized defaults |
| `F10` | Save & exit (reboots to POST) |
| `F11` | Toggle fullscreen |
| `F12` | Save a screenshot (`screenshot.png`) |

Changed settings persist in `settings.json` (Save & Exit / F10).
"Save as User Defaults" writes `user_defaults.json`.

## Layout

- `main.py` — window, scaling, event loop (also `--screenshot out.png [--screen post|setup]` headless mode)
- `app.py` — state machine: POST → SETUP (popups/dialogs) → REBOOT → POST
- `theme.py` — palette, grid dimensions, layout metrics (single visual tuning point)
- `font.py` / `screen.py` / `renderer.py` — glyph cache, 100×31 cell buffer, chrome drawing
- `menu_data.py` — data-driven definitions of all six pages and submenus
- `menu_model.py` — navigation, values, dependencies (`depends_on` graying)
- `post_screen.py` — POST timeline (memory count, device detection, blinking prompt)
- `settings.py` — atomic JSON persistence
- `smoke_test.py` — headless functional test (`python smoke_test.py`)

## Font

Renders with **PxPlus IBM VGA 8x16** from the
[Ultimate Oldschool PC Font Pack](https://int10h.org/oldschool-pc-fonts/)
(CC BY-SA 4.0, see `assets/fonts/LICENSE.TXT`). Falls back to Lucida
Console / Consolas / Courier New if the bundled TTF is missing.
