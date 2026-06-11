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

# Tab to Advanced (via Ai Tweaker), open CPU Configuration submenu
app.handle_key(key(pygame.K_RIGHT), 0)
check("RIGHT switches to Ai Tweaker",
      app.model.pages[app.model.page_idx]["id"] == "oc")
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
check("classic advanced levels have no hints",
      all(not c["hints"] for c in CHALLENGES[10:23]))

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

# Win: jump to the final level (last phase if multi-phase) -> WIN state
app.game.progress["level"] = len(CHALLENGES) - 1
app.game.progress["phase"] = max(
    0, len(CHALLENGES[-1].get("goal_phases", [])) - 1)
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
check("vendor registry has 4 vendors", set(_vendors.ids()) >=
      {"ami", "award", "efi", "phoenix"})
for vid in ("ami", "award", "efi", "phoenix"):
    spec = _vendors.get(vid)
    check("vendor %s has draw_setup or draw_setup_shell" % vid,
          "draw_setup" in spec or "draw_setup_shell" in spec)

# ----------------------------------------------------------- engine (Phase 1)
import json

import hardware_rules
from app import SETUP_SHELL
from hardware_rules import match_value

print()


def buffer_text(buf):
    return "\n".join("".join(c[0] for c in row) for row in buf.cells)


_BASE_TICKET = {
    "id": "t_base", "vendor": "award", "cpu_brand": "amd",
    "title": "Test", "briefing": ["Test machine."], "hints": [],
    "sabotage": {"hd_audio": "Disabled"}, "goal": {"hd_audio": "Enabled"},
    "fail": {"style": "black", "lines": ["no boot"]},
    "success_lines": ["ok"],
}

# Vendor-aware POST: an award ticket boots with the Award sequence
app_aw = App(game=GameManager(challenges=[_BASE_TICKET], persist=False))
app_aw.start(0)
app_aw.handle_key(key(pygame.K_RETURN), 0)
check("award ticket powers on to POST", app_aw.state == POST)
buf = ScreenBuffer()
app_aw.draw(buf, 10_000)
txt = buffer_text(buf)
check("award POST lines rendered", "Award Modular BIOS" in txt)
check("award POST memory count completes",
      "Memory Testing :  524288K OK" in txt)
check("award POST prompt rendered", "Press DEL to enter SETUP" in txt)
app_aw.handle_key(key(pygame.K_F2), 10_000)
check("award POST ignores F2", app_aw.state == POST)
app_aw.handle_key(key(pygame.K_DELETE), 10_000)
check("award POST DEL enters setup", app_aw.state == SETUP)

# EFI POST: ESC (and only ESC) enters the shell
app_efi = App(game=GameManager(
    challenges=[dict(_BASE_TICKET, id="t_efi", vendor="efi")], persist=False))
app_efi.start(0)
app_efi.handle_key(key(pygame.K_RETURN), 0)
buf = ScreenBuffer()
app_efi.draw(buf, 10_000)
check("efi POST lines rendered", "TianoCore EDK II" in buffer_text(buf))
app_efi.handle_key(key(pygame.K_DELETE), 10_000)
check("efi POST ignores DEL", app_efi.state == POST)
app_efi.handle_key(key(pygame.K_ESCAPE), 10_000)
check("efi POST ESC enters shell", app_efi.state == SETUP_SHELL)

# Ticket-driven POST context: extra lines + stuck debug code
app_ctx = App(game=GameManager(challenges=[dict(
    _BASE_TICKET, id="t_ctx", vendor="ami",
    post_extra_lines=[(3500, "CMOS Checksum Bad - Press F2 to Run Setup")],
    post_code_hint="55")], persist=False))
app_ctx.start(0)
app_ctx.handle_key(key(pygame.K_RETURN), 0)
buf = ScreenBuffer()
app_ctx.draw(buf, 10_000)
txt = buffer_text(buf)
check("post extra_lines rendered", "CMOS Checksum Bad" in txt)
from theme import GRID_W as _GW, GRID_H as _GH
check("post stuck code rendered",
      buf.cells[_GH - 1][_GW - 3][0] + buf.cells[_GH - 1][_GW - 2][0] == "55")

# no_video variant: setup blocked, vendor beep requested, ESC powers off
app_nv = App(game=GameManager(challenges=[dict(
    _BASE_TICKET, id="t_nv", vendor="ami",
    post_variant={"variant": "no_video", "beep": "memory_fail"})],
    persist=False))
