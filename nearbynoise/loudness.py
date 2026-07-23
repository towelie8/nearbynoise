"""Relative-dBFS loudness categories, shared by the table and the charts.

dBFS is a relative level (0 = full scale), not a calibrated SPL. These
categories map it onto an intuitive scale for non-technical viewers.
"""

# Category thresholds (relative dBFS). Upper boundary is inclusive.
_EXTREME_DBFS = -20.0
_LOUD_DBFS = -35.0
_MID_DBFS = -52.0

# Bar/plot fill maps [-70, -10] dBFS onto [0, 100] %.
_FILL_FLOOR_DBFS = -70.0
_FILL_CEIL_DBFS = -10.0

# (threshold, label, css class, colour), loudest first.
_CATEGORIES = [
    (_EXTREME_DBFS, "Sehr laut", "lvl-extreme", "#b00020"),
    (_LOUD_DBFS, "Laut", "lvl-loud", "#e07000"),
    (_MID_DBFS, "Mittel", "lvl-mid", "#c9a800"),
    (float("-inf"), "Leise", "lvl-quiet", "#2e7d32"),
]


def fill_percent(peak_dbfs):
    """Map a dBFS peak onto a 0-100 % bar fill, clamped to the range."""
    span = _FILL_CEIL_DBFS - _FILL_FLOOR_DBFS
    fill = round((peak_dbfs - _FILL_FLOOR_DBFS) / span * 100)
    return max(0, min(100, fill))


def loudness(peak_dbfs):
    """Return {label, css, colour, fill} for a relative dBFS peak."""
    for threshold, label, css, colour in _CATEGORIES:
        if peak_dbfs >= threshold:
            return {"label": label, "css": css, "colour": colour,
                    "fill": fill_percent(peak_dbfs)}
