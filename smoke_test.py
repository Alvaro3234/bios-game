"""Headless smoke test: drives the App state machine with synthetic key events.

Run: python smoke_test.py
Also dumps popup/dialog screenshots into assets/reference/ for visual review.
"""

import os
import sys
import types

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import settings
from app import App, POST, SETUP, REBOOT, BRIEFING, OUTCOME, WIN
from renderer import Renderer
from screen import ScreenBuffer
from theme import NATIVE_W, NATIVE_H

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "assets", "reference")

failures = []


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        failures.append(name)


def key(k, unicode=""):
    return types.SimpleNamespace(key=k, unicode=unicode)


def shot(app, name, now=0):
    buf = ScreenBuffer()
    app.draw(buf, now)
    surf = Renderer().render(buf)
    out = pygame.transform.scale(surf, (NATIVE_W * 2, NATIVE_H * 2))
    pygame.image.save(out, os.path.join(REF, name))


# Fresh start: no persisted settings
for p in (settings.SETTINGS_PATH, settings.USER_DEFAULTS_PATH):
    if os.path.exists(p):
        os.remove(p)

app = App()
app.start(0)
check("starts in POST", app.state == POST)

app.handle_key(key(pygame.K_DELETE), 0)
check("DEL enters setup", app.state == SETUP)
check("starts on Main page", app.model.pages[app.model.page_idx]["id"] == "main")

# Tab to Advanced, open CPU Configuration submenu
app.handle_key(key(pygame.K_RIGHT), 0)
check("RIGHT switches to Advanced",
      app.model.pages[app.model.page_idx]["id"] == "advanced")
item = app.model.current_item()
check("cursor on CPU Configuration submenu",
      item is not None and item["label"] == "CPU Configuration")
app.handle_key(key(pygame.K_RETURN), 0)
check("Enter opens submenu", app.model.in_submenu)
item = app.model.current_item()
check("cursor skips info lines to Hyper-Threading",
      item is not None and item["id"] == "ht")

# Open option popup, pick "Disabled"
app.handle_key(key(pygame.K_RETURN), 0)
check("Enter opens option popup",
      app.popup is not None and app.popup["kind"] == "option")
shot(app, "sim_popup.png")
app.handle_key(key(pygame.K_DOWN), 0)
app.handle_key(key(pygame.K_RETURN), 0)
check("popup commits value", app.model.values["ht"] == "Disabled")
check("model is dirty", app.model.is_dirty())

# depends_on: turbo depends on speedstep
app.model.values["speedstep"] = "Disabled"
turbo = next(i for i in app.model.level.items if i.get("id") == "turbo")
check("turbo grayed when SpeedStep disabled", not app.model.is_enabled(turbo))
app.model.values["speedstep"] = "Enabled"
check("turbo enabled when SpeedStep enabled", app.model.is_enabled(turbo))

# ESC backs out of submenu
app.handle_key(key(pygame.K_ESCAPE), 0)
check("ESC leaves submenu", not app.model.in_submenu)

# F10 save & exit -> Yes -> reboot, settings.json written
app.handle_key(key(pygame.K_F10), 0)
check("F10 opens dialog", app.popup is not None and app.popup["kind"] == "dialog")
shot(app, "sim_dialog.png")
app.handle_key(key(pygame.K_RETURN), 0)
check("save&exit reboots", app.state == REBOOT)
saved = settings.load()
check("settings.json persisted ht=Disabled", saved.get("ht") == "Disabled")

# Reboot timer -> POST -> setup again, persisted value restored
app.update(2000)
check("reboot returns to POST", app.state == POST)
app.handle_key(key(pygame.K_F2), 2000)
check("F2 re-enters setup", app.state == SETUP)
check("persisted value loaded", app.model.values["ht"] == "Disabled")

# F9 optimized defaults
app.handle_key(key(pygame.K_F9), 2000)
app.handle_key(key(pygame.K_RETURN), 2000)
check("F9 restores defaults", app.model.values["ht"] == "Enabled")

# Boot page screenshot + numeric popup
while app.model.pages[app.model.page_idx]["id"] != "boot":
    app.handle_key(key(pygame.K_RIGHT), 2000)
item = app.model.current_item()
check("boot page cursor on Setup Prompt Timeout",
      item is not None and item.get("id") == "setup_timeout")
