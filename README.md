# nearbynoise

A 24/7 noise monitoring system for apartments, built for a Raspberry Pi 4B with a USB microphone.

## What it does

The system continuously records audio into a RAM ring buffer. When the loudness exceeds a configurable threshold for a minimum duration, it extracts an audio clip with pre-roll and post-roll context, stores it as MP3, logs the event to a JSONL file, and uploads it via rsync/SSH to an external server. A Flask web interface presents all events in a simple table with in-browser audio playback, designed for non-technical users.

## Planned architecture

- `capture.py` — microphone audio capture
- `ringbuffer.py` — RAM ring buffer with pre/post-roll extraction
- `detector.py` — RMS-based threshold trigger with hysteresis
- `logger.py` — JSONL event logging
- `uploader.py` — rsync/SSH upload daemon
- `webserver.py` — Flask web UI
- `main.py` — service entry point (runs as a systemd service)

## Stack

Python 3.9+, pyaudio, numpy, pydub, Flask, pytest.

## Status

In design phase. No implementation yet.
