"""RMS threshold detector with hysteresis, cooldown and max event length.

State machine (spec section 4): IDLE -> CANDIDATE -> ACTIVE -> CLOSING.
Durations are measured up to the END of the current block, because a block
timestamp marks its first sample.
"""
import math
from dataclasses import dataclass

import numpy as np

_SILENCE_DBFS = -120.0
_IDLE, _CANDIDATE, _ACTIVE, _CLOSING = range(4)


def dbfs(block):
    """RMS level of an int16 block in dBFS (0 dBFS = full scale)."""
    rms = math.sqrt(np.mean(block.astype(np.float64) ** 2))
    if rms == 0:
        return _SILENCE_DBFS
    return 20 * math.log10(rms / 32768)


@dataclass
class Event:
    t_start: float
    t_end: float
    peak_dbfs: float


class Detector:
    def __init__(self, sample_rate, block_size, trigger_dbfs,
                 release_offset_db, min_trigger_ms, release_ms,
                 cooldown_s, max_event_s):
        self._block_s = block_size / sample_rate
        self._trigger = trigger_dbfs
        self._release = trigger_dbfs - release_offset_db
        self._min_trigger_s = min_trigger_ms / 1000
        self._release_s = release_ms / 1000
        self._cooldown_s = cooldown_s
        self._max_event_s = max_event_s
        self._state = _IDLE
        self._candidate_since = 0.0
        self._event_start = 0.0
        self._quiet_since = 0.0
        self._peak = _SILENCE_DBFS
        self._cooldown_until = 0.0

    def process(self, block, timestamp):
        """Feed one block; returns the finished Event exactly once, else None."""
        level = dbfs(block)
        block_end = timestamp + self._block_s

        if timestamp < self._cooldown_until:
            return None

        if self._state == _IDLE:
            if level >= self._trigger:
                self._state = _CANDIDATE
                self._candidate_since = timestamp
                self._peak = level
            return None

        self._peak = max(self._peak, level)

        if self._state == _CANDIDATE:
            if level < self._trigger:
                self._state = _IDLE
            elif block_end - self._candidate_since >= self._min_trigger_s:
                self._state = _ACTIVE
                self._event_start = self._candidate_since
            return None

        if self._state == _ACTIVE:
            if level < self._release:
                self._state = _CLOSING
                self._quiet_since = timestamp
                return None
            if block_end - self._event_start >= self._max_event_s:
                return self._close(t_end=block_end, now=block_end)
            return None

        # _CLOSING
        if level >= self._trigger:
            self._state = _ACTIVE
            return None
        if block_end - self._quiet_since >= self._release_s:
            return self._close(t_end=self._quiet_since, now=block_end)
        return None

    def _close(self, t_end, now):
        event = Event(self._event_start, t_end, self._peak)
        self._state = _IDLE
        self._cooldown_until = now + self._cooldown_s
        return event
