from datetime import datetime, timezone, timedelta

from nearbynoise.charts import hourly_counts, bar_chart_svg, scatter_svg

NOW = datetime(2026, 7, 23, 12, 0, 0, tzinfo=timezone.utc)


def test_hourly_counts_buckets_events_and_drops_old_ones():
    times = [
        NOW - timedelta(minutes=10),           # current hour
        NOW - timedelta(minutes=30),           # current hour
        NOW - timedelta(hours=1, minutes=5),   # one hour ago
        NOW - timedelta(hours=25),             # outside the 24 h window
    ]
    counts = hourly_counts(times, NOW, hours=24)
    assert len(counts) == 24
    assert counts[-1] == 2      # current hour is the last (rightmost) bucket
    assert counts[-2] == 1      # one hour ago
    assert sum(counts) == 3     # the 25 h old event is ignored


def test_bar_chart_svg_has_one_bar_per_nonzero_bucket():
    counts = [0] * 24
    counts[23] = 2
    counts[22] = 1
    svg = bar_chart_svg(counts, NOW)
    assert svg.startswith("<svg")
    assert svg.count('class="chart-bar"') == 2


def test_scatter_svg_has_a_coloured_circle_per_point_in_window():
    points = [
        (NOW - timedelta(hours=1), -15.0),    # Sehr laut -> #b00020
        (NOW - timedelta(hours=2), -60.0),    # Leise -> #2e7d32
        (NOW - timedelta(hours=30), -20.0),   # outside window -> ignored
    ]
    svg = scatter_svg(points, NOW)
    assert svg.count("<circle") == 2
    assert "#b00020" in svg
    assert "#2e7d32" in svg


def test_scatter_svg_has_no_circle_without_points():
    svg = scatter_svg([], NOW)
    assert "<circle" not in svg