app.handle_key(key(pygame.K_RETURN), 2000)
check("numeric popup opens", app.popup is not None and app.popup["kind"] == "text")
for ch in "5":
    app.handle_key(key(ord(ch), ch), 2000)
app.handle_key(key(pygame.K_RETURN), 2000)
check("numeric popup commits", app.model.values["setup_timeout"] == 5)
shot(app, "sim_boot.png", 2000)

# Password install/status
while app.model.pages[app.model.page_idx]["id"] != "security":
    app.handle_key(key(pygame.K_LEFT), 2000)
lvl = app.model.level
lvl.cursor = next(i for i, it in enumerate(lvl.items)
                  if it.get("id") == "admin_pwd")
app.handle_key(key(pygame.K_RETURN), 2000)
for ch in "secret":
    app.handle_key(key(ord(ch), ch), 2000)
shot(app, "sim_password.png", 2000)
app.handle_key(key(pygame.K_RETURN), 2000)
status_item = next(it for it in lvl.items
                   if it.get("dynamic") == "pwd_status:admin_pwd")
check("password status shows Installed",
      app.model.display_value(status_item) == "Installed")

# ESC at top level -> quit dialog -> Yes -> reboot
app.handle_key(key(pygame.K_ESCAPE), 2000)
check("top-level ESC opens quit dialog",
      app.popup is not None and app.popup["kind"] == "dialog")
app.handle_key(key(pygame.K_RETURN), 2000)
check("quit-without-saving reboots", app.state == REBOOT)
check("dirty changes discarded", not os.path.exists(settings.SETTINGS_PATH)
      or settings.load().get("setup_timeout", 1) == 1)

# ===================================================================
# Challenge game mode
# ===================================================================
import datetime

import game as game_mod
from app import REBOOT_MS
from challenges import CHALLENGES
from game import GameManager, validate_challenges
from menu_model import MenuModel

print()
validate_challenges()
check("challenge data self-check (ids/values valid)", True)

for p in (settings.SETTINGS_PATH, settings.USER_DEFAULTS_PATH,
          game_mod.PROGRESS_PATH):
    if os.path.exists(p):
        os.remove(p)

app = App(game=GameManager())
app.start(0)
check("game starts in BRIEFING", app.state == BRIEFING)
check("first challenge is boot order",
      app.game.current()["id"] == "ch01_boot_order")
shot(app, "sim_briefing.png")

# Briefing -> POST -> setup; sabotage must be live
app.handle_key(key(pygame.K_RETURN), 0)
check("briefing key powers on (POST)", app.state == POST)
app.handle_key(key(pygame.K_DELETE), 0)
check("DEL enters setup", app.state == SETUP)
check("sabotage applied (boot1 = NIC)",
      app.model.values["boot1"] == "Onboard NIC (IPV4)")

# Fail path: save & exit without fixing anything
app.handle_key(key(pygame.K_F10), 0)
app.handle_key(key(pygame.K_RETURN), 0)
check("F10 reboots", app.state == REBOOT)
app.update(REBOOT_MS + 1)
check("reboot leads to OUTCOME", app.state == OUTCOME)
check("outcome is failure", app.outcome is False)
shot(app, "sim_outcome_fail.png")
app.handle_key(key(pygame.K_RETURN), REBOOT_MS + 1)
check("failure returns to BRIEFING", app.state == BRIEFING)
check("attempt recorded", app.game.attempts == 1)
check("one hint now visible", len(app.game.visible_hints()) == 1)
check("retry keeps player settings (no re-sabotage)",
      app.game.progress["armed_for_level"] == 0)

# Success path: fix boot1, save & exit
app.handle_key(key(pygame.K_RETURN), 0)          # power on
app.handle_key(key(pygame.K_F2), 0)              # enter setup
app.model.values["boot1"] = CHALLENGES[0]["goal"]["boot1"]
app.handle_key(key(pygame.K_F10), 0)
app.handle_key(key(pygame.K_RETURN), 0)
app.update(REBOOT_MS + 1)
check("outcome is success", app.outcome is True)
shot(app, "sim_outcome_success.png")
app.handle_key(key(pygame.K_RETURN), 0)
check("success advances to next challenge",
      app.game.level == 1 and app.game.attempts == 0)
check("next challenge briefing", app.state == BRIEFING)
check("new sabotage armed for level 1",
      settings.load().get("sata_mode", "").startswith("Intel RST"))
