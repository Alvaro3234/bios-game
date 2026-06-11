"""Challenge campaign: progress, sabotage arming, evaluation, game screens."""

import json
import os

import hardware_rules
import settings
from challenges import CHALLENGES
from menu_data import MENU
from menu_model import MenuModel, iter_persistable
from paths import writable
from renderer import word_wrap
from theme import (GRID_W, GRID_H, BLUE, WHITE, BLACK,
                   POST_BG, POST_FG, POST_HI)

PROGRESS_PATH = writable("progress.json")

ITEM_BY_ID = {it["id"]: it for it in iter_persistable()}

# Physical bench actions the player can perform from the briefing screen.
KNOWN_ACTIONS = {"replace_battery", "clear_cmos"}


def _validate_goal_dict(label, goal):
    for cid, v in goal.items():
        if cid == "_time_offset_s":
            assert isinstance(v, (int, float)), label
            continue
        item = ITEM_BY_ID.get(cid)
        assert item is not None, "%s: unknown id %r" % (label, cid)
        if item["type"] == "option" and v != "__nonempty__":
            wants = v if isinstance(v, list) else [v]
            for w in wants:
                assert w in item["values"], \
                    "%s: %r not in values of %r" % (label, w, cid)


def _validate_constraint(label, con):
    assert isinstance(con.get("match"), dict) and con["match"], \
        "%s: empty match" % label
    for part in ("match", "unless"):
        for cid, want in (con.get(part) or {}).items():
            item = ITEM_BY_ID.get(cid)
            assert item is not None, "%s: unknown id %r" % (label, cid)
            if isinstance(want, dict):
                assert item["type"] == "numeric", \
                    "%s: comparator on non-numeric %r" % (label, cid)
                assert set(want) <= {">=", "<="}, \
                    "%s: bad comparator in %r" % (label, cid)
            elif item["type"] == "option":
                wants = want if isinstance(want, list) else [want]
                for w in wants:
                    assert w in item["values"], \
                        "%s: %r not in values of %r" % (label, w, cid)
    fail = con.get("fail")
    assert isinstance(fail, dict) and fail.get("lines"), \
        "%s: constraint needs a fail dict with lines" % label


def _validate_extras(label, ch):
    for i, con in enumerate(ch.get("boot_constraints", [])):
        _validate_constraint("%s.boot_constraints[%d]" % (label, i), con)
    for key, entry in (ch.get("hw_info") or {}).items():
        if isinstance(entry, dict):
            assert entry.get("by") in ITEM_BY_ID, \
                "%s.hw_info[%r]: unknown by-id %r" % (label, key,
                                                      entry.get("by"))
    for act in ch.get("required_actions", []):
        assert act in KNOWN_ACTIONS, \
            "%s: unknown required action %r" % (label, act)
    for act in ch.get("bench", []):
        assert act in KNOWN_ACTIONS, \
            "%s: unknown bench action %r" % (label, act)
    # A required physical fix must be offered in the briefing toolbox.
    assert set(ch.get("required_actions", [])) <= set(ch.get("bench", [])), \
        "%s: required_actions not all available in bench" % label
    assert ch.get("hw_fault") in (None, "cmos_battery"), \
        "%s: unknown hw_fault %r" % (label, ch.get("hw_fault"))
    if ch.get("hw_fault") == "cmos_battery":
        assert "replace_battery" in ch.get("bench", []), \
            "%s: cmos_battery fault without replace_battery in bench" % label


def validate_challenges():
    """Data self-check: every sabotage/goal id+value must be valid.

    apply_saved drops invalid values silently, which would make a
    challenge silently unwinnable or trivially won.
    """
    for i, con in enumerate(hardware_rules.GLOBAL_CONSTRAINTS):
        _validate_constraint("GLOBAL_CONSTRAINTS[%d]" % i, con)
    for ch in CHALLENGES:
        _validate_goal_dict(ch["id"] + ".sabotage", ch.get("sabotage", {}))
        _validate_extras(ch["id"], ch)
        if ch.get("goal_phases"):
            for i, ph in enumerate(ch["goal_phases"]):
                _validate_goal_dict("%s.phase%d.goal" % (ch["id"], i),
                                    ph.get("goal", {}))
                _validate_goal_dict("%s.phase%d.next_sabotage"
                                    % (ch["id"], i),
                                    ph.get("next_sabotage", {}))
        else:
            _validate_goal_dict(ch["id"] + ".goal", ch.get("goal", {}))


