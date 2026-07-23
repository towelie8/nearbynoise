"""Flask UI for the VServer. Auth and TLS live in nginx, not here."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (Flask, abort, redirect, render_template_string, request,
                   send_from_directory)

from nearbynoise.charts import bar_chart_svg, hourly_counts, scatter_svg
from nearbynoise.loudness import loudness as _loudness
from nearbynoise.notes import load_notes, set_note

DISPLAY_TZ = ZoneInfo("Europe/Berlin")

PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laermprotokoll</title>
<style>
 body{font-family:sans-serif;margin:1rem;max-width:60rem}
 table{border-collapse:collapse;width:100%}
 td,th{padding:.5rem;border-bottom:1px solid #ccc;text-align:left}
 audio{width:14rem;max-width:60vw}
 .charts{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1rem}
 figure{margin:0;flex:1 1 20rem}
 figcaption{font-size:.9rem;color:#444;margin-bottom:.25rem}
 .chart{width:100%;height:auto;border:1px solid #eee;border-radius:.35rem}
 .empty{color:#666}
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
 .note input[type=text]{width:11rem;max-width:40vw}
 .note button{margin-left:.25rem}
</style></head><body>
<h1>Laermprotokoll</h1>
<h2>Letzte 24 Stunden</h2>
{% if has_recent %}
<div class="charts">
<figure><figcaption>Ereignisse pro Stunde</figcaption>{{ bar_svg|safe }}</figure>
<figure><figcaption>Lautheit ueber die Zeit</figcaption>{{ scatter_svg|safe }}</figure>
</div>
{% else %}
<p class="empty">Keine Ereignisse in den letzten 24 Stunden</p>
{% endif %}
<table><tr><th>Datum</th><th>Uhrzeit</th><th>Dauer</th><th>Pegel</th><th>Anhoeren</th><th>Notiz</th></tr>
{% for e in events %}
<tr><td>{{ e.date }}</td><td>{{ e.time }}</td><td>{{ e.duration }} s</td>
<td><span class="pegel {{ e.css }}"><span class="bar"><i style="width:{{ e.fill }}%"></i></span><span class="word">{{ e.label }}</span> <span class="dbfs">({{ e.peak }} dB)</span></span></td>
<td>{% if e.path %}<audio controls preload="none" src="/audio/{{ e.path }}"></audio>
{% else %}Aufnahme fehlgeschlagen{% endif %}</td>
<td class="note"><form method="post" action="/note"><input type="hidden" name="event" value="{{ e.sort }}"><input type="text" name="note" value="{{ e.note }}" placeholder="Notiz..." maxlength="500"><button type="submit">Speichern</button></form></td></tr>
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


def create_app(events_dir, log_path, now=None, notes_path=None):
    events_dir = Path(events_dir)
    log_path = Path(log_path)
    notes_path = Path(notes_path) if notes_path else events_dir / "notes.json"
    now_provider = now or (lambda: datetime.now(DISPLAY_TZ))
    app = Flask(__name__)

    @app.get("/")
    def index():
        events = _load_events(log_path)
        notes = load_notes(notes_path)
        for e in events:
            e["note"] = notes.get(e["sort"], "")
        current = now_provider()
        points = [(datetime.fromisoformat(e["sort"]).astimezone(DISPLAY_TZ),
                   e["peak"]) for e in events]
        counts = hourly_counts([t for t, _ in points], current)
        return render_template_string(
            PAGE, events=events,
            bar_svg=bar_chart_svg(counts, current),
            scatter_svg=scatter_svg(points, current),
            has_recent=sum(counts) > 0)

    @app.post("/note")
    def save_note():
        event = request.form.get("event", "")
        if event:
            set_note(notes_path, event, request.form.get("note", ""))
        return redirect("/")

    @app.get("/audio/<yyyy>/<mm>/<dd>/<filename>")
    def audio(yyyy, mm, dd, filename):
        day = events_dir / yyyy / mm / dd
        if not day.resolve().is_relative_to(events_dir.resolve()):
            abort(404)
        return send_from_directory(day, filename)

    return app
