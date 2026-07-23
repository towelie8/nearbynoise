import sys
import numpy as np
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def pyaudio_mock(mocker):
    mock = MagicMock()
    mocker.patch.dict(sys.modules, {"pyaudio": mock})
    mock.paInt16 = 8
    return mock


def make_capture(pyaudio_mock, reads):
    from nearbynoise.capture import AudioCapture
    stream = pyaudio_mock.PyAudio.return_value.open.return_value
    stream.read.side_effect = reads
    return AudioCapture(sample_rate=44100, channels=1, block_size=1024)


def test_yields_int16_blocks_of_block_size(pyaudio_mock):
    raw = np.arange(1024, dtype=np.int16).tobytes()
    cap = make_capture(pyaudio_mock, [raw, raw])
    block = next(cap.blocks())
    assert block.dtype == np.int16
    assert len(block) == 1024
    assert block[5] == 5


def test_raises_capture_error_on_device_failure(pyaudio_mock):
    from nearbynoise.capture import CaptureError
    cap = make_capture(pyaudio_mock, OSError("device gone"))
    with pytest.raises(CaptureError):
        next(cap.blocks())


def test_close_terminates_stream(pyaudio_mock):
    cap = make_capture(pyaudio_mock, [])
    cap.close()
    stream = pyaudio_mock.PyAudio.return_value.open.return_value
    stream.stop_stream.assert_called_once()
    stream.close.assert_called_once()
    pyaudio_mock.PyAudio.return_value.terminate.assert_called_once()


# --- capture rate verification (guards against a device that does not honor
#     the configured sample rate, e.g. the SC60 at 44100 Hz) ---

def test_rate_within_tolerance_accepts_matching_rate():
    from nearbynoise.capture import rate_within_tolerance
    assert rate_within_tolerance(48000, 48000) is True


def test_rate_within_tolerance_rejects_time_compressed_rate():
    from nearbynoise.capture import rate_within_tolerance
    # SC60 at 44100 delivered ~24435 Hz -> must be flagged
    assert rate_within_tolerance(24435, 44100) is False


def test_rate_within_tolerance_respects_ten_percent_boundary():
    from nearbynoise.capture import rate_within_tolerance
    assert rate_within_tolerance(45000, 48000) is True    # 6.25% off
    assert rate_within_tolerance(40000, 48000) is False   # 16.7% off


def test_measure_effective_rate_computes_frames_per_second():
    from nearbynoise.capture import measure_effective_rate
    blocks = iter([np.zeros(24000, dtype=np.int16),
                   np.zeros(24000, dtype=np.int16),
                   np.zeros(24000, dtype=np.int16)])
    clock = iter([0.0, 0.5, 1.0, 1.0])
    rate = measure_effective_rate(blocks, duration_s=1.0, now=lambda: next(clock))
    assert rate == 48000.0


def test_measure_effective_rate_returns_zero_when_no_time_elapsed():
    from nearbynoise.capture import measure_effective_rate
    clock = iter([5.0, 5.0])
    rate = measure_effective_rate(iter([]), duration_s=1.0, now=lambda: next(clock))
    assert rate == 0.0
