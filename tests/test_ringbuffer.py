import numpy as np
import pytest
from nearbynoise.ringbuffer import RingBuffer

SR = 1000       # simple numbers: 1 block = 100 samples = 0.1 s
BS = 100


def make_buffer(seconds=1.0):
    return RingBuffer(seconds=seconds, sample_rate=SR, block_size=BS)


def fill(rb, n_blocks, start_value=0):
    """Blocks of constant values 0,1,2,... at t=0.0, 0.1, 0.2, ..."""
    for i in range(n_blocks):
        block = np.full(BS, start_value + i, dtype=np.int16)
        rb.append(block, timestamp=(start_value + i) * 0.1)


def test_eviction_keeps_only_capacity():
    rb = make_buffer(seconds=1.0)          # capacity: 10 blocks
    fill(rb, 15)                            # blocks 0..14
    out = rb.extract(0.0, 1.5)              # ask for everything
    assert len(out) == 10 * BS              # only newest 10 blocks remain
    assert out[0] == 5                      # oldest surviving block is #5


def test_extract_exact_range():
    rb = make_buffer(seconds=2.0)
    fill(rb, 10)                            # t = 0.0 .. 1.0
    out = rb.extract(0.25, 0.65)            # 0.4 s -> 400 samples
    assert len(out) == 400
    assert out[0] == 2                      # t=0.25 lies in block #2
    assert out[-1] == 6                     # t=0.6499 lies in block #6


def test_extract_clamps_to_available():
    rb = make_buffer(seconds=1.0)
    fill(rb, 3)                             # t = 0.0 .. 0.3
    out = rb.extract(-5.0, 0.15)            # asks before recording started
    assert len(out) == 150                  # clamped to t=0.0
    assert out[0] == 0


def test_extract_empty_buffer():
    rb = make_buffer()
    assert len(rb.extract(0.0, 1.0)) == 0
