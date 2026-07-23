"""Per-event notes, stored in a small JSON file on the server.

Notes live outside events.jsonl because the Pi's rsync overwrites that file on
every upload. The store is a dict {timestamp_start: text}, written atomically.
"""
import json
import os
from pathlib import Path

MAX_NOTE_LEN = 500


def load_notes(path):
    """Return the notes dict, or {} if the file is missing or empty."""
    path = Path(path)
    if not path.exists():
        return {}
    text = path.read_text()
    if not text.strip():
        return {}
    return json.loads(text)


def set_note(path, key, text):
    """Set (or clear, if blank) the note for `key`; returns the updated dict."""
    path = Path(path)
    notes = load_notes(path)
    text = (text or "").strip()[:MAX_NOTE_LEN]
    if text:
        notes[key] = text
    else:
        notes.pop(key, None)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(notes, ensure_ascii=False))
    os.replace(tmp, path)
    return notes
