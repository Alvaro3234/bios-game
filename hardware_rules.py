"""Declarative boot-time hardware constraints ("silicon limits").

A constraint describes a settings combination that prevents the machine
from booting, independently of the ticket's scripted failure:

    {
        "id": "xmp_profile2_unstable",
        "match":  {"xmp": "Profile 2"},          # all must match (AND)
        "unless": {"dram_volt": "1.45V"},        # escape combo (AND)
        "fail": {"style": "memtrain",
                 "lines": ["..."],
                 "beep": "memory_fail",          # optional beep_map kind
                 "post_code": "55"},             # optional stuck POST code
    }

Match grammar per id:
    "Value"            exact match (option/password)
    ["V1", "V2"]       membership
    {">=": n}          numeric comparison (numeric items only)
    {"<=": n}          (operators may be combined in one dict)

GLOBAL_CONSTRAINTS model the simulated board itself and apply to every
ticket and to endless mode, so the player can learn the machine's limits.
Per-ticket `boot_constraints` (same schema) describe machine-specific
flaws and are checked first.
"""

from menu_model import iter_persistable

ITEM_BY_ID = {it["id"]: it for it in iter_persistable()}

MEMTRAIN_FAIL = {
    "style": "memtrain",
    "lines": [
        "Memory initialization error.",
        "The system DRAM failed training at the configured frequency.",
        "",
        "MRC: DDR4 training FAILED on channel A, rank 0",
        "MRC: retrying with last known good timings... FAILED",
    ],
    "beep": "memory_fail",
    "post_code": "55",
}

WATCHDOG_FAIL = {
    "style": "bsod",
    "lines": [
        "Your PC ran into a problem and needs to restart. We're just",
        "collecting some error info, and then we'll restart for you.",
        "",
        "0% complete",
        "",
        "Stop code: CLOCK_WATCHDOG_TIMEOUT",
    ],
}

POWER_CYCLE_FAIL = {
    "style": "black",
    "lines": [
        "(the machine powers on, the fans spin for a second,",
        " then it clicks off and tries again -- over and over)",
    ],
    "beep": "memory_fail",
    "post_code": "00",
}

THERMTRIP_FAIL = {
    "style": "thermtrip",
    "lines": [
        "CPU Over Temperature Error!",
        "CPU Fan Error!",
        "",
        "The system reached the processor thermal trip point",
        "shortly after boot and shut itself down.",
        "",
        "Press F1 to Resume",
    ],
    "post_code": "Eb",
}

# The simulated board's limits: identical in every ticket and in endless
# mode, so the player can learn the machine. Checked top to bottom; the
# first match wins, so harder walls come before tunable ones.
GLOBAL_CONSTRAINTS = [
    {
        # No amount of voltage pushes this chip past 52x.
        "id": "cpu_ratio_silicon_wall",
        "match": {"cpu_ratio": {">=": 53}},
        "fail": POWER_CYCLE_FAIL,
    },
    {
        # 47x and up boots only with a positive voltage offset.
        "id": "cpu_ratio_needs_vcore",
        "match": {"cpu_ratio": {">=": 47},
                  "vcore_offset": ["Auto", "-0.10V", "-0.05V", "+0.00V"]},
        "fail": WATCHDOG_FAIL,
    },
    {
        # The memory controller trains 3600 only with 1.45V and 2T.
        "id": "xmp_profile2_unstable",
        "match": {"xmp": "Profile 2"},
        "unless": {"dram_volt": "1.45V", "cmd_rate": "2T"},
        "fail": MEMTRAIN_FAIL,
    },
    {
        "id": "dram_3600_unstable",
        "match": {"dram_freq": "3600 MHz"},
        "unless": {"dram_volt": "1.45V", "cmd_rate": "2T"},
        "fail": MEMTRAIN_FAIL,
    },
    {
        "id": "cpu_fan_disabled_thermtrip",
        "match": {"cpu_fan_profile": "Disabled"},
        "fail": THERMTRIP_FAIL,
    },
]


def match_value(value, want):
    """One id's value against one match spec; see grammar above."""
    if isinstance(want, dict):
        for op, ref in want.items():
            if op == ">=":
                if not (isinstance(value, (int, float)) and value >= ref):
                    return False
            elif op == "<=":
                if not (isinstance(value, (int, float)) and value <= ref):
                    return False
            else:
                raise ValueError("unknown comparator %r" % op)
        return True
    if isinstance(want, (list, tuple)):
        return value in want
    return value == want


def _matches(model, spec):
    for cid, want in spec.items():
        item = ITEM_BY_ID.get(cid)
        # Grayed-out settings have no effect on the machine.
        if item is None or not model.is_enabled(item):
            return False
        if not match_value(model.values.get(cid), want):
            return False
    return True


def check_constraints(model, extra=None):
    """Return the `fail` dict of the first violated constraint, or None.

    Per-ticket constraints (`extra`) are checked before the global board
    limits so a ticket can override the generic failure with a specific
    one.
    """
    for con in list(extra or []) + GLOBAL_CONSTRAINTS:
        if _matches(model, con["match"]):
            unless = con.get("unless")
            if unless and _matches(model, unless):
                continue
            return con["fail"]
    return None
