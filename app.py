"""Application state machine: POST -> SETUP (popups/dialogs) -> REBOOT -> POST."""

import os

import pygame

import settings
import vendors
from menu_model import MenuModel
from post_screen import PostScreen
from theme import BLACK

POST, SETUP, REBOOT = "post", "setup", "reboot"
BRIEFING, OUTCOME, WIN = "briefing", "outcome", "win"
SETUP_SHELL = "setup_shell"
MAIN_MENU = "main_menu"
ENDLESS_PROMPT = "endless_prompt"
OPTIONS = "options"
CONFIRM = "confirm"
REBOOT_MS = 1200


def _progress_path():
    from game import PROGRESS_PATH
    return PROGRESS_PATH

_PLUS_KEYS = (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS)
_MINUS_KEYS = (pygame.K_MINUS, pygame.K_KP_MINUS)


class App:
    def __init__(self, game=None, audio=None, start_in_menu=False):
        self.state = POST
        self.game = game           # GameManager in challenge mode, else None
        self.audio = audio         # Audio() or None (silent)
        self.post = PostScreen()
        self.model = None
        self.shell = None          # ShellSession when vendor == "efi"
        self.popup = None          # active popup/dialog dict, or None
        self.outcome = None        # bool, set when entering OUTCOME
        self.reboot_t0 = 0
        self.running = True
        self._last_outcome_jingled = None
        self._last_post_beeped = False
        # Pre-game UI helpers (lazily attached when entering the menu)
        self.menu = None
        self.endless_prompt = None
        self.options = None
        self.confirm = None
        self._start_in_menu = start_in_menu

    # ------------------------------------------------------------ lifecycle
    def start(self, now):
        if self._start_in_menu:
            self._enter_main_menu()
            return
        if self.game:
            if self.game.complete:
                self.state = WIN
            else:
                self.game.ensure_machine_state()
                self.state = BRIEFING
        else:
            self.post.reset(now)

    def _enter_main_menu(self):
        from menu_screen import MainMenu
        self.menu = MainMenu()
        self.state = MAIN_MENU

    def _start_campaign(self, now):
        from game import GameManager
        self.game = GameManager()
        if self.game.complete:
            self.state = WIN
        else:
            self.game.ensure_machine_state()
            self.state = BRIEFING

    def _start_endless(self, seed, n, now):
        from game import GameManager
        from procedural import generate_shift
        tickets = generate_shift(seed=seed, n=n)
        self.game = GameManager(challenges=tickets, persist=False)
        self.game.ensure_machine_state()
        self.state = BRIEFING

    def enter_setup(self):
        cpu_brand = self.game.current_cpu_brand() if self.game else "intel"
        vendor_id = self.game.current_vendor() if self.game else "ami"
        self.model = MenuModel(cpu_brand)
        self.model.apply_saved(settings.load())
        self.model.snapshot()
        self.popup = None
        if vendor_id == "efi":
            from shell import ShellSession
            self.shell = ShellSession(self.model)
            self.state = SETUP_SHELL
        else:
            self.shell = None
            self.state = SETUP

    def reboot(self, now):
        self.state = REBOOT
        self.reboot_t0 = now
        self.popup = None

    # ------------------------------------------------------------ update
    def update(self, now):
        if self.state == REBOOT and now - self.reboot_t0 >= REBOOT_MS:
            if self.game:
                self.outcome = self.game.evaluate()
                self.state = OUTCOME
                if self.audio and self._last_outcome_jingled is not now:
                    self.audio.jingle("success" if self.outcome else "fail")
                    self._last_outcome_jingled = now
            else:
                self.state = POST
                self.post.reset(now)
        elif self.state == POST and self.audio and not self._last_post_beeped:
            # Play the vendor OK beep once when POST has finished its memory
            # count (~2400 ms in). Cheap heuristic: triggered after 2400ms.
            if now - getattr(self.post, "t0", now) > 2400:
                v = self._vendor()
                pattern = v.get("beep_map", {}).get("ok") or []
                if pattern:
                    self.audio.beep_pattern(pattern)
                self._last_post_beeped = True
        elif self.state != POST:
            self._last_post_beeped = False

    # ------------------------------------------------------------ input
    def handle_key(self, event, now):
        if self.audio and self.state in (SETUP, SETUP_SHELL):
            self.audio.click()
        if self.state in (MAIN_MENU, ENDLESS_PROMPT, OPTIONS, CONFIRM):
            self._menu_key(event, now)
            return
        if self.state == POST:
            if self.post.handle_key(event.key) == "setup":
                self.enter_setup()
        elif self.state == SETUP:
            if self.popup:
                self._popup_key(event, now)
            else:
                self._setup_key(event, now)
        elif self.state == SETUP_SHELL:
            self._shell_key(event, now)
        elif self.state == BRIEFING:
            self.state = POST
            self.post.reset(now)
        elif self.state == OUTCOME:
            if self.outcome:
                if self.game.has_more_phases():
                    self.game.advance_phase()
                    # Re-enter briefing for the next phase. The model
                    # already carries the player's last save, so we just
                    # show the addendum and bounce them through POST again.
                    self.state = BRIEFING
                    return
                self.game.advance()
                if self.game.complete:
                    self.state = WIN
                    return
            else:
                self.game.record_failure()
            self.game.ensure_machine_state()
            self.state = BRIEFING
        elif self.state == WIN:
            if event.key == pygame.K_r:
                self.game.reset()
                self.game.ensure_machine_state()
                self.state = BRIEFING
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False

    def _setup_key(self, event, now):
        m = self.model
        key = event.key
        item = m.current_item()

        if key == pygame.K_UP:
            m.move(-1)
        elif key == pygame.K_DOWN:
            m.move(1)
        elif key == pygame.K_LEFT and not m.in_submenu:
            m.switch_page(-1)
        elif key == pygame.K_RIGHT and not m.in_submenu:
            m.switch_page(1)
        elif key == pygame.K_TAB and item and item["type"] == "datetime":
            m.dt_field = (m.dt_field + 1) % 3
        elif key in _PLUS_KEYS and item:
            m.change(item, 1)
        elif key in _MINUS_KEYS and item:
            m.change(item, -1)
        elif key == pygame.K_RETURN and item:
            self._activate(item, now)
        elif key == pygame.K_ESCAPE:
            if not m.leave_submenu():
                self._dialog("Exit Without Saving",
                             ["Quit without saving?"],
                             lambda: (m.restore_snapshot(), self.reboot(now)))
        elif key == pygame.K_F1:
            self.popup = {"kind": "help"}
        elif key == pygame.K_F2:
            self._dialog("Load Previous Values",
                         ["Load Previous Values?"],
                         m.restore_snapshot)
        elif key == pygame.K_F9:
            self._dialog("Load Optimized Defaults",
                         ["Load Optimized Defaults?"],
                         m.load_defaults)
        elif key == pygame.K_F10:
            self._dialog("Save & Exit Setup",
                         ["Save configuration and exit?"],
                         lambda: self._save_and(lambda: self.reboot(now)))

    def _activate(self, item, now):
        t = item["type"]
        if t == "submenu":
            self.model.enter_submenu(item)
        elif t == "option":
            sel = item["values"].index(self.model.values[item["id"]])
            self.popup = {"kind": "option", "item": item, "sel": sel}
        elif t == "numeric":
            self.popup = {"kind": "text", "item": item, "buffer": "",
                          "masked": False, "numeric": True,
                          "title": item["label"]}
        elif t == "password":
            self.popup = {"kind": "text", "item": item, "buffer": "",
                          "masked": True, "numeric": False,
                          "title": "Create New Password"}
        elif t == "action":
            self._run_action(item, now)

    def _run_action(self, item, now):
        m, action = self.model, item["action"]
        if action in ("save_exit", "save_reset"):
            self._dialog("Save & Exit Setup",
                         ["Save configuration and exit?"],
                         lambda: self._save_and(lambda: self.reboot(now)))
        elif action == "discard_exit":
            self._dialog("Exit Without Saving",
                         ["Quit without saving?"],
                         lambda: (m.restore_snapshot(), self.reboot(now)))
        elif action == "discard_changes":
            self._dialog("Load Previous Values",
                         ["Load Previous Values?"], m.restore_snapshot)
        elif action == "load_defaults":
            self._dialog("Load Optimized Defaults",
                         ["Load Optimized Defaults?"], m.load_defaults)
        elif action == "save_user_defaults":
            self._dialog("Save Values as User Defaults",
                         ["Save configuration?"],
                         lambda: settings.save(m.values,
                                               settings.USER_DEFAULTS_PATH))
        elif action == "restore_user_defaults":
            self._dialog("Restore User Defaults",
                         ["Restore User Defaults?"],
                         lambda: m.apply_saved(
                             settings.load(settings.USER_DEFAULTS_PATH)))
        elif action == "factory_keys":
            self._dialog("Restore Factory Keys",
                         ["Install factory default Secure Boot",
                          "key databases?"], lambda: None)
        elif action == "clear_keys":
            self._dialog("Reset To Setup Mode",
                         ["Delete all Secure Boot key databases",
                          "from NVRAM?"], lambda: None)
        elif action == "boot_override":
            self.reboot(now)

    def _save_and(self, then):
        settings.save(self.model.export_values())
        self.model.snapshot()
        then()

    def _menu_key(self, event, now):
        key = event.key
        if self.state == MAIN_MENU:
            if key == pygame.K_UP:
                self.menu.move(-1)
            elif key == pygame.K_DOWN:
                self.menu.move(1)
            elif key == pygame.K_RETURN:
                self._main_menu_activate(now)
            elif key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False
        elif self.state == ENDLESS_PROMPT:
            if key == pygame.K_UP:
                self.endless_prompt.move(-1)
            elif key == pygame.K_DOWN:
                self.endless_prompt.move(1)
            elif key == pygame.K_RETURN:
                action = self.endless_prompt.activate()
                if action == "start":
                    seed = self.endless_prompt.picked_seed()
                    n = self.endless_prompt.size
                    self._start_endless(seed, n, now)
                elif action == "back":
                    self._enter_main_menu()
            elif key == pygame.K_ESCAPE:
                self._enter_main_menu()
        elif self.state == OPTIONS:
            if key == pygame.K_UP:
                self.options.move(-1)
            elif key == pygame.K_DOWN:
                self.options.move(1)
            elif key == pygame.K_RETURN:
                action = self.options.activate()
                if action == "reset":
                    from menu_screen import ConfirmDialog
                    self.confirm = ConfirmDialog(
                        "Reset Campaign Progress",
                        ["Erase progress.json and start from level 1?",
                         "This cannot be undone."],
                        self._do_reset_progress)
                    self.state = CONFIRM
                elif action == "back":
                    self._enter_main_menu()
            elif key == pygame.K_ESCAPE:
                self._enter_main_menu()
            # Reflect any audio toggle change live
            if self.audio:
                self.audio.enabled = (self.options.audio
                                      and self.audio.enabled
                                      or self.options.audio
                                      and not self.audio.enabled
                                      and False)
        elif self.state == CONFIRM:
            if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                self.confirm.move(1)
            elif key == pygame.K_RETURN:
                outcome = self.confirm.activate()
                self.confirm = None
                if outcome == "back":
                    self.state = OPTIONS
            elif key == pygame.K_ESCAPE:
                self.confirm = None
                self.state = OPTIONS

    def _main_menu_activate(self, now):
        from menu_screen import EndlessPrompt, OptionsMenu
        choice = self.menu.chosen()
        if choice == "challenge":
            self._start_campaign(now)
        elif choice == "endless":
            self.endless_prompt = EndlessPrompt()
            self.state = ENDLESS_PROMPT
        elif choice == "options":
            self.options = OptionsMenu()
            self.state = OPTIONS
        elif choice == "quit":
            self.running = False

    def _do_reset_progress(self):
        # Wipe progress.json (settings stay so options aren't lost).
        try:
            from game import PROGRESS_PATH
            if os.path.exists(PROGRESS_PATH):
                os.remove(PROGRESS_PATH)
        except (OSError, ImportError):
            pass

    def _shell_key(self, event, now):
        sh = self.shell
        key = event.key
        if key == pygame.K_RETURN:
            sh.submit()
            if sh.wants_reboot:
                if sh.discard_on_reboot:
                    self.model.restore_snapshot()
                settings.save(self.model.export_values())
                self.model.snapshot()
                self.reboot(now)
        elif key == pygame.K_BACKSPACE:
            sh.backspace()
        elif key == pygame.K_UP:
            sh.history_prev()
        elif key == pygame.K_DOWN:
            sh.history_next()
        elif key == pygame.K_ESCAPE:
            sh.println("Use 'exit' to quit the shell, or 'reset cold' to save.")
        elif event.unicode:
            sh.handle_char(event.unicode)

    def _dialog(self, title, lines, on_yes):
        self.popup = {"kind": "dialog", "title": title, "lines": lines,
                      "buttons": ["Yes", "No"], "sel": 0, "on_yes": on_yes}

    # ------------------------------------------------------------ popups
    def _popup_key(self, event, now):
        p, key = self.popup, event.key
        kind = p["kind"]

        if kind == "help":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_F1):
                self.popup = None

        elif kind == "option":
            n = len(p["item"]["values"])
            if key in (pygame.K_UP,) + _MINUS_KEYS:
                p["sel"] = (p["sel"] - 1) % n
            elif key in (pygame.K_DOWN,) + _PLUS_KEYS:
                p["sel"] = (p["sel"] + 1) % n
            elif key == pygame.K_RETURN:
                self.model.set_option_index(p["item"], p["sel"])
                self.popup = None
            elif key == pygame.K_ESCAPE:
                self.popup = None

        elif kind == "dialog":
            n = len(p["buttons"])
            if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                p["sel"] = (p["sel"] + 1) % n
            elif key == pygame.K_RETURN:
                on_yes = p["on_yes"] if p["buttons"][p["sel"]] == "Yes" else None
                self.popup = None
                if on_yes:
                    on_yes()
            elif key == pygame.K_ESCAPE:
                self.popup = None

        elif kind == "text":
            if key == pygame.K_RETURN:
                item = p["item"]
                if p["numeric"]:
                    if p["buffer"]:
                        lo, hi = item.get("min", 0), item.get("max", 1 << 30)
                        self.model.values[item["id"]] = max(
                            lo, min(hi, int(p["buffer"])))
                else:
                    self.model.values[item["id"]] = p["buffer"]
                self.popup = None
            elif key == pygame.K_ESCAPE:
                self.popup = None
            elif key == pygame.K_BACKSPACE:
                p["buffer"] = p["buffer"][:-1]
            elif event.unicode and event.unicode.isprintable():
                if p["numeric"] and not event.unicode.isdigit():
                    return
                if len(p["buffer"]) < 20:
                    p["buffer"] += event.unicode

    # ------------------------------------------------------------ render
    def _vendor(self):
        vid = self.game.current_vendor() if self.game else "ami"
        return vendors.get(vid)

    def _draw_shift_hud(self, buf, now):
        """Tiny ticker for shift mode: ticket N/total + attempts."""
        if not (self.game and not self.game.persist):
            return
        from theme import GRID_W, GRID_H, WHITE, BLUE
        tag = "SHIFT  Ticket %d/%d  Attempts: %d" % (
            self.game.level + 1, len(self.game.challenges),
            self.game.attempts)
        buf.text(GRID_W - 2 - len(tag), GRID_H - 1, tag, WHITE, BLUE)

    def draw(self, buf, now):
        if self.state == MAIN_MENU:
            has_progress = os.path.exists(_progress_path())
            self.menu.draw(buf, now, has_progress=has_progress)
            return
        if self.state == ENDLESS_PROMPT:
            self.endless_prompt.draw(buf, now)
            return
        if self.state == OPTIONS:
            self.options.draw(buf, now)
            return
        if self.state == CONFIRM:
            self.confirm.draw(buf, now)
            return
        if self.state == POST:
            self.post.draw(buf, now)
        elif self.state == REBOOT:
            buf.clear(BLACK, BLACK)
        elif self.state == BRIEFING:
            self.game.draw_briefing(buf, now)
        elif self.state == OUTCOME:
            self.game.draw_outcome(buf, self.outcome, now)
        elif self.state == WIN:
            self.game.draw_win(buf, now)
        elif self.state == SETUP_SHELL:
            v = self._vendor()
            self.shell.cursor_visible = (now // 530) % 2 == 0
            v["draw_setup_shell"](buf, self.shell)
        else:
            v = self._vendor()
            v["draw_setup"](buf, self.model)
            self._draw_shift_hud(buf, now)
            p = self.popup
            if p:
                if p["kind"] == "option":
                    v["draw_option_popup"](buf, p["item"], p["sel"],
                                            model=self.model)
                elif p["kind"] == "dialog":
                    v["draw_dialog"](buf, p["title"], p["lines"],
                                     p["buttons"], p["sel"])
                elif p["kind"] == "text":
                    v["draw_text_popup"](buf, p["title"], p["buffer"],
                                          p["masked"])
                elif p["kind"] == "help":
                    v["draw_help_popup"](buf)