app_nv.start(0)
app_nv.handle_key(key(pygame.K_RETURN), 0)
app_nv.handle_key(key(pygame.K_DELETE), 100)
check("no_video blocks setup entry", app_nv.state == POST)
check("no_video requests fault beep",
      app_nv.post.pending_beep(700) == "memory_fail")
app_nv.handle_key(key(pygame.K_ESCAPE), 700)
check("no_video ESC powers off to briefing", app_nv.state == BRIEFING)

# Constraint match grammar
check("match exact", match_value("A", "A") and not match_value("B", "A"))
check("match membership", match_value("A", ["A", "B"])
      and not match_value("C", ["A", "B"]))
check("match comparators", match_value(5, {">=": 3, "<=": 8})
      and not match_value(2, {">=": 3}) and not match_value(9, {"<=": 8}))

# Per-ticket boot constraint trumps the goal; releasing it passes
gm_con = GameManager(challenges=[dict(
    _BASE_TICKET, id="t_con", vendor="ami",
    boot_constraints=[{
        "id": "test_con",
        "match": {"setup_timeout": {">=": 10}},
        "fail": {"style": "black", "lines": ["POST loop"],
                 "post_code": "55"},
    }])], persist=False)
gm_con.ensure_machine_state()
vals = settings.load()
vals.update({"hd_audio": "Enabled", "setup_timeout": 15})
settings.save(vals)
ok, fi = gm_con.evaluate_full()
check("violated constraint fails the boot",
      ok is False and fi is not None and fi.get("post_code") == "55")
check("evaluate() keeps bool contract", gm_con.evaluate() is False)
vals["setup_timeout"] = 1
settings.save(vals)
ok, fi = gm_con.evaluate_full()
check("released constraint passes", ok is True and fi is None)

# Global constraint with an "unless" escape combo
hardware_rules.GLOBAL_CONSTRAINTS.append({
    "id": "g_test",
    "match": {"numlock": "Off"},
    "unless": {"quiet_boot": "Disabled"},
    "fail": {"style": "black", "lines": ["numlock crash"]},
})
try:
    vals = settings.load()
    vals.update({"numlock": "Off", "quiet_boot": "Enabled"})
    settings.save(vals)
    ok, fi = gm_con.evaluate_full()
    check("global constraint fires", ok is False and fi is not None)
    vals["quiet_boot"] = "Disabled"
    settings.save(vals)
    ok, fi = gm_con.evaluate_full()
    check("unless combo escapes the constraint", ok is True)
finally:
    hardware_rules.GLOBAL_CONSTRAINTS.pop()

# Constraint fail_info drives the outcome screen
app_fi = App(game=gm_con)
app_fi.state = OUTCOME
app_fi.outcome, app_fi.outcome_fail = False, {
    "style": "black", "lines": ["CONSTRAINT FAIL LINE"]}
buf = ScreenBuffer()
app_fi.draw(buf, 0)
check("fail_info overrides scripted fail",
      "CONSTRAINT FAIL LINE" in buffer_text(buf))

# hw: dynamic info values (static + reactive forms)
m_hw = MenuModel()
m_hw.set_hw_info({
    "cpu_temp": "95 C",
    "cpu_fan": {"by": "ht", "map": {"Enabled": "1200 RPM"},
                "default": "0 RPM"},
})
check("hw: static value resolves",
      m_hw.display_value({"type": "info", "dynamic": "hw:cpu_temp"}) == "95 C")
fan_item = {"type": "info", "dynamic": "hw:cpu_fan"}
check("hw: reactive value follows setting",
      m_hw.display_value(fan_item) == "1200 RPM")
m_hw.values["ht"] = "Disabled"
check("hw: reactive value falls back to default",
      m_hw.display_value(fan_item) == "0 RPM")

# depends_on list form
m_dep = MenuModel()
dep_item = {"type": "option", "id": "x", "values": ["A"],
            "depends_on": ("ht", ["Enabled", "Auto"])}
check("depends_on list form enables", m_dep.is_enabled(dep_item))
m_dep.values["ht"] = "Disabled"
check("depends_on list form grays", not m_dep.is_enabled(dep_item))

# F5/F6 value-change aliases in setup
app_f5 = App()
app_f5.start(0)
app_f5.handle_key(key(pygame.K_DELETE), 0)
while app_f5.model.pages[app_f5.model.page_idx]["id"] != "advanced":
    app_f5.handle_key(key(pygame.K_RIGHT), 0)
