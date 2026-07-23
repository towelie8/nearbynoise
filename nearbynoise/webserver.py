"""Flask UI for the VServer. Auth and TLS live in nginx, not here."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, abort, render_template_string, send_from_directory

DISPLAY_TZ = ZoneInfo("Europe/Berlin")

# Loudness categories (relative dBFS). Upper boundary is inclusive.
_EXTREME_DBFS = -20.0
_LOUD_DBFS = -35.0
_MID_DBFS = -52.0

# Bar fill maps [-70, -10] dBFS onto [0, 100] %.
_FILL_FLOOR_DBFS = -70.0
_FILL_CEIL_DBFS = -10.0


def _loudness(peak_dbfs):
    """Map a relative dBFS peak to a category label, CSS class and bar fill %."""
    if peak_dbfs >= _EXTREME_DBFS:
        label, css = "Sehr laut", "lvl-extreme"
    elif peak_dbfs >= _LOUD_DBFS:
        label, css = "Laut", "lvl-loud"
    elif peak_dbfs >= _MID_DBFS:
        label, css = "Mittel", "lvl-mid"
    else:
        label, css = "Leise", "lvl-quiet"
    span = _FILL_CEIL_DBFS - _FILL_FLOOR_DBFS
    fill = round((peak_dbfs - _FILL_FLOOR_DBFS) / span * 100)
    fill = max(0, min(100, fill))
    return {"label": label, "css": css, "fill": fill}

PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laermprotokoll</title>
<style>
 body{font-family:sans-serif;margin:1rem;max-width:60rem}
 table{border-collapse:collapse;width:100%}
 td,th{padding:.5rem;border-bottom:1px solid #ccc;text-align:left}
 audio{width:14rem;max-width:60vw}
 .pegel{display:flex;align-items:center;gap:.5rem}
 .bar{flex:0 0 6rem;height:.7rem;background:#eee;border-radius:.35rem;overflow:hidden}
 .bar>i{display:block;height:100%}
 .lvl-quiet .bar>i{background:#2e7d32}
 .lvl-mid .bar>i{background:#c9a800}
 .lvl-loud .bar>i{background:#e07000}
 .lvl-extreme .bar>i{background:#b00020}
 .word{min-width:5rem}
 .lvl-loud .word{color:#e07000}
 .lvl-extreme .word{color:#b00020;font-weight:bold}
 .dbfs{color:#888;font-size:.85em}
</style></head><body>
<h1>Laermprotokoll</h1>
<table><tr><th>Datum</th><th>Uhrzeit</th><th>Dauer</th><th>Pegel</th><th>Anhoeren</th></tr>
{% for e in events %}
<tr><td>{{ e.date }}</td><td>{{ e.time }}</td><td>{{ e.duration }} s</td>
<td><span class="pegel {{ e.css }}"><span class="bar"><i style="width:{{ e.fill }}%"></i></span><span class="word">{{ e.label }}</span> <span class="dbfs">({{ e.peak }} dB)</span></span></td>
<td>{% if e.path %}<audio controls preload="none" src="/audio/{{ e.path }}"></audio>
{% else %}Aufnahme fehlgeschlagen{% endif %}</td></tr>
{% endfor %}
</table></body></html>"""


def _load_events(log_path):
    events = []
    if not log_path.exists():
        return events
    for line in log_path.read_text().splitlines():
        entry = json.loads(line)
        start = datetime.fromisoformat(entry["timestamp_start"])
        path = None
        if entry.get("filename"):
            # file paths stay in UTC (matches filename and date tree)
            path = f"{start:%Y/%m/%d}/{entry['filename']}"
        start = start.astimezone(DISPLAY_TZ)
        loud = _loudness(entry["peak_dbfs"])
        events.append({
            "sort": entry["timestamp_start"],
            "date": f"{start:%d.%m.%Y}",
            "time": f"{start:%H:%M:%S}",
            "duration": entry["duration_sec"],
            "peak": entry["peak_dbfs"],
            "label": loud["label"],
            "css": loud["css"],
            "fill": loud["fill"],
            "path": path,
        })
    return sorted(events, key=lambda e: e["sort"], reverse=True)


def create_app(events_dir, log_path):
    events_dir = Path(events_dir)
    log_path = Path(log_path)
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template_string(PAGE, events=_load_events(log_path))

    @app.get("/audio/<yyyy>/<mm>/<dd>/<filename>")
    def audio(yyyy, mm, dd, filename):
        day = events_dir / yyyy / mm / dd
        if not day.resolve().is_relative_to(events_dir.resolve()):
            abort(404)
        return send_from_directory(day, filename)

    return app
