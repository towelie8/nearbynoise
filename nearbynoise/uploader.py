"""Background upload to the VServer. rsync --relative recreates the
YYYY/MM/DD tree on the remote automatically - no manual directories."""
import subprocess
import threading
from pathlib import Path


class Uploader(threading.Thread):
    def __init__(self, events_dir, log_path, remote_target, interval_s):
        super().__init__(daemon=True, name="uploader")
        self._events_dir = Path(events_dir)
        self._log_path = Path(log_path)
        self._remote = remote_target
        self._interval = interval_s
        self._stop = threading.Event()

    def sync_once(self):
        mp3s = sorted(self._events_dir.rglob("*.mp3"))
        if mp3s:
            rel = [f"./{p.relative_to(self._events_dir)}" for p in mp3s]
            result = subprocess.run(
                ["rsync", "-az", "--relative", *rel, self._remote],
                cwd=self._events_dir)
            if result.returncode == 0:
                for p in mp3s:
                    p.unlink()
        if self._log_path.exists():
            subprocess.run(["rsync", "-az", str(self._log_path), self._remote])

    def run(self):
        while not self._stop.wait(self._interval):
            self.sync_once()

    def stop(self):
        self._stop.set()
