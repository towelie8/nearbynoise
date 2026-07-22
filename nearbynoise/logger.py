import json
from datetime import datetime, timezone
from pathlib import Path


def _iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


class EventLogger:
    def __init__(self, log_path):
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event, filename, error=None):
        entry = {
            "timestamp_start": _iso(event.t_start),
            "timestamp_end": _iso(event.t_end),
            "duration_sec": round(event.t_end - event.t_start, 3),
            "peak_dbfs": round(event.peak_dbfs, 1),
            "filename": filename,
        }
        if error is not None:
            entry["error"] = error
        with self._path.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
            fh.flush()
