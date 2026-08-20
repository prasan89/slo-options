from slo_options.analytics.candlestick import Candle, confirm, detect


def C(o, h, l, c):
    return Candle(o, h, l, c)


def test_bullish_engulfing_detected_and_requires_confirmation():
    signals = detect([C(105, 106, 99, 100), C(98, 110, 97, 109)])
    pattern = next(x for x in signals if x.name == "Bullish Engulfing")
    assert pattern.direction == "bullish"
    assert pattern.requires_confirmation
    assert not pattern.confirmed
    assert confirm(pattern, C(109, 112, 108, 111)).confirmed


def test_bearish_engulfing_detected():
    signals = detect([C(100, 106, 99, 105), C(107, 108, 96, 98)])
    pattern = next(x for x in signals if x.name == "Bearish Engulfing")
    assert pattern.direction == "bearish"


def test_doji_and_spinning_top():
    signals = detect([C(100, 105, 95, 100)])
    names = {x.name for x in signals}
    assert "Doji" in names


def test_three_black_crows():
    signals = detect([C(110, 111, 100, 102), C(104, 105, 96, 98), C(100, 101, 90, 92)])
    assert any(x.name == "Three Black Crows" for x in signals)