app_f5.handle_key(key(pygame.K_RETURN), 0)      # CPU Configuration
check("F5/F6 precondition (cursor on ht)",
      app_f5.model.current_item()["id"] == "ht")
app_f5.handle_key(key(pygame.K_F6), 0)
check("F6 changes value forward", app_f5.model.values["ht"] == "Disabled")
app_f5.handle_key(key(pygame.K_F5), 0)
check("F5 changes value back", app_f5.model.values["ht"] == "Enabled")

# hw_actions: persistence round-trip + cleared on advance
if os.path.exists(game_mod.PROGRESS_PATH):
    os.remove(game_mod.PROGRESS_PATH)
gm_act = GameManager()
gm_act.perform_action("replace_battery")
check("hw_action recorded", gm_act.has_action("replace_battery"))
check("hw_action persisted", GameManager().has_action("replace_battery"))
gm_act.advance()
check("advance clears hw_actions",
      not GameManager().has_action("replace_battery"))

# required_actions gates evaluate_full
gm_req = GameManager(challenges=[dict(
    _BASE_TICKET, id="t_req", vendor="ami",
    required_actions=["replace_battery"])], persist=False)
gm_req.ensure_machine_state()
vals = settings.load()
vals["hd_audio"] = "Enabled"
settings.save(vals)
ok, fi = gm_req.evaluate_full()
check("missing bench action fails", ok is False and fi is None)
gm_req.perform_action("replace_battery")
check("performed bench action passes", gm_req.evaluate() is True)

# Old-format progress.json (pre-hw_actions) still loads
with open(game_mod.PROGRESS_PATH, "w", encoding="utf-8") as f:
    json.dump({"level": 3, "attempts": 1, "armed_for_level": 3,
               "phase": 0}, f)
gm_old = GameManager()
check("old progress.json loads with empty hw_actions",
      gm_old.level == 3 and gm_old.progress["hw_actions"] == [])

# ----------------------------------------------------------- hardware (Phase 2)
from menu_model import iter_persistable

print()

check("menu has 8 pages", len(MenuModel().pages) == 8)
check("campaign has 28 levels", len(CHALLENGES) >= 28)

# XMP Profile 2 fails memory training unless tuned (board limit)
gm_hw = GameManager(challenges=[dict(
    _BASE_TICKET, id="t_hw", vendor="ami", sabotage={"xmp": "Profile 2"},
    goal={})], persist=False)
gm_hw.ensure_machine_state()
ok, fi = gm_hw.evaluate_full()
check("XMP Profile 2 fails training",
      ok is False and fi is not None and fi["style"] == "memtrain")
vals = settings.load()
vals.update({"dram_volt": "1.45V", "cmd_rate": "2T"})
settings.save(vals)
ok, fi = gm_hw.evaluate_full()
check("tuned XMP Profile 2 trains", ok is True)
vals.update({"xmp": "Disabled", "dram_volt": "Auto", "cmd_rate": "Auto"})
settings.save(vals)
check("disabling XMP also boots", gm_hw.evaluate() is True)

# Manual 3600 MHz hits the same wall
vals["dram_freq"] = "3600 MHz"
settings.save(vals)
ok, fi = gm_hw.evaluate_full()
check("manual 3600 fails training", ok is False and fi["style"] == "memtrain")
vals["dram_freq"] = "3200 MHz"
settings.save(vals)
check("3200 is stable", gm_hw.evaluate() is True)

# Overclock: ratio 50 needs positive vcore; 53+ never boots
vals.update({"cpu_ratio": 50, "vcore_offset": "Auto"})
settings.save(vals)
ok, fi = gm_hw.evaluate_full()
check("50x on Auto vcore watchdogs",
      ok is False and "CLOCK_WATCHDOG_TIMEOUT" in " ".join(fi["lines"]))
vals["vcore_offset"] = "+0.10V"
settings.save(vals)
check("50x with +0.10V boots", gm_hw.evaluate() is True)
vals["cpu_ratio"] = 53
settings.save(vals)
ok, fi = gm_hw.evaluate_full()
check("53x never boots (silicon wall)",
      ok is False and fi.get("post_code") == "00")

# Fan disabled trips thermal protection
vals.update({"cpu_ratio": 36, "vcore_offset": "Auto",
             "cpu_fan_profile": "Disabled"})
