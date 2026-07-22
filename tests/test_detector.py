import math
import numpy as np
import pytest
from nearbynoise.detector import Detector, dbfs

SR = 10000
BS = 500                      # 1 block = 50 ms
BLOCK_S = BS / SR


def make_block(level_dbfs):
    """Sine block with an exact RMS level in dBFS."""
    amp = 32768 * (10 ** (level_dbfs / 20)) * math.sqrt(2)
    t = np.arange(BS)
    return (amp * np.sin(2 * np.pi * 440 * t / SR)).astype(np.int16)


def make_detector(**kw):
    defaults = dict(sample_rate=SR, block_size=BS, trigger_dbfs=-30.0,
                    release_offset_db=5.0, min_trigger_ms=200,
                    release_ms=1000, cooldown_s=10, max_event_s=60)
    defaults.update(kw)
    return Detector(**defaults)


def feed(det, levels, t0=0.0):
    """Feed one block per level; return list of (event, index)."""
    events = []
    for i, lvl in enumerate(levels):
        ev = det.process(make_block(lvl), t0 + i * BLOCK_S)
        if ev is not None:
            events.append((ev, i))
    return events


def test_dbfs_of_calibrated_sine():
    assert dbfs(make_block(-30.0)) == pytest.approx(-30.0, abs=0.1)


def test_triggers_after_200ms_loud():
    # 4 blocks = 200 ms loud, then quiet for release_ms (20 blocks) -> one event
    events = feed(make_detector(), [-20.0] * 4 + [-60.0] * 25)
    assert len(events) == 1
    ev, _ = events[0]
    assert ev.t_start == pytest.approx(0.0)
    assert ev.peak_dbfs == pytest.approx(-20.0, abs=0.2)


def test_no_trigger_at_150ms():
    # 3 blocks = 150 ms < MIN_TRIGGER_MS -> no event
    assert feed(make_detector(), [-20.0] * 3 + [-60.0] * 30) == []


def test_hysteresis_dip_does_not_close_event():
    # dip to -33 dBFS (below trigger -30 but above release -35) mid-event
    levels = [-20.0] * 4 + [-33.0] * 4 + [-20.0] * 4 + [-60.0] * 25
    events = feed(make_detector(), levels)
    assert len(events) == 1
    ev, _ = events[0]
    assert ev.t_end >= 12 * BLOCK_S - BLOCK_S  # dip is inside the event


def test_cooldown_suppresses_second_event():
    det = make_detector(cooldown_s=10)
    levels = ([-20.0] * 4 + [-60.0] * 25) * 2   # second burst inside cooldown
    assert len(feed(det, levels)) == 1


def test_max_event_length_caps_sustained_noise():
    det = make_detector(max_event_s=1.0)
    events = feed(det, [-20.0] * 40)             # 2 s of continuous noise
    assert len(events) == 1
    ev, _ = events[0]
    assert ev.t_end - ev.t_start == pytest.approx(1.0, abs=2 * BLOCK_S)
