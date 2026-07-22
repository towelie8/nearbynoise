"""Central configuration. Tune TRIGGER_DBFS on site, then: systemctl restart nearbynoise-recorder."""

# Audio
SAMPLE_RATE = 44100          # Hz
CHANNELS = 1                 # mono
BLOCK_SIZE = 1024            # samples per block (~23 ms)

# Ring buffer
RING_BUFFER_SECONDS = 600    # 10 min RAM history

# Detection (relative dBFS, not calibrated SPL)
TRIGGER_DBFS = -30.0         # trigger threshold ("60 dB" tuning point)
RELEASE_OFFSET_DB = 5.0      # release threshold = TRIGGER_DBFS - offset
MIN_TRIGGER_MS = 200         # minimum loud duration to trigger
RELEASE_MS = 1000            # minimum quiet duration to end an event
COOLDOWN_S = 10              # dead time after a stored event
MAX_EVENT_S = 60             # event length cap for sustained noise

# Event clips
PRE_ROLL_S = 5
POST_ROLL_S = 5
MP3_BITRATE = "128k"

# Paths (Pi)
EVENTS_DIR = "/home/pi/audio_events"     # date tree YYYY/MM/DD below
LOG_PATH = "/home/pi/logs/events.jsonl"

# Upload
UPLOAD_INTERVAL_S = 30
REMOTE_TARGET = "user@vserver:/var/www/laermprotokoll/"