settings.save(vals)
ok, fi = gm_hw.evaluate_full()
check("disabled CPU fan trips thermal",
      ok is False and fi["style"] == "thermtrip")
vals["cpu_fan_profile"] = "Standard"
settings.save(vals)
check("fan restored boots", gm_hw.evaluate() is True)

# Monitor page sensors react to settings out of the box
m_mon = MenuModel()
fan_info = {"type": "info", "dynamic": "hw:cpu_fan_rpm"}
check("default fan readout", m_mon.display_value(fan_info) == "1280 RPM")
m_mon.values["cpu_fan_profile"] = "Disabled"
check("fan readout follows profile", m_mon.display_value(fan_info) == "N/A")
mem_info = {"type": "info", "dynamic": "hw:dram_freq_now"}
check("memory frequency follows XMP",
      m_mon.display_value(mem_info) == "2666 MHz")
m_mon.values["xmp"] = "Profile 1"
check("memory frequency shows XMP speed",
      m_mon.display_value(mem_info) == "3200 MHz")

# M.2 lane sharing grays SATA port 1 hot plug
m_m2 = MenuModel()
p1 = next(it for it in iter_persistable() if it["id"] == "sata_p1_hotplug")
check("port 1 hotplug enabled by default", m_m2.is_enabled(p1))
m_m2.values["m2_mode"] = "SATA"
check("M.2 SATA mode grays port 1 hotplug", not m_m2.is_enabled(p1))

# ch28 phase 1: grayed hotplug can't satisfy the phase-2 goal early
ch28 = next(c for c in CHALLENGES if c["id"] == "ch28_m2_lanes")
gm_28 = GameManager(challenges=[ch28], persist=False)
gm_28.ensure_machine_state()
check("ch28 sabotage live", settings.load().get("m2_mode") == "SATA")
check("ch28 phase 0 fails as shipped", not gm_28.evaluate())
vals = settings.load()
vals["m2_mode"] = "Auto"
settings.save(vals)
check("ch28 phase 0 passes after lane fix", gm_28.evaluate())
gm_28.advance_phase()
check("ch28 phase 1 needs hotplug", not gm_28.evaluate())
vals["sata_p1_hotplug"] = "Enabled"
settings.save(vals)
check("ch28 phase 1 passes", gm_28.evaluate())

# ch24: keeping Profile 2 forces the tuning combo
ch24 = next(c for c in CHALLENGES if c["id"] == "ch24_xmp_tuning")
gm_24 = GameManager(challenges=[ch24], persist=False)
gm_24.ensure_machine_state()
check("ch24 fails as shipped", not gm_24.evaluate())
vals = settings.load()
vals["xmp"] = "Disabled"          # lazy fix: boots, but goal demands P2
settings.save(vals)
check("ch24 rejects disabling XMP", not gm_24.evaluate())
vals.update({"xmp": "Profile 2", "dram_volt": "1.45V", "cmd_rate": "2T"})
settings.save(vals)
check("ch24 tuned Profile 2 passes", gm_24.evaluate())

# New templates generate valid, winnable tickets
from procedural import generate_ticket
_rng = __import__("random").Random(7)
for _tpl_id in ("tpl_xmp_unstable", "tpl_oc_watchdog", "tpl_fan_overheat",
                "tpl_rtc_wake", "tpl_ac_restore", "tpl_erp_wol_conflict",
                "tpl_m2_lanes", "tpl_cmos_clock"):
    _exclude = {t["id"] for t in SABOTAGE_TEMPLATES} - {_tpl_id}
    t = generate_ticket(_rng, _exclude=_exclude)
    _vgd(t["id"] + ".sabotage", t["sabotage"])
    _vgd(t["id"] + ".goal", t["goal"])
check("new templates pass the validator", True)
t_fan = generate_ticket(_rng, _exclude={t["id"] for t in SABOTAGE_TEMPLATES}
                        - {"tpl_fan_overheat"})
check("fan template carries hw_info clue", "cpu_temp" in t_fan.get("hw_info", {}))

# ----------------------------------------------------------- vendors (Phase 3)
print()

# Award home grid: category navigation, edit, save round-trip
app_home = App(game=GameManager(
    challenges=[dict(_BASE_TICKET, id="t_home")], persist=False))
