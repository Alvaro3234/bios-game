"""Shift mode persistence + scoring.

A Shift is a sequence of procedurally-generated tickets played back-to-back.
The player gets a score based on:
  - completion time (lower is better, baseline 60s/ticket)
  - hints used (none here since procedural tickets have no hints)
  - first-try bonus per ticket

High scores per (vendor_pool tag) are stored in shifts.json.
"""

import json
import os
import time

from paths import writable


SHIFTS_PATH = writable("shifts.json")


def load_high_scores():
    try:
        with open(SHIFTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_high_scores(data):
    tmp = SHIFTS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SHIFTS_PATH)


class ShiftRun:
    """Live scoring state for one shift attempt."""

    BASELINE_SECONDS_PER_TICKET = 60
    TIME_PENALTY_PER_SECOND = 1
    FIRST_TRY_BONUS = 100
    RETRY_PENALTY = 25

    def __init__(self, seed, n, vendor_pool_tag="any"):
        self.seed = seed
        self.n = n
        self.tag = vendor_pool_tag
        self.t0 = time.monotonic()
        self.per_ticket_attempts = [0] * n
        self.per_ticket_first_pass_at = [None] * n

    def record_failure(self, idx):
        if 0 <= idx < self.n:
            self.per_ticket_attempts[idx] += 1

    def record_success(self, idx):
        if 0 <= idx < self.n and self.per_ticket_first_pass_at[idx] is None:
            self.per_ticket_first_pass_at[idx] = time.monotonic() - self.t0

    def score(self):
        total_time = time.monotonic() - self.t0
        baseline = self.BASELINE_SECONDS_PER_TICKET * self.n
        time_pts = max(0, int((baseline - total_time)
                              * self.TIME_PENALTY_PER_SECOND))
        bonus = sum(self.FIRST_TRY_BONUS
                    for a in self.per_ticket_attempts if a == 0)
        penalty = sum(self.RETRY_PENALTY * a
                      for a in self.per_ticket_attempts)
        return max(0, time_pts + bonus - penalty)

    def finalize(self):
        """Update shifts.json with the best score for this (seed, tag)."""
        scores = load_high_scores()
        key = "%s/seed=%d/n=%d" % (self.tag, self.seed, self.n)
        cur = scores.get(key, 0)
        s = self.score()
        if s > cur:
            scores[key] = s
            save_high_scores(scores)
        return s
