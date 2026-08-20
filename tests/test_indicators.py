from slo_options.analytics.indicators import bollinger, ema, indicator_state, macd, rsi, sma

def test_sma_ema():
    values = [1,2,3,4,5]
    assert sma(values, 3) == 4
    assert ema(values, 3) is not None

def test_rsi_range():
    value = rsi(list(range(1, 40)))
    assert value is not None and 0 <= value <= 100

def test_macd_and_bollinger():
    values = [100 + i * 0.5 for i in range(60)]
    assert macd(values) is not None
    bands = bollinger(values)
    assert bands is not None and bands.upper >= bands.middle >= bands.lower

def test_indicator_state_is_confirmation_only():
    values = [100 + i * 0.5 for i in range(220)]
    state = indicator_state(values)
    assert state['rsi'] == 'bullish'
    assert state['trend'] == 'bullish'
