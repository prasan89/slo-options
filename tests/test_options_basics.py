from slo_options.options_basics import OptionQuote, intrinsic_value, liquidity_score, moneyness, option_cost, time_value

def quote(kind="CALL", strike=100, ltp=7.0):
    return OptionQuote("TEST", kind, strike, "2026-09-01", ltp, bid=6.9, ask=7.1, volume=5000, open_interest=20000)

def test_intrinsic_and_time_value():
    q = quote("CALL", 100, 7)
    assert intrinsic_value(105, 100, "CALL") == 5
    assert time_value(q, 105) == 2

def test_moneyness_and_cost():
    q = quote("PUT", 105, 6)
    assert moneyness(100, 105, "PUT") == "ITM"
    assert option_cost(q, contracts=2, contract_size=50) == 600

def test_liquidity_score_rewards_liquid_quotes():
    assert liquidity_score(quote()) > 50
