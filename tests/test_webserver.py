import json
import pytest
from nearbynoise.webserver import create_app

ENTRY = {"timestamp_start": "2026-07-22T20:15:30+00:00",
         "timestamp_end": "2026-07-22T20:15:44+00:00",
         "duration_sec": 14.2, "peak_dbfs": -21.4,
         "filename": "20260722T201530.mp3"}


@pytest.fixture
def client(tmp_path):
    day = tmp_path / "2026" / "07" / "22"
    day.mkdir(parents=True)
    (day / "20260722T201530.mp3").write_bytes(b"ID3fake")
    log = tmp_path / "events.jsonl"
    older = dict(ENTRY, timestamp_start="2026-07-21T10:00:00+00:00",
                 filename="20260721T100000.mp3")
    log.write_text(json.dumps(older) + "\n" + json.dumps(ENTRY) + "\n")
    return create_app(tmp_path, log).test_client()


def test_index_lists_events_newest_first(client):
    html = client.get("/").get_data(as_text=True)
    assert "22.07.2026" in html
    assert "14.2" in html or "14,2" in html
    assert html.index("20260722T201530") < html.index("20260721T100000")
    assert "/audio/2026/07/22/20260722T201530.mp3" in html


def test_audio_route_serves_mp3(client):
    resp = client.get("/audio/2026/07/22/20260722T201530.mp3")
    assert resp.status_code == 200
    assert resp.data == b"ID3fake"


def test_audio_route_404_for_missing_file(client):
    assert client.get("/audio/2026/07/22/nope.mp3").status_code == 404


def test_error_events_shown_without_player(client, tmp_path):
    log = tmp_path / "events.jsonl"
    broken = dict(ENTRY, filename=None)
    broken["error"] = "encoding failed"
    log.write_text(json.dumps(broken) + "\n")
    html = client.get("/").get_data(as_text=True)
    assert "<audio" not in html
    assert "Aufnahme fehlgeschlagen" in html
