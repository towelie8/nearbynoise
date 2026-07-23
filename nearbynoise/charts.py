"""Server-side inline-SVG charts for the overview (no JS, no external libs).

Two views over a rolling window (default 24 h): events per hour (bars) and
loudness over time (coloured points). All functions are pure and take an
explicit `now` so they are deterministic under test.
"""
from nearbynoise.loudness import loudness

# Plot geometry (SVG user units; the page scales width to 100%).
_W, _H = 640, 180
_LEFT, _RIGHT, _TOP, _BOTTOM = 34, 10, 12, 26
_PLOT_W = _W - _LEFT - _RIGHT
_PLOT_H = _H - _TOP - _BOTTOM

# Loudness axis for the scatter plot (dBFS).
_FLOOR_DBFS, _CEIL_DBFS = -70.0, -10.0


def _age_hours(now, t):
    return (now - t).total_seconds() / 3600.0


def hourly_counts(times, now, hours=24):
    """Count events per hour bucket; oldest bucket first, current hour last."""
    counts = [0] * hours
    for t in times:
        idx_from_now = int(_age_hours(now, t))
        if 0 <= idx_from_now < hours:
            counts[hours - 1 - idx_from_now] += 1
    return counts


def _svg(parts):
    body = "".join(parts)
    return (f'<svg viewBox="0 0 {_W} {_H}" class="chart" '
            f'preserveAspectRatio="xMidYMid meet">{body}</svg>')


def bar_chart_svg(counts, now, hours=24):
    """Bar chart of events per hour over the window."""
    peak = max(counts) or 1
    bucket_w = _PLOT_W / hours
    base_y = _TOP + _PLOT_H
    parts = [f'<line x1="{_LEFT}" y1="{base_y}" x2="{_LEFT + _PLOT_W}" '
             f'y2="{base_y}" stroke="#ccc"/>']
    for i, count in enumerate(counts):
        if count:
            bar_h = count / peak * _PLOT_H
            x = _LEFT + i * bucket_w + 1
            y = base_y - bar_h
            parts.append(f'<rect class="chart-bar" x="{x:.1f}" y="{y:.1f}" '
                         f'width="{bucket_w - 2:.1f}" height="{bar_h:.1f}" '
                         f'fill="#5b8def"/>')
    # hour-of-day labels every 3rd bucket
    for i in range(0, hours, 3):
        hour = (now.hour - (hours - 1 - i)) % 24
        x = _LEFT + i * bucket_w + bucket_w / 2
        parts.append(f'<text x="{x:.1f}" y="{_H - 8}" font-size="10" '
                     f'text-anchor="middle" fill="#666">{hour}</text>')
    return _svg(parts)


def _dbfs_to_y(dbfs):
    frac = (dbfs - _FLOOR_DBFS) / (_CEIL_DBFS - _FLOOR_DBFS)
    frac = max(0.0, min(1.0, frac))
    return _TOP + _PLOT_H - frac * _PLOT_H


def scatter_svg(points, now, hours=24):
    """Scatter of loudness (y) over time (x); point colour by loudness category."""
    base_y = _TOP + _PLOT_H
    parts = [f'<line x1="{_LEFT}" y1="{base_y}" x2="{_LEFT + _PLOT_W}" '
             f'y2="{base_y}" stroke="#ccc"/>',
             f'<text x="2" y="{_TOP + 8}" font-size="10" fill="#666">laut</text>',
             f'<text x="2" y="{base_y}" font-size="10" fill="#666">leise</text>']
    for t, dbfs in points:
        age = _age_hours(now, t)
        if not 0 <= age < hours:
            continue
        x = _LEFT + (1 - age / hours) * _PLOT_W
        y = _dbfs_to_y(dbfs)
        colour = loudness(dbfs)["colour"]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" '
                     f'fill="{colour}"/>')
    return _svg(parts)
