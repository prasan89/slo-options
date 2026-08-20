from slo_options.analytics.fundamental import FundamentalSnapshot, event_risk, risk_multiplier

def test_relative_valuation_score():
    s = FundamentalSnapshot(pe=15, sector_pe=20, peg=0.9, debt_to_equity=0.5, free_cash_flow=10)
    assert s.relative_pe == 0.75
    assert s.score() > 50

def test_event_risk():
    assert event_risk(1) == "HIGH"
    assert event_risk(3) == "MEDIUM"
    assert event_risk(20) == "NORMAL"
    assert risk_multiplier("HIGH") == 0.5