check("progress.json persisted", GameManager().level == 1)

# Date challenge: offset persistence round-trip
gm = app.game
gm.progress = {"level": 4, "attempts": 0, "armed_for_level": -1}
gm.ensure_machine_state()
saved = settings.load()
check("date sabotage written",
      abs(saved.get("_time_offset_s", 0) + 94608000) < 1)
check("date challenge fails with wrong clock", not gm.evaluate())
m = MenuModel()
m.apply_saved(saved)
check("model restores CMOS offset",
      abs(m.time_offset.total_seconds() + 94608000) < 1)
m.time_offset = datetime.timedelta(0)
settings.save(m.export_values())
check("date challenge passes with fixed clock", gm.evaluate())

# depends_on guard: grayed child must not satisfy the goal (ch10)
gm.progress = {"level": 9, "attempts": 0, "armed_for_level": -1}
gm.ensure_machine_state()
vals = settings.load()
vals.update({"secure_boot": "Disabled", "csm": "Disabled",
             "csm_pcie": "Legacy OpROM first"})
settings.save(vals)
check("grayed csm_pcie does not pass", not gm.evaluate())
vals["csm"] = "Enabled"
settings.save(vals)
check("full dependency chain passes", gm.evaluate())

# Advanced tier (11+): vague, hint-free, multi-step
check("campaign has at least 20 levels", len(CHALLENGES) >= 20)
check("levels 11+ are advanced tier",
      all(c.get("tier") == "advanced" for c in CHALLENGES[10:]))
check("advanced levels have no hints",
      all(not c["hints"] for c in CHALLENGES[10:]))

# ch11 performance chain: turbo only counts once speedstep is back on
gm.progress = {"level": 10, "attempts": 0, "armed_for_level": -1}
gm.ensure_machine_state()
check("ch11 sabotage live", settings.load().get("active_cores") == "2")
check("ch11 fails as sabotaged", not gm.evaluate())
vals = settings.load()
vals.update({"ht": "Enabled", "active_cores": "All", "turbo": "Enabled"})
settings.save(vals)
check("ch11 turbo alone insufficient (speedstep off)", not gm.evaluate())
vals["speedstep"] = "Enabled"
settings.save(vals)
check("ch11 full chain passes", gm.evaluate())

# ch18 TPM clear: pending op needs the chip enabled first
gm.progress = {"level": 17, "attempts": 0, "armed_for_level": -1}
gm.ensure_machine_state()
vals = settings.load()
vals["tpm_pending"] = "TPM Clear"          # chip still disabled
settings.save(vals)
check("ch18 pending clear on disabled chip fails", not gm.evaluate())
vals["tpm_enable"] = "Enable"
settings.save(vals)
check("ch18 enable + clear passes", gm.evaluate())

# ch20 kiosk: all five goals required
gm.progress = {"level": 19, "attempts": 1, "armed_for_level": -1}
gm.ensure_machine_state()
vals = settings.load()
vals.update({"admin_pwd": "k10sk!", "quiet_boot": "Enabled",
             "fast_boot": "Enabled", "boot2": "Disabled"})
settings.save(vals)
check("ch20 four of five goals fails", not gm.evaluate())
vals["boot3"] = "Disabled"
settings.save(vals)
check("ch20 full hardening passes", gm.evaluate())
app.game.progress = gm.progress
app.state = BRIEFING
shot(app, "sim_briefing_advanced.png")

# Win: jump to the final level, then succeed -> WIN state
app.game.progress["level"] = len(CHALLENGES) - 1
app.game.progress["phase"] = 0
app.state = OUTCOME
app.outcome = True
# Burn through any remaining phases of the final level so we land on WIN.
for _ in range(8):
    if app.state == WIN:
        break
    app.handle_key(key(pygame.K_RETURN), 0)
    if app.state == BRIEFING and app.game.complete:
        app.handle_key(key(pygame.K_RETURN), 0)
    if app.state == OUTCOME:
        app.outcome = True
check("campaign complete -> WIN", app.state == WIN)
shot(app, "sim_win.png")
app.handle_key(key(pygame.K_r), 0)
check("R restarts campaign", app.state == BRIEFING and app.game.level == 0)

