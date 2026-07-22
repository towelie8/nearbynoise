from unittest.mock import call
import pytest
from nearbynoise.uploader import Uploader


@pytest.fixture
def setup(tmp_path):
    events = tmp_path / "events"
    day = events / "2026" / "07" / "22"
    day.mkdir(parents=True)
    mp3 = day / "20260722T201530.mp3"
    mp3.write_bytes(b"fake")
    log = tmp_path / "events.jsonl"
    log.write_text("{}\n")
    up = Uploader(events_dir=events, log_path=log,
                  remote_target="user@host:/var/www/laermprotokoll/",
                  interval_s=30)
    return up, events, mp3, log


def test_rsync_called_with_relative_date_tree(setup, mocker):
    up, events, mp3, log = setup
    run = mocker.patch("nearbynoise.uploader.subprocess.run")
    run.return_value.returncode = 0
    up.sync_once()
    mp3_call = run.call_args_list[0]
    assert mp3_call.args[0][:3] == ["rsync", "-az", "--relative"]
    assert "./2026/07/22/20260722T201530.mp3" in mp3_call.args[0]
    assert mp3_call.args[0][-1] == "user@host:/var/www/laermprotokoll/"
    assert mp3_call.kwargs["cwd"] == events
    log_call = run.call_args_list[1]
    assert str(log) in log_call.args[0]


def test_deletes_mp3_only_on_success(setup, mocker):
    up, events, mp3, log = setup
    run = mocker.patch("nearbynoise.uploader.subprocess.run")
    run.return_value.returncode = 0
    up.sync_once()
    assert not mp3.exists()
    assert log.exists()          # events.jsonl is never deleted


def test_keeps_mp3_on_rsync_failure(setup, mocker):
    up, events, mp3, log = setup
    run = mocker.patch("nearbynoise.uploader.subprocess.run")
    run.return_value.returncode = 12
    up.sync_once()
    assert mp3.exists()


def test_no_rsync_when_nothing_to_upload(tmp_path, mocker):
    events = tmp_path / "events"
    events.mkdir()
    up = Uploader(events, tmp_path / "missing.jsonl", "u@h:/x/", 30)
    run = mocker.patch("nearbynoise.uploader.subprocess.run")
    up.sync_once()
    run.assert_not_called()
