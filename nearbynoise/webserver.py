"""Flask UI for the VServer. Auth and TLS live in nginx, not here."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, abort, render_template_string, send_from_directory

DISPLAY_TZ = ZoneInfo("Europe/Berlin")

# Severity thresholds for highlighting loud events (relative dBFS)
PEAK_HIGH_DBFS = -20.0
PEAK_MID_DBFS = -35.0


def _severity(peak_dbfs):
    if peak_dbfs >= PEAK_HIGH_DBFS:
        return "peak-high"
    if peak_dbfs >= PEAK_MID_DBFS:
        return "peak-mid"
    return "peak-low"

PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laermprotokoll</title>
<style>
 body{font-family:sans-serif;margin:1rem;max-width:60rem}
 table{border-collapse:collapse;width:100%}
 td,th{padding:.5rem;border-bottom:1px solid #ccc;text-align:left}
 audio{width:14rem;max-width:60vw}
 .peak-high{color:#b00020;font-weight:bold}
 .peak-mid{color:#b36b00}
</style></head><body>
<h1>Laermprotokoll</h1>
<table><tr><th>Datum</th><th>Uhrzeit</th><th>Dauer</th><th>Pegel</th><th>Anhoeren</th></tr>
{% for e in events %}
<tr><td>{{ e.date }}</td><td>{{ e.time }}</td><td>{{ e.duration }} s</td>
<td class="{{ e.severity }}">{{ e.peak }} dB</td>
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
        events.append({
            "sort": entry["timestamp_start"],
            "date": f"{start:%d.%m.%Y}",
            "time": f"{start:%H:%M:%S}",
            "duration": entry["duration_sec"],
            "peak": entry["peak_dbfs"],
            "severity": _severity(entry["peak_dbfs"]),
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
