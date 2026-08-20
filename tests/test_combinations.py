from datetime import datetime, timedelta

import pytest

from slo_options.strategy.combinations import (
    Instrument,
    butterfly,
    calendar,
    covered_call,
    iron_condor,
    long_call,
    long_call_spread,
    long_ratio_put_spread,
    risk_reversal,
    straddle,
    strangle,
)


EXPIRY = datetime(2026, 9, 24)
FAR = datetime(2026, 10, 29)


def test_long_call_has_defined_downside():
    trade = long_call(100, 5, EXPIRY)
    assert trade.entry_debit == 5
    assert trade.payoff_at_expiry(90, EXPIRY) == -5
    assert trade.payoff_at_expiry(110, EXPIRY) == 5


def test_long_call_spread_caps_profit():
    trade = long_call_spread(100, 110, 8, 3, EXPIRY)
    assert trade.entry_debit == 5
    assert trade.payoff_at_expiry(100, EXPIRY) == -5
    assert trade.payoff_at_expiry(110, EXPIRY) == 5
    assert trade.payoff_at_expiry(130, EXPIRY) == 5


def test_ratio_put_has_two_short_legs():
    trade = long_ratio_put_spread(100, 90, 6, 2, EXPIRY)
    assert trade.legs[0].quantity == 1
    assert trade.legs[1].quantity == 2
    assert trade.entry_debit == 2


def test_calendar_requires_time_valuation():
    trade = calendar(Instrument.CALL, 100, 5, 8, EXPIRY, FAR)
    assert trade.name == "LONG_CALENDAR"
    with pytest.raises(ValueError):
        trade.payoff_at_expiry(100, EXPIRY)


def test_butterfly_requires_equidistant_strikes():
    trade = butterfly(Instrument.CALL, 90, 100, 110, 12, 7, 3, EXPIRY)
    assert [leg.quantity for leg in trade.legs] == [1, 2, 1]
    with pytest.raises(ValueError):
        butterfly(Instrument.CALL, 90, 100, 120, 12, 7, 3, EXPIRY)


def test_straddle_and_strangle():
    assert len(straddle(100, 5, 4, EXPIRY).legs) == 2
    assert len(strangle(90, 110, 3, 3, EXPIRY).legs) == 2


def test_iron_condor_is_defined_risk():
    trade = iron_condor(95, 90, 105, 110, 3, 1, 3, 1, EXPIRY)
    assert trade.entry_credit_received == 4
    assert trade.payoff_at_expiry(100, EXPIRY) == 4
    assert trade.payoff_at_expiry(80, EXPIRY) == -1


def test_risk_reversal_direction():
    bullish = risk_reversal(105, 95, 3, 2, EXPIRY, bullish=True)
    bearish = risk_reversal(105, 95, 3, 2, EXPIRY, bullish=False)
    assert bullish.name == "BULLISH_RISK_REVERSAL"
    assert bearish.name == "BEARISH_RISK_REVERSAL"


def test_covered_call():
    trade = covered_call(100, 110, 4, EXPIRY)
    assert trade.entry_debit == 96
    assert trade.payoff_at_expiry(100, EXPIRY) == 4
    assert trade.payoff_at_expiry(120, EXPIRY) == 14
