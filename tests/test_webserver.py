import json
from datetime import datetime, timezone

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
    assert "22:15:30" in html      # 20:15:30 UTC shown as Europe/Berlin local time
    assert "14.2" in html or "14,2" in html
    assert html.index("20260722T201530") < html.index("20260721T100000")
    assert "/audio/2026/07/22/20260722T201530.mp3" in html


def test_audio_route_serves_mp3(client):
    resp = client.get("/audio/2026/07/22/20260722T201530.mp3")
    assert resp.status_code == 200
    assert resp.data == b"ID3fake"


def test_audio_route_404_for_missing_file(client):
    assert client.get("/audio/2026/07/22/nope.mp3").status_code == 404


def test_loudness_label_by_threshold():
    from nearbynoise.webserver import _loudness
    assert _loudness(-15)["label"] == "Sehr laut"
    assert _loudness(-20)["label"] == "Sehr laut"    # upper boundary inclusive
    assert _loudness(-25)["label"] == "Laut"
    assert _loudness(-35)["label"] == "Laut"         # boundary inclusive
    assert _loudness(-40)["label"] == "Mittel"
    assert _loudness(-52)["label"] == "Mittel"       # boundary inclusive
    assert _loudness(-60)["label"] == "Leise"


def test_loudness_css_class_by_threshold():
    from nearbynoise.webserver import _loudness
    assert _loudness(-15)["css"] == "lvl-extreme"
    assert _loudness(-25)["css"] == "lvl-loud"
    assert _loudness(-40)["css"] == "lvl-mid"
    assert _loudness(-60)["css"] == "lvl-quiet"


def test_loudness_fill_clamped_and_linear():
    from nearbynoise.webserver import _loudness
    assert _loudness(-10)["fill"] == 100
    assert _loudness(-5)["fill"] == 100     # clamped above ceiling
    assert _loudness(-70)["fill"] == 0
    assert _loudness(-90)["fill"] == 0      # clamped below floor
    assert _loudness(-40)["fill"] == 50     # (dbfs+70)/60*100


def test_pegel_column_shows_bar_word_and_dbfs(client, tmp_path):
    log = tmp_path / "events.jsonl"
    quiet = dict(ENTRY, peak_dbfs=-60.0)
    mid = dict(ENTRY, peak_dbfs=-40.0)
    loud = dict(ENTRY, peak_dbfs=-28.0)
    extreme = dict(ENTRY, peak_dbfs=-15.0)
    log.write_text("\n".join(json.dumps(e) for e in (quiet, mid, loud, extreme)) + "\n")
    html = client.get("/").get_data(as_text=True)
    assert "Leise" in html
    assert "Mittel" in html
    assert "Laut" in html            # standalone label (distinct from "Sehr laut")
    assert "Sehr laut" in html
    for css in ("lvl-quiet", "lvl-mid", "lvl-loud", "lvl-extreme"):
        assert css in html
    assert "width:50%" in html       # bar fill for the -40 dB (Mittel) event
    assert "-15" in html             # dBFS value still shown


def test_overview_charts_rendered_for_recent_events(tmp_path):
    day = tmp_path / "2026" / "07" / "22"
    day.mkdir(parents=True)
    (day / "20260722T201530.mp3").write_bytes(b"ID3fake")
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps(ENTRY) + "\n")
    now = datetime(2026, 7, 22, 21, 0, 0, tzinfo=timezone.utc)  # 45 min after event
    app = create_app(tmp_path, log, now=lambda: now)
    html = app.test_client().get("/").get_data(as_text=True)
    assert html.count('class="chart"') == 2      # two SVG charts
    assert "<circle" in html                      # the recent event as a point


def test_overview_empty_state_when_no_recent_events(tmp_path):
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps(ENTRY) + "\n")
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)   # long after the event
    app = create_app(tmp_path, log, now=lambda: now)
    html = app.test_client().get("/").get_data(as_text=True)
    assert "Keine Ereignisse in den letzten 24 Stunden" in html
    assert "<circle" not in html


def test_error_events_shown_without_player(client, tmp_path):
    log = tmp_path / "events.jsonl"
    broken = dict(ENTRY, filename=None)
    broken["error"] = "encoding failed"
    log.write_text(json.dumps(broken) + "\n")
    html = client.get("/").get_data(as_text=True)
    assert "<audio" not in html
    assert "Aufnahme fehlgeschlagen" in html