app_home.start(0)
app_home.handle_key(key(pygame.K_RETURN), 0)
app_home.handle_key(key(pygame.K_DELETE), 10_000)
check("award setup uses the home grid",
      app_home.model.home_items is not None)
check("home cursor on STANDARD CMOS SETUP",
      app_home.model.current_item()["label"] == "STANDARD CMOS SETUP")
buf = ScreenBuffer()
app_home.draw(buf, 0)
txt = buffer_text(buf)
check("home grid renders categories",
      "INTEGRATED PERIPHERALS" in txt and "PC HEALTH STATUS" in txt
      and "FREQUENCY/VOLTAGE CONTROL" in txt)
app_home.handle_key(key(pygame.K_RIGHT), 0)
check("RIGHT jumps to the second column",
      app_home.model.current_item()["label"] == "FREQUENCY/VOLTAGE CONTROL")
app_home.handle_key(key(pygame.K_LEFT), 0)
check("LEFT jumps back to the first column",
      app_home.model.current_item()["label"] == "STANDARD CMOS SETUP")
for _ in range(5):
    app_home.handle_key(key(pygame.K_DOWN), 0)
check("cursor reaches INTEGRATED PERIPHERALS",
      app_home.model.current_item()["label"] == "INTEGRATED PERIPHERALS")
app_home.handle_key(key(pygame.K_RETURN), 0)
check("Enter opens the category", app_home.model.in_submenu)
lvl = app_home.model.level
lvl.cursor = next(i for i, it in enumerate(lvl.items)
                  if it.get("id") == "hd_audio")
app_home.handle_key(key(pygame.K_F6), 0)
check("hd_audio toggled inside the category",
      app_home.model.values["hd_audio"] == "Enabled")
app_home.handle_key(key(pygame.K_ESCAPE), 0)
check("Esc returns to the home grid", not app_home.model.in_submenu)
app_home.handle_key(key(pygame.K_F10), 0)
app_home.handle_key(key(pygame.K_RETURN), 0)
check("F10 from home saves and reboots", app_home.state == REBOOT)
check("award home save persisted",
      settings.load().get("hd_audio") == "Enabled")
app_home.update(20_000)
check("award ticket solved via home grid", app_home.outcome is True)

# Esc at home opens the quit dialog (app_aw is still sitting in setup)
app_aw.handle_key(key(pygame.K_ESCAPE), 10_000)
check("Esc at home opens quit dialog",
      app_aw.popup is not None and app_aw.popup["kind"] == "dialog")

# EFI shell: new commands
m_sh = MenuModel("intel")
sh2 = _SS(m_sh)
for cmd in ("ver", "map", "memmap", "dh", "dmpstore"):
    check("shell %s outputs" % cmd, bool(sh2.execute(cmd)))
check("shell echo echoes", sh2.execute("echo ciao") == ["ciao"])
check("shell time shows clock", ":" in sh2.execute("time")[0])
sh2.execute("date 06/11/2023")
check("shell date sets the RTC offset",
      abs(m_sh.time_offset.total_seconds()) > 86400 * 300)
check("shell date readback", sh2.execute("date")[0] == "06/11/2023")
sh2.execute("time 08:30:00")
check("shell time readback",
      sh2.execute("time")[0].startswith("08:30"))
check("shell help lists time/date",
      any("time" in l for l in sh2.execute("help")))

# ch29: clock fixable entirely from the EFI shell
import datetime as _dt
ch29 = next(c for c in CHALLENGES if c["id"] == "ch29_efi_clock")
gm_29 = GameManager(challenges=[ch29], persist=False)
gm_29.ensure_machine_state()
check("ch29 fails with drifted clock", not gm_29.evaluate())
m29 = MenuModel()
m29.apply_saved(settings.load())
sh29 = _SS(m29)
_now = _dt.datetime.now()
sh29.execute("date %s" % _now.strftime("%m/%d/%Y"))
sh29.execute("time %s" % _now.strftime("%H:%M:%S"))
settings.save(m29.export_values())
check("ch29 passes after shell clock fix", gm_29.evaluate())

# ----------------------------------------------------------- phoenix (Phase 4)
print()

ph_ticket = dict(_BASE_TICKET, id="t_ph", vendor="phoenix")
app_ph = App(game=GameManager(challenges=[ph_ticket], persist=False))
app_ph.start(0)
app_ph.handle_key(key(pygame.K_RETURN), 0)
buf = ScreenBuffer()
app_ph.draw(buf, 10_000)
txt = buffer_text(buf)
check("phoenix POST lines rendered",
      "PhoenixBIOS 4.0 Release 6.0" in txt)