class GameManager:
    def __init__(self, challenges=None, persist=True):
        """Default: campaign mode reads/writes progress.json.

        Pass `challenges` (a list with the same schema as CHALLENGES) to
        run a custom playlist — e.g. a procedurally generated shift.
        Set `persist=False` to keep progress in-memory only.
        """
        self.challenges = list(challenges) if challenges is not None else CHALLENGES
        self.persist = persist
        self.progress = {"level": 0, "attempts": 0,
                         "armed_for_level": -1, "phase": 0,
                         "hw_actions": []}
        if persist:
            try:
                with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.progress.update({k: data[k] for k in self.progress
                                          if isinstance(data.get(k), int)})
                    acts = data.get("hw_actions")
                    if isinstance(acts, list):
                        self.progress["hw_actions"] = [
                            a for a in acts if isinstance(a, str)]
            except (OSError, ValueError):
                pass

    # ------------------------------------------------------------ state
    @property
    def level(self):
        return self.progress["level"]

    @property
    def attempts(self):
        return self.progress["attempts"]

    @property
    def complete(self):
        return self.level >= len(self.challenges)

    def current(self):
        return self.challenges[self.level]

    def current_vendor(self):
        if self.complete:
            return "ami"
        return self.current().get("vendor", "ami")

    def current_cpu_brand(self):
        if self.complete:
            return "intel"
        return self.current().get("cpu_brand", "intel")

    @property
    def phase(self):
        return self.progress.get("phase", 0)

    def current_goal(self):
        """Active goal: the per-phase goal in multi-phase, else `goal`."""
        ch = self.current()
        phases = ch.get("goal_phases")
        if phases:
            i = min(self.phase, len(phases) - 1)
            return phases[i].get("goal", {})
        return ch.get("goal", {})

    def current_phase_info(self):
        """Return (phase_idx, total_phases, phase_dict) for the active phase.
        For single-phase challenges, total_phases is 1 and phase_dict is empty."""
        ch = self.current()
        phases = ch.get("goal_phases")
        if not phases:
            return 0, 1, {}
        i = min(self.phase, len(phases) - 1)
        return i, len(phases), phases[i]

    def has_more_phases(self):
        ch = self.current()
        phases = ch.get("goal_phases")
        return bool(phases) and self.phase < len(phases) - 1

    # ------------------------------------------------------------ bench
    def has_action(self, name):
        return name in self.progress.get("hw_actions", [])

    def perform_action(self, name):
        """Record a physical bench action (battery swap, CMOS clear)."""
        acts = self.progress.setdefault("hw_actions", [])
        if name not in acts:
            acts.append(name)
            self._save_progress()

    def advance_phase(self):
        """Move to the next phase: bump counter, inject next sabotage."""
        ch = self.current()
        phases = ch.get("goal_phases", [])
        self.progress["phase"] = self.phase + 1
        if self.progress["phase"] < len(phases):
            nxt = phases[self.progress["phase"]].get("next_sabotage")
            if nxt:
                vals = settings.load()
                vals.update(nxt)
                settings.save(vals)
        self._save_progress()

    def _save_progress(self):
        if not self.persist:
            return
        tmp = PROGRESS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2)
        os.replace(tmp, PROGRESS_PATH)

    def battery_dead(self):
        """A dead CMOS battery loses NVRAM contents on every power cycle
        until the player physically replaces it at the bench."""
        if self.complete:
            return False
        return (self.current().get("hw_fault") == "cmos_battery"
                and not self.has_action("replace_battery"))

    def ensure_machine_state(self):
        """First attempt of a level: write defaults+sabotage to settings.
        Retries keep whatever the player last saved — unless the CMOS
        battery is dead, in which case the saved fixes evaporate on
        every boot."""
        if self.complete:
            return
        if self.battery_dead() or self.progress["armed_for_level"] != self.level:
            model = MenuModel(self.current_cpu_brand())
            values = model.export_values()
            values.update(self.current()["sabotage"])
            settings.save(values)
            self.progress["armed_for_level"] = self.level
            self._save_progress()

    # ------------------------------------------------------------ rules
    def evaluate(self):
        """Bool-only contract kept for callers that don't need fail info."""
        return self.evaluate_full()[0]

    def evaluate_full(self):
        """Check the persisted machine state against the current goal.

        Returns (success, fail_info): fail_info is the `fail` dict of a
        violated boot constraint (board limits or ticket-specific), or
        None — in which case the ticket's scripted `fail` applies.
        """
        model = MenuModel(self.current_cpu_brand())
        model.apply_saved(settings.load())
        ch = self.current()

        # A settings combination the board can't boot with trumps the goal.
        fail = hardware_rules.check_constraints(
            model, ch.get("boot_constraints"))
        if fail:
            return False, fail

        # Physical faults must have been fixed at the bench.
        for act in ch.get("required_actions", []):
            if not self.has_action(act):
                return False, None

        goal = self.current_goal()
        for cid, want in goal.items():
            item = ITEM_BY_ID[cid]
            if not model.is_enabled(item):   # grayed = not effective
                return False, None
            v = model.values.get(cid)
            if want == "__nonempty__":
                ok = bool(v)
            elif isinstance(want, list):
                ok = v in want
            else:
                ok = v == want
            if not ok:
                return False, None
        # Time offset only checked on the final phase
        if not self.has_more_phases():
            goff = ch.get("goal_offset")
            if goff:
                limit = goff["max_abs_days"] * 86400
                if abs(model.time_offset.total_seconds()) > limit:
                    return False, None
        return True, None

    def post_context(self):
        """Per-ticket POST context consumed by PostScreen.reset()."""
        if self.complete:
            return {}
        ch = self.current()
        ctx = {}
        pv = ch.get("post_variant")
        if pv:
            # A variant can clear itself once a bench action is performed
            # (e.g. no_video until the CMOS is cleared).
            until = pv.get("until_action")
            if not (until and self.has_action(until)):
                ctx.update({k: v for k, v in pv.items()
                            if k != "until_action"})
        if ch.get("post_code_hint"):
            ctx["post_code"] = ch["post_code_hint"]
        if ch.get("post_extra_lines"):
            ctx["extra_lines"] = list(ch["post_extra_lines"])
        if self.battery_dead():
            ctx["extra_lines"] = list(ctx.get("extra_lines", [])) + list(
                ch.get("cmos_checksum_lines",
                       [(3450, "CMOS checksum error - Defaults loaded"),
                        (3560, "Warning: CMOS battery voltage low")]))
        return ctx

    def record_failure(self):
        self.progress["attempts"] += 1
        self._save_progress()

    def advance(self):
        self.progress["level"] += 1
        self.progress["attempts"] = 0
        self.progress["phase"] = 0
        self.progress["hw_actions"] = []   # next ticket = new machine
        self._save_progress()

    def reset(self):
        self.progress = {"level": 0, "attempts": 0,
                         "armed_for_level": -1, "phase": 0,
                         "hw_actions": []}
        self._save_progress()

    def visible_hints(self):
        ch = self.current()
        return ch["hints"][:min(self.attempts, len(ch["hints"]))]

    # ------------------------------------------------------------ screens
    def draw_briefing(self, buf, now):
        ch = self.current()
        advanced = ch.get("tier") == "advanced"
        buf.clear(POST_FG, POST_BG)
        header = ("BIOS REPAIR SERVICE - SENIOR TECHNICIAN" if advanced
                  else "BIOS REPAIR SERVICE")
        buf.text(2, 1, header, POST_FG, POST_BG)
        tag = "LEVEL %d/%d" % (self.level + 1, len(self.challenges))
        phase_idx, total_phases, phase = self.current_phase_info()
        if total_phases > 1:
            tag += "  PHASE %d/%d" % (phase_idx + 1, total_phases)
        buf.text(GRID_W - 2 - len(tag), 1, tag, POST_FG, POST_BG)

        # Ticket box
        x0, x1 = 4, GRID_W - 5
        inner = x1 - x0 - 5
        lines = []
        for para in ch["briefing"]:
            lines.extend(word_wrap(para, inner) if para else [""])
        addendum = phase.get("phase_briefing_addendum") if phase else None
        if addendum:
            lines.append("")
            for para in addendum:
                lines.extend(word_wrap(para, inner) if para else [""])
        hints = self.visible_hints()
        if hints:
            lines.append("")
            for i, hint in enumerate(hints):
                for hl in word_wrap("HINT %d: %s" % (i + 1, hint), inner):
                    lines.append(("hint", hl))
        elif advanced and self.attempts:
            lines.append("")
            lines.append(("hint", "(Senior tier: no hints available. "
                                  "Figure it out.)"))
        h = min(len(lines) + 4, GRID_H - 7)
        buf.box(x0, 3, x1 - x0 + 1, h, WHITE, POST_BG, fill=False)
        title = " %s " % ch["title"].upper()
        buf.text(x0 + (x1 - x0 + 1 - len(title)) // 2, 3, title,
                 POST_HI, POST_BG)
        for i, line in enumerate(lines[:h - 4]):
            if isinstance(line, tuple):
                buf.text(x0 + 3, 5 + i, line[1], POST_HI, POST_BG)
            else:
                buf.text(x0 + 3, 5 + i, line, POST_FG, POST_BG)

        if self.attempts:
            buf.text(x0, 4 + h, "Failed attempts: %d" % self.attempts,
                     POST_FG, POST_BG)
        self._draw_toolbox(buf, ch, x0, h)
        if (now // 530) % 2 == 0:
            buf.text_center(GRID_H - 2,
                            "Press any key to power on the machine",
                            POST_HI, POST_BG)

    _TOOLBOX_LABELS = {
        "replace_battery": "B: replace the CMOS battery (CR2032)",
        "clear_cmos": "J: short the CLR_CMOS jumper (reset NVRAM)",
    }
    _TOOLBOX_DONE = {
        "replace_battery": "battery replaced, fresh CR2032 installed",
        "clear_cmos": "NVRAM cleared to factory defaults",
    }

    def _draw_toolbox(self, buf, ch, x0, h):
        bench = ch.get("bench", [])
        if not bench:
            return
        y = 5 + h
        buf.text(x0, y, "TOOLBOX (bench actions):", POST_HI, POST_BG)
        for i, act in enumerate(bench):
            line = "  " + self._TOOLBOX_LABELS.get(act, act)
            if self.has_action(act):
                line += "   [done: %s]" % self._TOOLBOX_DONE.get(act, "ok")
            buf.text(x0, y + 1 + i, line, POST_FG, POST_BG)

    def draw_outcome(self, buf, success, now, fail_info=None):
        ch = self.current()
        if success:
            self._draw_console(buf, ch["success_lines"])
            self._banner(buf, "CHALLENGE COMPLETE",
                         "Press any key to continue", now)
            return
        fail = fail_info or ch["fail"]
        style = fail["style"]
        lines = fail["lines"]
        if style == "bsod":
            buf.clear(WHITE, BLUE)
            buf.text(4, 3, ":(", WHITE, BLUE)
            for i, line in enumerate(lines):
                buf.text(4, 6 + i, line, WHITE, BLUE)
            self._banner(buf, "PROBLEM NOT SOLVED",
                         "Press any key to try again", now, bg=BLUE)
        elif style == "secureboot":
            buf.clear(POST_FG, POST_BG)
            w = max(len(l) for l in lines) + 8
            h = len(lines) + 4
            x = (GRID_W - w) // 2
            y = (GRID_H - h) // 2 - 2
            buf.box(x, y, w, h, WHITE, POST_BG, fill=False)
            for i, line in enumerate(lines):
                buf.text(x + 4, y + 2 + i,
                         line, POST_HI if i == 0 else POST_FG, POST_BG)
            self._banner(buf, "PROBLEM NOT SOLVED",
                         "Press any key to try again", now)
        elif style == "memtrain":
            self._draw_console(buf, lines)
            dots = "." * (1 + (now // 400) % 3)
            buf.text(2, 3 + len(lines), "MRC: memory training" + dots,
                     POST_FG, POST_BG)
            self._post_code(buf, fail)
            self._banner(buf, "PROBLEM NOT SOLVED",
                         "Press any key to try again", now)
        elif style == "thermtrip":
            buf.clear(POST_FG, POST_BG)
            for i, line in enumerate(lines):
                hot = "Error" in line or line.startswith("Press F1")
                buf.text(2, 2 + i, line,
                         POST_HI if hot else POST_FG, POST_BG)
            self._post_code(buf, fail)
            self._banner(buf, "PROBLEM NOT SOLVED",
                         "Press any key to try again", now)
        else:
            self._draw_console(buf, lines)
            self._post_code(buf, fail)
            self._banner(buf, "PROBLEM NOT SOLVED",
                         "Press any key to try again", now)

    def _draw_console(self, buf, lines):
        buf.clear(POST_FG, POST_BG)
        for i, line in enumerate(lines):
            buf.text(2, 2 + i, line, POST_FG, POST_BG)

    def _post_code(self, buf, fail):
        code = fail.get("post_code")
        if code:
            buf.text(GRID_W - 3, GRID_H - 1, code, POST_HI, POST_BG)

    def _banner(self, buf, title, prompt, now, bg=POST_BG):
        fg = WHITE
        y = GRID_H - 6
        w = max(len(title), len(prompt)) + 10
        x = (GRID_W - w) // 2
        buf.box(x, y, w, 4, fg, bg, fill=False)
        buf.text(x + (w - len(title)) // 2, y + 1, title, fg, bg)
        if (now // 530) % 2 == 0:
            buf.text(x + (w - len(prompt)) // 2, y + 2, prompt, fg, bg)

    def draw_win(self, buf, now):
        buf.clear(POST_FG, POST_BG)
        lines = [
            "CAMPAIGN COMPLETE",
            "",
            "You repaired all %d machines." % len(self.challenges),
            "The help desk queue is empty. For now...",
            "",
            "R: play again        ESC: exit",
        ]
        w = max(len(l) for l in lines) + 12
        h = len(lines) + 4
        x = (GRID_W - w) // 2
        y = (GRID_H - h) // 2
        buf.box(x, y, w, h, WHITE, POST_BG, fill=False)
        for i, line in enumerate(lines):
            fg = POST_HI if i == 0 else POST_FG
            buf.text(x + (w - len(line)) // 2, y + 2 + i, line, fg, POST_BG)
