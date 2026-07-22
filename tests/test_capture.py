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