check("phoenix POST counts RAM in K",
      "523264K Extended RAM Passed" in txt)
check("phoenix POST prompt rendered", "Press <F2> to enter SETUP" in txt)
app_ph.handle_key(key(pygame.K_DELETE), 10_000)
check("phoenix POST ignores DEL", app_ph.state == POST)
app_ph.handle_key(key(pygame.K_F2), 10_000)
check("phoenix F2 enters setup", app_ph.state == SETUP)
buf = ScreenBuffer()
app_ph.draw(buf, 0)
txt = buffer_text(buf)
check("phoenix setup chrome rendered",
      "PhoenixBIOS Setup Utility" in txt and "Item Specific Help" in txt)
check("phoenix page title overrides applied",
      "Performance" in txt and "Ai Tweaker" not in txt)

# Solve the ticket end-to-end with phoenix keys (F5/F6 included)
while app_ph.model.pages[app_ph.model.page_idx]["id"] != "chipset":
    app_ph.handle_key(key(pygame.K_RIGHT), 0)
app_ph.handle_key(key(pygame.K_DOWN), 0)       # PCH-IO Configuration
app_ph.handle_key(key(pygame.K_RETURN), 0)
lvl = app_ph.model.level
lvl.cursor = next(i for i, it in enumerate(lvl.items)
                  if it.get("id") == "hd_audio")
app_ph.handle_key(key(pygame.K_F6), 0)
check("phoenix F6 toggles hd_audio",
      app_ph.model.values["hd_audio"] == "Enabled")
app_ph.handle_key(key(pygame.K_F10), 0)
app_ph.handle_key(key(pygame.K_RETURN), 0)
app_ph.update(REBOOT_MS * 2)
check("phoenix ticket solved end-to-end",
      app_ph.state == OUTCOME and app_ph.outcome is True)

# Grouped beep codes: 1-3-3-1 memory pattern = 8 beeps + 3 pauses
mem_pattern = _vendors.get("phoenix")["beep_map"]["memory_fail"]
check("phoenix 1-3-3-1 memory beep pattern",
      sum(1 for f, _ in mem_pattern if f) == 8
      and sum(1 for f, _ in mem_pattern if not f) == 3)

# Phoenix curated tickets validate and are reachable
for cid in ("ch30_phoenix_dock", "ch31_phoenix_rtc", "ch32_phoenix_fan"):
    ch = next(c for c in CHALLENGES if c["id"] == cid)
    check("%s is a phoenix ticket" % cid, ch["vendor"] == "phoenix")

# ----------------------------------------------------------- diagnosis (Phase 5)
print()

WINDOWS_SSD = CHALLENGES[0]["goal"]["boot1"]
NIC = CHALLENGES[0]["sabotage"]["boot1"]

# Dead CMOS battery: saved fixes evaporate until the battery is replaced
ch33 = next(c for c in CHALLENGES if c["id"] == "ch33_cmos_battery")
gm_b = GameManager(challenges=[ch33], persist=False)
app_b = App(game=gm_b)
app_b.start(0)
check("battery ticket starts in BRIEFING", app_b.state == BRIEFING)
buf = ScreenBuffer()
app_b.draw(buf, 0)
check("briefing shows the TOOLBOX",
      "TOOLBOX" in buffer_text(buf)
      and "replace the CMOS battery" in buffer_text(buf))
ctx = gm_b.post_context()
check("dead battery injects CMOS checksum POST lines",
      any("CMOS checksum error" in t for _, t in ctx.get("extra_lines", [])))
vals = settings.load()
vals.update({"boot1": WINDOWS_SSD, "_time_offset_s": 0})
settings.save(vals)
ok, fi = gm_b.evaluate_full()
check("correct settings still fail with dead battery", ok is False)
gm_b.record_failure()
gm_b.ensure_machine_state()
saved = settings.load()
check("dead battery wipes the player's fixes on reboot",
      saved.get("boot1") == NIC
      and abs(saved.get("_time_offset_s", 0) + 94608000) < 1)
app_b.handle_key(key(pygame.K_b), 0)
check("B replaces the battery without powering on",
      app_b.state == BRIEFING and gm_b.has_action("replace_battery"))
