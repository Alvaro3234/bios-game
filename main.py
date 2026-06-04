"""UEFI BIOS simulator (AMI Aptio Setup Utility look-alike).

Run:            python main.py
Keys:           DEL/F2 enter setup, arrows/Enter/ESC/+/-/F1/F2/F9/F10 in setup,
                F11 fullscreen, F12 screenshot.
Screenshot mode (headless, for testing):
                python main.py --screenshot out.png [--screen post|setup]
"""

import argparse
import os
import sys

# Window placement before pygame.init
os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

import pygame  # noqa: E402

from theme import NATIVE_W, NATIVE_H, BLACK  # noqa: E402


def compute_blit(window_size):
    """Largest aspect-preserving rect (integer-scaled when possible)."""
    ww, wh = window_size
    scale = min(ww / NATIVE_W, wh / NATIVE_H)
    if scale >= 1:
        scale = int(scale)
    w, h = int(NATIVE_W * scale), int(NATIVE_H * scale)
    return pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)


_SCANLINE_CACHE = {}


def make_scanline_overlay(size):
    """Translucent horizontal-line overlay sized to `size`."""
    if size in _SCANLINE_CACHE:
        return _SCANLINE_CACHE[size]
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # One dim line every 2 rows
    for y in range(0, h, 2):
        pygame.draw.line(surf, (0, 0, 0, 80), (0, y), (w, y))
    _SCANLINE_CACHE[size] = surf
    return surf


def run_screenshot(path, screen_name, level=0):
    """Render one frame headlessly and save it (used for verification)."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((1, 1))

    from app import App
    from renderer import Renderer
    from screen import ScreenBuffer

    buf = ScreenBuffer()
    if screen_name in ("briefing", "fail", "success", "win"):
        # Draw game screens directly (no progress/settings side effects)
        from game import GameManager
        gm = GameManager()
        gm.progress = {"level": level, "attempts": 0, "armed_for_level": -1}
        if screen_name == "briefing":
            gm.draw_briefing(buf, 0)
        elif screen_name == "win":
            gm.draw_win(buf, 0)
        else:
            gm.draw_outcome(buf, screen_name == "success", 0)
    else:
        app = App()
        app.start(0)
        if screen_name == "setup":
            app.enter_setup()
            now = 0
        else:
            now = 10_000  # POST timeline fully revealed, prompt visible
        app.draw(buf, now)

    surface = Renderer().render(buf)
    out = pygame.transform.scale(surface, (NATIVE_W * 2, NATIVE_H * 2))
    pygame.image.save(out, path)
    print("saved", path)


def run(freeplay=False, shift_seed=None, shift_n=5, menu=False):
    pygame.init()
    pygame.display.set_caption("Aptio Setup Utility")
    window = pygame.display.set_mode((NATIVE_W * 2, NATIVE_H * 2),
                                     pygame.RESIZABLE)

    from app import App
    from renderer import Renderer
    from screen import ScreenBuffer

    from audio import Audio
    import settings as _settings
    audio_enabled = bool(_settings.load().get("_audio", True))
    audio = Audio(enabled=audio_enabled)

    if menu:
        app = App(audio=audio, start_in_menu=True)
    elif freeplay:
        app = App(audio=audio)
    elif shift_seed is not None:
        from game import GameManager
        from procedural import generate_shift
        tickets = generate_shift(seed=shift_seed, n=shift_n)
        app = App(game=GameManager(challenges=tickets, persist=False),
                  audio=audio)
    else:
        from game import GameManager
        app = App(game=GameManager(), audio=audio)
    app.start(pygame.time.get_ticks())
    rend = Renderer()
    buf = ScreenBuffer()
    clock = pygame.time.Clock()
    fullscreen = False

    # CRT scanlines toggle, persisted in settings.json under _scanlines
    import settings as _settings
    _saved = _settings.load()
    scanlines = bool(_saved.get("_scanlines", False))

    while app.running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        window = pygame.display.set_mode(
                            (0, 0), pygame.FULLSCREEN)
                    else:
                        window = pygame.display.set_mode(
                            (NATIVE_W * 2, NATIVE_H * 2), pygame.RESIZABLE)
                elif event.key == pygame.K_F12:
                    shot = pygame.transform.scale(
                        rend.render(buf), (NATIVE_W * 2, NATIVE_H * 2))
                    path = os.path.join(os.path.dirname(__file__),
                                        "screenshot.png")
                    pygame.image.save(shot, path)
                elif event.key == pygame.K_F8:
                    scanlines = not scanlines
                    cur = _settings.load()
                    cur["_scanlines"] = scanlines
                    _settings.save(cur)
                else:
                    app.handle_key(event, now)

        app.update(now)
        app.draw(buf, now)
        frame = rend.render(buf)

        window.fill(BLACK)
        dst = compute_blit(window.get_size())
        if dst.size == (NATIVE_W, NATIVE_H):
            window.blit(frame, dst)
        else:
            window.blit(pygame.transform.scale(frame, dst.size), dst)
        if scanlines:
            window.blit(make_scanline_overlay(dst.size), dst.topleft)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", metavar="PATH",
                        help="render one frame headlessly to PATH and exit")
    parser.add_argument("--screen",
                        choices=["post", "setup", "briefing", "fail",
                                 "success", "win"],
                        default="setup")
    parser.add_argument("--level", type=int, default=0,
                        help="challenge index for game-screen screenshots")
    parser.add_argument("--freeplay", action="store_true",
                        help="sandbox mode without challenges")
    parser.add_argument("--shift", type=int, metavar="SEED",
                        help="play a procedurally generated shift")
    parser.add_argument("--shift-n", type=int, default=5,
                        help="number of tickets per shift (default 5)")
    parser.add_argument("--no-menu", action="store_true",
                        help="skip the main menu and resume the campaign")
    args = parser.parse_args()
    if args.screenshot:
        run_screenshot(args.screenshot, args.screen, args.level)
        sys.exit(0)
    show_menu = not (args.freeplay or args.shift is not None or args.no_menu)
    run(freeplay=args.freeplay, shift_seed=args.shift, shift_n=args.shift_n,
        menu=show_menu)
