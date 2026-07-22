import numpy as np
import pytest
from nearbynoise.detector import Event
from nearbynoise import main as main_mod


class FakeConfig:
    SAMPLE_RATE = 1000
    CHANNELS = 1
    MP3_BITRATE = "128k"
    PRE_ROLL_S = 1
    POST_ROLL_S = 1


def test_write_event_encodes_into_date_tree(tmp_path, mocker):
    cfg = FakeConfig()
    cfg.EVENTS_DIR = str(tmp_path)
    seg_cls = mocker.patch("nearbynoise.main.AudioSegment")
    ev = Event(t_start=1753211730.0, t_end=1753211740.0, peak_dbfs=-20.0)  # 2025-07-22 19:15:30 UTC
    samples = np.zeros(12000, dtype=np.int16)
    filename = main_mod.write_event(ev, samples, cfg)
    assert filename == "20250722T191530.mp3"
    export = seg_cls.return_value.export
    out_path = export.call_args.args[0]
    assert str(out_path).endswith("2025/07/22/20250722T191530.mp3")
    assert out_path.parent.is_dir()          # date tree created automatically


def test_write_event_returns_none_on_encoding_error(tmp_path, mocker):
    cfg = FakeConfig()
    cfg.EVENTS_DIR = str(tmp_path)
    seg = mocker.patch("nearbynoise.main.AudioSegment")
    seg.return_value.export.side_effect = OSError("no ffmpeg")
    ev = Event(0.0, 1.0, -20.0)
    assert main_mod.write_event(ev, np.zeros(100, np.int16), cfg) is None
