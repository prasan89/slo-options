import pytest

from slo_options.risk.limits import RiskLimits, validate_portfolio_risk
from slo_options.risk.position_sizing import calculate_position_size


def test_position_size_respects_risk_and_capital_limits():
    result = calculate_position_size(
        capital=100_000,
        entry_premium=100,
        stop_premium=65,
        lot_size=50,
        risk_per_trade_pct=0.01,
        max_capital_pct=0.10,
    )

    assert result.quantity > 0
    assert result.max_loss <= 1_000
    assert result.premium_capital <= 10_000


def test_no_position_when_one_lot_exceeds_risk_budget():
    result = calculate_position_size(
        capital=10_000,
        entry_premium=500,
        stop_premium=250,
        lot_size=50,
    )
    assert result.quantity == 0


def test_portfolio_risk_limit():
    limits = RiskLimits(max_portfolio_risk_pct=0.03, max_open_positions=3)
    assert validate_portfolio_risk(100_000, 2_000, 800, 2, limits) is True
    assert validate_portfolio_risk(100_000, 2_500, 800, 2, limits) is False
    assert validate_portfolio_risk(100_000, 0, 500, 3, limits) is False


def test_invalid_stop():
    with pytest.raises(ValueError):
        calculate_position_size(100_000, 100, 100, 50)
