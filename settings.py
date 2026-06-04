"""settings.json persistence: atomic save, validated load."""

import json
import os

from paths import writable

SETTINGS_PATH = writable("settings.json")
USER_DEFAULTS_PATH = writable("user_defaults.json")


def load(path=SETTINGS_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(values, path=SETTINGS_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(values, f, indent=2)
    os.replace(tmp, path)
