from nearbynoise.loudness import loudness


def test_loudness_label_and_css_by_threshold():
    assert loudness(-15)["label"] == "Sehr laut"
    assert loudness(-15)["css"] == "lvl-extreme"
    assert loudness(-20)["label"] == "Sehr laut"    # boundary inclusive
    assert loudness(-25)["label"] == "Laut"
    assert loudness(-35)["label"] == "Laut"          # boundary inclusive
    assert loudness(-40)["label"] == "Mittel"
    assert loudness(-52)["label"] == "Mittel"        # boundary inclusive
    assert loudness(-60)["label"] == "Leise"


def test_loudness_colour_per_category():
    assert loudness(-15)["colour"] == "#b00020"
    assert loudness(-25)["colour"] == "#e07000"
    assert loudness(-40)["colour"] == "#c9a800"
    assert loudness(-60)["colour"] == "#2e7d32"


def test_loudness_fill_clamped_and_linear():
    assert loudness(-10)["fill"] == 100
    assert loudness(-5)["fill"] == 100
    assert loudness(-70)["fill"] == 0
    assert loudness(-90)["fill"] == 0
    assert loudness(-40)["fill"] == 50
