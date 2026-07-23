"""Recorder entry point (runs on the Pi as a systemd service)."""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pydub import AudioSegment

from nearbynoise import config
from nearbynoise.capture import (
    AudioCapture,
    CaptureError,
    measure_effective_rate,
    rate_within_tolerance,
)
from nearbynoise.detector import Detector
from nearbynoise.logger import EventLogger
from nearbynoise.ringbuffer import RingBuffer
from nearbynoise.uploader import Uploader


def write_event(event, samples, cfg):
    """Encode samples to MP3 under EVENTS_DIR/YYYY/MM/DD/. Returns the
    filename, or None if encoding failed (event is still logged then)."""
    start = datetime.fromtimestamp(event.t_start, tz=timezone.utc)
    filename = f"{start:%Y%m%dT%H%M%S}.mp3"
    day_dir = Path(cfg.EVENTS_DIR) / f"{start:%Y}" / f"{start:%m}" / f"{start:%d}"
    day_dir.mkdir(parents=True, exist_ok=True)
    segment = AudioSegment(samples.tobytes(), sample_width=2,
                           frame_rate=cfg.SAMPLE_RATE, channels=cfg.CHANNELS)
    try:
        segment.export(day_dir / filename, format="mp3",
                       bitrate=cfg.MP3_BITRATE)
    except OSError as exc:
        print(f"mp3 export failed: {exc}", file=sys.stderr)
        return None
    return filename


def run():
    ring = RingBuffer(config.RING_BUFFER_SECONDS, config.SAMPLE_RATE,
                      config.BLOCK_SIZE)
    detector = Detector(sample_rate=config.SAMPLE_RATE,
                        block_size=config.BLOCK_SIZE,
                        trigger_dbfs=config.TRIGGER_DBFS,
                        release_offset_db=config.RELEASE_OFFSET_DB,
                        min_trigger_ms=config.MIN_TRIGGER_MS,
                        release_ms=config.RELEASE_MS,
                        cooldown_s=config.COOLDOWN_S,
                        max_event_s=config.MAX_EVENT_S)
    logger = EventLogger(config.LOG_PATH)
    uploader = Uploader(config.EVENTS_DIR, config.LOG_PATH,
                        config.REMOTE_TARGET, config.UPLOAD_INTERVAL_S)
    uploader.start()
    capture = AudioCapture(config.SAMPLE_RATE, config.CHANNELS,
                           config.BLOCK_SIZE)
    pending = None
    try:
        eff_rate = measure_effective_rate(capture.blocks(), duration_s=1.0)
        if not rate_within_tolerance(eff_rate, config.SAMPLE_RATE):
            print(f"WARNING: measured capture rate {eff_rate:.0f} Hz deviates "
                  f"from configured {config.SAMPLE_RATE} Hz; recordings may be "
                  f"time-distorted", file=sys.stderr)
        for block in capture.blocks():
            now = time.time()
            ring.append(block, now)
            event = detector.process(block, now)
            if event is not None:
                pending = event
            if pending and now >= pending.t_end + config.POST_ROLL_S:
                samples = ring.extract(pending.t_start - config.PRE_ROLL_S,
                                       pending.t_end + config.POST_ROLL_S)
                filename = write_event(pending, samples, config)
                error = None if filename else "mp3 encoding failed"
                logger.log(pending, filename, error=error)
                pending = None
    except CaptureError as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        sys.exit(1)          # systemd restarts us
    finally:
        uploader.stop()
        capture.close()


if __name__ == "__main__":
    run()