buf = ScreenBuffer()
app_b.draw(buf, 0)
check("toolbox marks the action done", "[done:" in buffer_text(buf))
check("fresh battery clears the checksum POST lines",
      not gm_b.post_context().get("extra_lines"))
vals = settings.load()
vals.update({"boot1": WINDOWS_SSD, "_time_offset_s": 0})
settings.save(vals)
gm_b.ensure_machine_state()
check("fresh battery retains settings across boots",
      settings.load().get("boot1") == WINDOWS_SSD)
check("ch33 passes after battery swap + fixes", gm_b.evaluate() is True)

# No-video ticket: blind machine, fixed from the bench
ch34 = next(c for c in CHALLENGES if c["id"] == "ch34_novideo")
app_n = App(game=GameManager(challenges=[ch34], persist=False))
app_n.start(0)
app_n.handle_key(key(pygame.K_RETURN), 0)        # power on
buf = ScreenBuffer()
app_n.draw(buf, 5000)
check("no-video POST transcribes the beeps",
      "three short" in buffer_text(buf))
app_n.handle_key(key(pygame.K_DELETE), 5000)
check("no-video blocks Setup", app_n.state == POST)
app_n.handle_key(key(pygame.K_ESCAPE), 5000)     # power off
check("ESC powers off to the bench", app_n.state == BRIEFING)
app_n.handle_key(key(pygame.K_j), 5000)          # clear CMOS
check("J clears NVRAM to defaults",
      app_n.state == BRIEFING
      and settings.load().get("xmp") == "Disabled"
      and app_n.game.has_action("clear_cmos"))
app_n.handle_key(key(pygame.K_RETURN), 5000)     # power on again
app_n.handle_key(key(pygame.K_DELETE), 20_000)
check("video restored after CMOS clear", app_n.state == SETUP)
app_n.handle_key(key(pygame.K_F10), 20_000)
app_n.handle_key(key(pygame.K_RETURN), 20_000)
app_n.update(20_000 + REBOOT_MS + 1)
check("ch34 solved from the bench",
      app_n.state == OUTCOME and app_n.outcome is True)

# Red herrings: deterministic, bounded, never interfering
import random as _random
from procedural import add_red_herrings, NOISE_SAFE
t1 = {"sabotage": {"boot1": NIC}, "goal": {"boot1": WINDOWS_SSD}}
t2 = {"sabotage": {"boot1": NIC}, "goal": {"boot1": WINDOWS_SSD}}
add_red_herrings(_random.Random(3), t1, k=2)
add_red_herrings(_random.Random(3), t2, k=2)
noise = set(t1["sabotage"]) - {"boot1"}
check("red herrings added from the safe pool",
      len(noise) == 2 and noise <= set(NOISE_SAFE))
check("red herrings deterministic per seed", t1 == t2)
t3 = {"sabotage": {}, "goal": {"cstates": "Enabled"}}
add_red_herrings(_random.Random(1), t3, k=99)
check("goal ids excluded from noise", "cstates" not in t3["sabotage"])
t4 = {"sabotage": {}, "goal": {}}
add_red_herrings(_random.Random(1), t4, k=99)
_constraint_ids = {"xmp", "dram_freq", "dram_volt", "cmd_rate",
                   "cpu_ratio", "vcore_offset", "cpu_fan_profile"}
check("noise never touches board-constraint inputs",
      not set(t4["sabotage"]) & _constraint_ids)
for iid in t4["sabotage"]:
    _vgd("noise", {iid: t4["sabotage"][iid]})
check("noise values pass the validator", True)

# Generated difficulty>=2 tickets carry noise beyond the template sabotage
_exclude = {t["id"] for t in SABOTAGE_TEMPLATES} - {"tpl_sata_mode"}
t_gen = generate_ticket(_random.Random(5), _exclude=_exclude)
check("generated d2 ticket has red herrings",
      len(set(t_gen["sabotage"]) - {"sata_mode"}) >= 1)

# Extended validator rejects bad data
try:
    game_mod._validate_constraint("bad", {
        "match": {"hd_audio": {">=": 3}}, "fail": {"lines": ["x"]}})
    check("validator rejects comparator on option", False)
except AssertionError:
    check("validator rejects comparator on option", True)
try:
    game_mod._validate_extras("bad", {"required_actions": ["solder_mod"]})
    check("validator rejects unknown action", False)
except AssertionError:
    check("validator rejects unknown action", True)

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
