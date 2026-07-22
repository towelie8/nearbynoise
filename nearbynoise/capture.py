"""Microphone capture. pyaudio is imported lazily so tests run without it."""
import numpy as np


class CaptureError(Exception):
    pass


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