# ----------------------------------------------------------- multi-phase
# Find the first goal_phases challenge in the campaign
mp_idx = next(i for i, c in enumerate(CHALLENGES) if c.get("goal_phases"))
mp_ch = CHALLENGES[mp_idx]
gm.progress = {"level": mp_idx, "attempts": 0,
               "armed_for_level": -1, "phase": 0}
gm.ensure_machine_state()
check("multi-phase phase 0 initially fails", not gm.evaluate())
vals = settings.load()
# Apply phase 0 goal
vals.update(mp_ch["goal_phases"][0]["goal"])
settings.save(vals)
check("multi-phase phase 0 passes after fix", gm.evaluate())
check("multi-phase has more phases", gm.has_more_phases())
gm.advance_phase()
check("multi-phase advanced to phase 1", gm.phase == 1)
check("multi-phase phase 1 still fails", not gm.evaluate())
vals = settings.load()
vals.update(mp_ch["goal_phases"][1]["goal"])
settings.save(vals)
check("multi-phase phase 1 passes after fix", gm.evaluate())
check("multi-phase no more phases", not gm.has_more_phases())

# ----------------------------------------------------------- EFI shell
from shell import ShellSession as _SS
m_efi = MenuModel("intel")
sh = _SS(m_efi)
sh.execute("setvar vmx Disabled")
check("efi shell setvar option", m_efi.values["vmx"] == "Disabled")
out = sh.execute("setvar vmx NotReal")
check("efi shell rejects invalid value",
      any("Invalid" in l for l in out))
out = sh.execute("bcfg boot dump")
check("efi shell bcfg dump prints boot1",
      any("boot1" in l for l in out))
m_efi.values["boot1"] = "Onboard NIC (IPV4)"
m_efi.values["boot2"] = "UEFI: SanDisk Ultra USB 3.0 1.00"
m_efi.values["boot3"] = "Windows Boot Manager (Samsung SSD 970 EVO Plus 1TB)"
sh.execute("bcfg boot mv 1 3")
check("efi shell bcfg mv swaps slots",
      m_efi.values["boot1"].startswith("Windows")
      and m_efi.values["boot3"] == "Onboard NIC (IPV4)")
out = sh.execute("reset cold")
check("efi shell reset cold sets wants_reboot", sh.wants_reboot)

# ----------------------------------------------------------- procedural
from procedural import generate_shift, SABOTAGE_TEMPLATES
s1 = generate_shift(seed=42, n=5)
s2 = generate_shift(seed=42, n=5)
check("procedural: seed determinism",
      [c["_template"] for c in s1] == [c["_template"] for c in s2])
check("procedural: 5 tickets", len(s1) == 5)
check("procedural: no template repeats in a shift",
      len({c["_template"] for c in s1}) == 5)
from game import _validate_goal_dict as _vgd
for ch in s1:
    _vgd(ch["id"] + ".sabotage", ch["sabotage"])
    _vgd(ch["id"] + ".goal", ch["goal"])
check("procedural: tickets pass goal validator", True)

# Verify shift mode wires through GameManager
gm_shift = game_mod.GameManager(challenges=s1, persist=False)
check("shift GM has 5 levels", len(gm_shift.challenges) == 5)
check("shift GM does not persist", not gm_shift.persist)

# ----------------------------------------------------------- audio (silent)
os.environ["SDL_AUDIODRIVER"] = "dummy"
from audio import Audio
_a = Audio(enabled=True)   # should auto-disable due to dummy driver
check("audio auto-disables in headless", not _a.enabled)
_a.click(); _a.beep(900, 100); _a.beep_pattern([(800, 50), (1200, 50)])
_a.jingle("success"); _a.jingle("fail")
check("audio silent no-op never raises", True)

# ----------------------------------------------------------- vendor registry
import vendors as _vendors
check("vendor registry has 3 vendors", set(_vendors.ids()) >=
      {"ami", "award", "efi"})
for vid in ("ami", "award", "efi"):
    spec = _vendors.get(vid)
    check("vendor %s has draw_setup or draw_setup_shell" % vid,
          "draw_setup" in spec or "draw_setup_shell" in spec)

# Cleanup so a fresh game starts at level 0 with pristine settings
for p in (settings.SETTINGS_PATH, settings.USER_DEFAULTS_PATH,
          game_mod.PROGRESS_PATH):
    if os.path.exists(p):
        os.remove(p)

print()
if failures:
    print("FAILED:", len(failures))
    sys.exit(1)
print("All checks passed.")
