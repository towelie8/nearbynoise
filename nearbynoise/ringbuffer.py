"""RAM ring buffer holding the last N seconds of audio for pre/post-roll."""
import collections

import numpy as np


class RingBuffer:
    def __init__(self, seconds, sample_rate, block_size):
        self._sample_rate = sample_rate
        self._block_size = block_size
        capacity_blocks = int(seconds * sample_rate / block_size)
        self._blocks = collections.deque(maxlen=capacity_blocks)

    def append(self, block, timestamp):
        """Store one block; timestamp is the time of its first sample."""
        self._blocks.append((timestamp, block))

    def extract(self, t_start, t_end):
        """Return all samples in [t_start, t_end), clamped to available data."""
        if not self._blocks:
            return np.empty(0, dtype=np.int16)
        oldest_ts = self._blocks[0][0]
        t_start = max(t_start, oldest_ts)
        parts = []
        for block_ts, block in self._blocks:
            lo = max(0, int(round((t_start - block_ts) * self._sample_rate)))
            hi = min(self._block_size,
                     int(round((t_end - block_ts) * self._sample_rate)))
            if lo < hi:
                parts.append(block[lo:hi])
        if not parts:
            return np.empty(0, dtype=np.int16)
        return np.concatenate(parts)
