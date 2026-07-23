"""Microphone capture. pyaudio is imported lazily so tests run without it."""
import time

import numpy as np


class CaptureError(Exception):
    pass


def rate_within_tolerance(effective_rate, expected_rate, tolerance=0.1):
    """True if the measured rate is within `tolerance` (fraction) of expected."""
    return abs(effective_rate - expected_rate) <= tolerance * expected_rate


def measure_effective_rate(blocks, duration_s=1.0, now=time.time):
    """Pull blocks for ~duration_s and return the real frames-per-second rate.

    Reveals a device that ignores the configured sample rate (the SC60 accepts
    44100 Hz but only delivers ~24435 Hz, time-compressing every recording).
    """
    start = now()
    frames = 0
    for block in blocks:
        frames += len(block)
        if now() - start >= duration_s:
            break
    elapsed = now() - start
    if elapsed <= 0:
        return 0.0
    return frames / elapsed


class AudioCapture:
    def __init__(self, sample_rate, channels, block_size):
        import pyaudio
        self._block_size = block_size
        self._pa = pyaudio.PyAudio()
        try:
            self._stream = self._pa.open(
                format=pyaudio.paInt16, channels=channels,
                rate=sample_rate, input=True,
                frames_per_buffer=block_size)
        except OSError as exc:
            self._pa.terminate()
            raise CaptureError(f"cannot open microphone: {exc}") from exc

    def blocks(self):
        while True:
            try:
                raw = self._stream.read(self._block_size,
                                        exception_on_overflow=False)
            except OSError as exc:
                raise CaptureError(f"microphone read failed: {exc}") from exc
            yield np.frombuffer(raw, dtype=np.int16)

    def close(self):
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()
