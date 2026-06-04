"""Audio: synthesized POST beeps, key clicks, and outcome jingles.

All tones are generated on the fly with numpy + pygame.sndarray — no
WAV assets to manage. Designed to be safe in headless CI:

- If `enabled=False`, every method is a silent no-op.
- If pygame.mixer.init fails (no audio device in CI), we auto-disable.
- Sounds are cached by (freq, ms) so repeated beeps are cheap.

Vendor specs supply `beep_map`: keys "ok", "memory_fail", "video_fail"
each mapping to a list of (freq_hz, duration_ms) tuples played in sequence.
"""

import os


def _audio_should_disable():
    """Auto-disable in headless / dummy-driver environments."""
    return os.environ.get("SDL_AUDIODRIVER", "").lower() == "dummy"


class Audio:
    SAMPLE_RATE = 22050

    def __init__(self, enabled=True):
        self.enabled = enabled and not _audio_should_disable()
        self._cache = {}
        self._np = None
        if not self.enabled:
            return
        try:
            import numpy as np
            self._np = np
        except ImportError:
            self.enabled = False
            return
        try:
            import pygame
            pygame.mixer.pre_init(self.SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.init()
        except Exception:
            self.enabled = False
            return
        self._pygame = pygame

    def _tone(self, freq, ms):
        if not self.enabled:
            return None
        key = (int(freq), int(ms))
        if key in self._cache:
            return self._cache[key]
        np = self._np
        n = int(self.SAMPLE_RATE * ms / 1000)
        if n <= 0:
            return None
        t = np.arange(n, dtype=np.float32) / self.SAMPLE_RATE
        wave = np.sign(np.sin(2 * np.pi * freq * t))
        # 5 ms fade in/out to avoid clicks
        fade = max(1, int(self.SAMPLE_RATE * 0.005))
        if fade * 2 < n:
            wave[:fade] *= np.linspace(0.0, 1.0, fade)
            wave[-fade:] *= np.linspace(1.0, 0.0, fade)
        wave = (wave * 0.3 * 32767).astype(np.int16)
        try:
            snd = self._pygame.sndarray.make_sound(wave)
        except Exception:
            self.enabled = False
            return None
        self._cache[key] = snd
        return snd

    def beep(self, freq, ms):
        snd = self._tone(freq, ms)
        if snd is not None:
            snd.play()

    def beep_pattern(self, pattern, gap_ms=100):
        """Sequence of (freq, ms) tuples. Plays serially via timer schedule.

        Pygame doesn't queue cleanly across Sound objects, so we play the
        first beep immediately and rely on the duration to space them.
        For our short sequences (2-4 beeps), this is acceptable.
        """
        if not self.enabled or not pattern:
            return
        # Concatenate into one buffer for accurate timing.
        np = self._np
        pieces = []
        gap_samples = int(self.SAMPLE_RATE * gap_ms / 1000)
        silence = np.zeros(gap_samples, dtype=np.float32)
        for freq, ms in pattern:
            n = int(self.SAMPLE_RATE * ms / 1000)
            if n <= 0:
                continue
            t = np.arange(n, dtype=np.float32) / self.SAMPLE_RATE
            w = np.sign(np.sin(2 * np.pi * freq * t))
            fade = max(1, int(self.SAMPLE_RATE * 0.005))
            if fade * 2 < n:
                w[:fade] *= np.linspace(0.0, 1.0, fade)
                w[-fade:] *= np.linspace(1.0, 0.0, fade)
            pieces.append(w)
            pieces.append(silence)
        if not pieces:
            return
        full = np.concatenate(pieces) * 0.3 * 32767
        wave = full.astype(np.int16)
        try:
            self._pygame.sndarray.make_sound(wave).play()
        except Exception:
            self.enabled = False

    def click(self):
        # Short 8ms square at 1200Hz, fairly quiet
        snd = self._tone(1200, 8)
        if snd is not None:
            snd.set_volume(0.4)
            snd.play()

    def jingle(self, kind):
        if not self.enabled:
            return
        if kind == "success":
            self.beep_pattern([(660, 80), (880, 80), (1320, 160)], gap_ms=30)
        elif kind == "fail":
            self.beep_pattern([(440, 120), (220, 280)], gap_ms=20)
