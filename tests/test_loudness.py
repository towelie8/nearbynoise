from nearbynoise.loudness import loudness, CALIBRATION_OFFSET_DB


def test_spl_is_dbfs_plus_calibration_offset():
    # dB(A) estimate = dBFS + offset; the on-site offset is ~103
    assert loudness(-13.3, offset=103)["spl"] == 90    # round(89.7)
    assert loudness(-51, offset=103)["spl"] == 52


def test_default_offset_is_the_calibrated_value():
    assert loudness(-51)["spl"] == round(-51 + CALIBRATION_OFFSET_DB)


def test_category_by_dba_threshold():
    # offset 100 -> dB(A) = dBFS + 100, easy to read; boundaries 50/65/80
    assert loudness(-55, offset=100)["label"] == "Leise"      # 45 dB(A)
    assert loudness(-50, offset=100)["label"] == "Mittel"     # 50 (boundary)
    assert loudness(-40, offset=100)["label"] == "Mittel"     # 60
    assert loudness(-35, offset=100)["label"] == "Laut"       # 65 (boundary)
    assert loudness(-20, offset=100)["label"] == "Sehr laut"  # 80 (boundary)


def test_css_class_and_colour_per_category():
    assert loudness(-20, offset=100)["css"] == "lvl-extreme"
    assert loudness(-20, offset=100)["colour"] == "#b00020"
    assert loudness(-35, offset=100)["css"] == "lvl-loud"
    assert loudness(-40, offset=100)["css"] == "lvl-mid"
    assert loudness(-55, offset=100)["css"] == "lvl-quiet"


def test_fill_clamped_and_linear_on_dba():
    # bar fill maps [35, 95] dB(A) onto [0, 100] %
    assert loudness(-8, offset=103)["fill"] == 100     # 95 dB(A) -> 100
    assert loudness(0, offset=103)["fill"] == 100      # 103 -> clamped
    assert loudness(-68, offset=103)["fill"] == 0      # 35 dB(A) -> 0
    assert loudness(-80, offset=103)["fill"] == 0      # clamped
    assert loudness(-38, offset=103)["fill"] == 50     # 65 dB(A) -> 50
