import json
from nearbynoise.detector import Event
from nearbynoise.logger import EventLogger


def test_log_writes_exact_jsonl_line(tmp_path):
    log = tmp_path / "logs" / "events.jsonl"
    EventLogger(log).log(Event(t_start=100.0, t_end=114.2, peak_dbfs=-21.4),
                         filename="19700101T000140.mp3")
    lines = log.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry == {
        "timestamp_start": "1970-01-01T00:01:40+00:00",
        "timestamp_end": "1970-01-01T00:01:54.200000+00:00",
        "duration_sec": 14.2,
        "peak_dbfs": -21.4,
        "filename": "19700101T000140.mp3",
    }


def test_appends_and_supports_error_field(tmp_path):
    log = tmp_path / "events.jsonl"
    lg = EventLogger(log)
    lg.log(Event(0.0, 1.0, -30.0), filename="a.mp3")
    lg.log(Event(2.0, 3.0, -25.0), filename=None, error="encoding failed")
    lines = log.read_text().splitlines()
    assert len(lines) == 2
    entry = json.loads(lines[1])
    assert entry["filename"] is None
    assert entry["error"] == "encoding failed"
