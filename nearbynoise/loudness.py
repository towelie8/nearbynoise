"""Loudness categories, shared by the table and the charts.

The detector measures a relative dBFS level (0 = full scale), not a calibrated
sound pressure. On site we compared the microphone against a phone dB meter and
found a near 1:1 relationship, so an estimated dB(A) is `dBFS + offset`. The
offset is site-specific (mic, gain, position) -- recalibrate by changing the one
number below. The result is an estimate for a communication headset, not a
metrology-grade reading, hence the "~" shown in the UI.
"""

# Calibration offset: estimated dB(A) = peak_dbfs + offset (Fensterbank, 3. OG).
CALIBRATION_OFFSET_DB = 103.0

# Category thresholds in estimated dB(A). Lower boundary is inclusive.
_MITTEL_MIN = 50
_LAUT_MIN = 65
_SEHR_LAUT_MIN = 80

# Bar/plot fill maps [35, 95] dB(A) onto [0, 100] %.
_FILL_FLOOR_DBA = 35.0
_FILL_CEIL_DBA = 95.0

# (min dB(A), label, css class, colour), loudest first.
_CATEGORIES = [
    (_SEHR_LAUT_MIN, "Sehr laut", "lvl-extreme", "#b00020"),
    (_LAUT_MIN, "Laut", "lvl-loud", "#e07000"),
    (_MITTEL_MIN, "Mittel", "lvl-mid", "#c9a800"),
    (float("-inf"), "Leise", "lvl-quiet", "#2e7d32"),
]


def fill_percent(dba):
    """Map an estimated dB(A) level onto a 0-100 % bar fill, clamped."""
    span = _FILL_CEIL_DBA - _FILL_FLOOR_DBA
    fill = round((dba - _FILL_FLOOR_DBA) / span * 100)
    return max(0, min(100, fill))


def loudness(peak_dbfs, offset=CALIBRATION_OFFSET_DB):
    """Return {label, css, colour, fill, spl} for a relative dBFS peak.

    `spl` is the estimated dB(A) level (rounded); `offset` overrides the site
    calibration (used in tests).
    """
    dba = round(peak_dbfs + offset)
    for min_dba, label, css, colour in _CATEGORIES:
        if dba >= min_dba:
            return {"label": label, "css": css, "colour": colour,
                    "fill": fill_percent(dba), "spl": dba}
