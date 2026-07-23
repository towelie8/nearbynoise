from nearbynoise.notes import load_notes, set_note, MAX_NOTE_LEN


def test_load_notes_returns_empty_when_file_missing(tmp_path):
    assert load_notes(tmp_path / "notes.json") == {}


def test_set_note_persists_and_loads(tmp_path):
    p = tmp_path / "notes.json"
    set_note(p, "2026-07-22T20:15:30+00:00", "Motorradfahrer X")
    assert load_notes(p)["2026-07-22T20:15:30+00:00"] == "Motorradfahrer X"


def test_set_note_updates_existing(tmp_path):
    p = tmp_path / "notes.json"
    set_note(p, "k", "erst")
    set_note(p, "k", "dann")
    assert load_notes(p)["k"] == "dann"


def test_set_note_empty_text_removes_entry(tmp_path):
    p = tmp_path / "notes.json"
    set_note(p, "k", "hallo")
    set_note(p, "k", "   ")
    assert "k" not in load_notes(p)


def test_set_note_truncates_long_text(tmp_path):
    p = tmp_path / "notes.json"
    set_note(p, "k", "x" * (MAX_NOTE_LEN + 100))
    assert len(load_notes(p)["k"]) == MAX_NOTE_LEN
