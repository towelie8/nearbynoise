"""Live level meter for tuning TRIGGER_DBFS on site.

Stop the recorder first (it holds the microphone exclusively):
    sudo systemctl stop nearbynoise-recorder
    .venv/bin/python tools/meter.py
Note the level during silence and during representative noise, set
TRIGGER_DBFS in nearbynoise/config.py between the two, then restart:
    sudo systemctl start nearbynoise-recorder
"""
import math

import numpy as np
import pyaudio

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
BLOCKS_PER_LINE = 43  # ~1 s per printed line


def main():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                     input=True, frames_per_buffer=BLOCK_SIZE)
    print("Level meter running, Ctrl+C to stop.")
    try:
        while True:
            blocks = [np.frombuffer(
                stream.read(BLOCK_SIZE, exception_on_overflow=False),
                dtype=np.int16) for _ in range(BLOCKS_PER_LINE)]
            samples = np.concatenate(blocks).astype(np.float64)
            rms = math.sqrt((samples ** 2).mean())
            db = 20 * math.log10(rms / 32768) if rms else -120.0
            print(f"{db:6.1f} dBFS  {'#' * max(0, int(db + 90))}")
    except KeyboardInterrupt:
        pass
    finally:
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    main()
