from slo_options.analytics.black_scholes import delta, implied_volatility, price
from slo_options.analytics.expected_move import expected_move


def test_atm_call_delta():
    d = delta(100, 100, 30 / 365, 0.20, 0.0, "CE")
    assert 0.45 < d < 0.60


def test_iv_roundtrip():
    p = price(100, 100, 30 / 365, 0.20, 0.0, "CE")
    iv = implied_volatility(p, 100, 100, 30 / 365, 0.0, "CE")
    assert abs(iv - 0.20) < 1e-6


def test_expected_move():
    assert expected_move(100, 0.20, 1) > 0
