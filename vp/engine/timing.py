from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Tuple

def step_duration(bpm: float, subdiv: int) -> float:
    if bpm <= 0:
        raise ValueError("bpm must be > 0")
    if subdiv <= 0:
        raise ValueError("subdiv must be > 0")
    return 60.0 / (bpm * subdiv)

def split_hold_gap(step_secs: float, chord_hold: float) -> Tuple[float, float]:
    if not (0.0 <= chord_hold <= 1.0):
        raise ValueError("chord_hold must be in [0, 1]")
    hold = step_secs * chord_hold
    gap = max(0.0, step_secs - hold)
    return hold, gap

@dataclass
class BeatClock:
    step_secs: float
    start_delay: float = 0.0

    def start_time(self) -> float:
        return time.perf_counter() + max(0.0, self.start_delay)

    def sleep_until_step(self, t0: float, index: int) -> None:
        deadline = t0 + (index * self.step_secs)
        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break
            time.sleep(remaining if remaining < 0.05 else 0.05)

    def next_deadline(self, t0: float, index: int) -> float:
        return t0 + (index * self.step_secs)
