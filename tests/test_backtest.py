from datetime import datetime, timedelta

from slo_options.backtest.engine import BacktestEngine
from slo_options.backtest.execution import ExecutionConfig, ExecutionModel
from slo_options.backtest.models import OptionBar, TradeSignal


def test_long_option_hits_target():
    t0 = datetime(2026, 1, 1)
    bars = [
        OptionBar(t0, "NIFTY-25000-CE", "NIFTY", 100, 99, 101),
        OptionBar(t0 + timedelta(days=1), "NIFTY-25000-CE", "NIFTY", 130, 129, 131),
    ]
    signals = [
        TradeSignal(
            timestamp=t0,
            option_symbol="NIFTY-25000-CE",
            action="BUY",
            quantity=1,
            entry_price=100,
            stop_price=65,
            target_price=125,
            max_holding_days=5,
        )
    ]
    result = BacktestEngine(
        10000,
        ExecutionModel(ExecutionConfig(slippage_pct=0.0)),
    ).run(bars, signals)

    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "TARGET"
    assert result.total_pnl > 0


def test_long_option_hits_stop():
    t0 = datetime(2026, 1, 1)
    bars = [
        OptionBar(t0, "NIFTY-25000-PE", "NIFTY", 100, 99, 101),
        OptionBar(t0 + timedelta(days=1), "NIFTY-25000-PE", "NIFTY", 60, 59, 61),
    ]
    signals = [
        TradeSignal(
            timestamp=t0,
            option_symbol="NIFTY-25000-PE",
            action="BUY",
            quantity=1,
            entry_price=100,
            stop_price=65,
            target_price=150,
            max_holding_days=5,
        )
    ]
    result = BacktestEngine(
        10000,
        ExecutionModel(ExecutionConfig(slippage_pct=0.0)),
    ).run(bars, signals)

    assert len(result.trades) == 1
    assert result.trades[0].exit_reason == "STOP"
    assert result.total_pnl < 0
