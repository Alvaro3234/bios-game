"""Resolve resource and state paths, both source-run and PyInstaller-frozen.

When frozen (PyInstaller --onefile), bundled data lives under sys._MEIPASS
(a temp dir extracted at launch). Mutable state (settings.json, progress.json,
shifts.json) must live alongside the executable so user edits persist
across runs.
"""

import os
import sys


def is_frozen():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def resource_dir():
    """Directory holding bundled read-only assets (fonts, etc.)."""
    if is_frozen():
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def writable_dir():
    """Directory for mutable JSON state. Next to the .exe when frozen."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource(*parts):
    return os.path.join(resource_dir(), *parts)


def writable(*parts):
    return os.path.join(writable_dir(), *parts)
