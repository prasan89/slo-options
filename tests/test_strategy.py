from datetime import datetime, timedelta

from slo_options.analytics.candidate import analyze_option
from slo_options.data.providers.mock import MockMarketDataProvider
from slo_options.models.market import OptionType
from slo_options.strategy.direction import Direction, calculate_direction
from slo_options.strategy.scoring import CandidateScore
from slo_options.strategy.selector import Signal, select_trade


def test_direction_bullish():
    snapshot = calculate_direction(
        spot=100,
        fast_ma=102,
        slow_ma=100,
        momentum_pct=1.5,
        hv=0.18,
    )
    assert snapshot.direction == Direction.BULLISH
    assert snapshot.score > 15


def test_direction_bearish():
    snapshot = calculate_direction(
        spot=100,
        fast_ma=98,
        slow_ma=100,
        momentum_pct=-1.5,
        hv=0.12,
    )
    assert snapshot.direction == Direction.BEARISH
    assert snapshot.score < -15


def test_direction_neutral():
    snapshot = calculate_direction(
        spot=100,
        fast_ma=100.05,
        slow_ma=100,
        momentum_pct=0.0,
    )
    assert snapshot.direction == Direction.NEUTRAL


def test_long_call_only_when_bullish():
    provider = MockMarketDataProvider()
    option = next(o for o in provider.get_option_chain("NIFTY") if o.option_type == OptionType.CALL)
    analytics = analyze_option(option, provider.get_underlying("NIFTY").spot, hv=0.15)
    score = CandidateScore(option.symbol, 90, 90, 90, 90, 90)

    signal = select_trade(Direction.BULLISH, analytics, score)

    assert signal.signal == Signal.BUY_CALL
    assert signal.stop_premium < signal.entry_premium < signal.target_premium


def test_long_put_only_when_bearish():
    provider = MockMarketDataProvider()
    option = next(o for o in provider.get_option_chain("NIFTY") if o.option_type == OptionType.PUT)
    analytics = analyze_option(option, provider.get_underlying("NIFTY").spot, hv=0.15)
    score = CandidateScore(option.symbol, 90, 90, 90, 90, 90)

    signal = select_trade(Direction.BEARISH, analytics, score)

    assert signal.signal == Signal.BUY_PUT


def test_no_trade_when_direction_mismatches_option_type():
    provider = MockMarketDataProvider()
    option = next(o for o in provider.get_option_chain("NIFTY") if o.option_type == OptionType.PUT)
    analytics = analyze_option(option, provider.get_underlying("NIFTY").spot, hv=0.15)
    score = CandidateScore(option.symbol, 90, 90, 90, 90, 90)

    signal = select_trade(Direction.BULLISH, analytics, score)

    assert signal.signal == Signal.NO_TRADE
