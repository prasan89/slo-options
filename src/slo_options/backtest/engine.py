from dataclasses import dataclass
from typing import Iterable

from slo_options.backtest.execution import ExecutionModel
from slo_options.backtest.models import BacktestResult, CompletedTrade, OptionBar, TradeSignal


@dataclass
class _OpenPosition:
    signal: TradeSignal
    entry_price: float
    entry_cost: float


class BacktestEngine:
    """Minimal event-driven simulator for long-option strategies."""

    def __init__(self, starting_capital: float, execution: ExecutionModel | None = None):
        if starting_capital <= 0:
            raise ValueError("starting_capital must be positive")
        self.starting_capital = starting_capital
        self.execution = execution or ExecutionModel()

    def run(
        self,
        bars: Iterable[OptionBar],
        signals: Iterable[TradeSignal],
    ) -> BacktestResult:
        bars_by_symbol = {}
        for bar in bars:
            bars_by_symbol.setdefault(bar.symbol, []).append(bar)
        for symbol_bars in bars_by_symbol.values():
            symbol_bars.sort(key=lambda x: x.timestamp)

        signal_list = sorted(signals, key=lambda x: x.timestamp)
        trades: list[CompletedTrade] = []
        capital = self.starting_capital
        equity_curve = [capital]

        for signal in signal_list:
            symbol_bars = bars_by_symbol.get(signal.option_symbol, [])
            if not symbol_bars:
                continue

            entry_bar = next((b for b in symbol_bars if b.timestamp >= signal.timestamp), None)
            if entry_bar is None:
                continue

            entry_price = self.execution.buy_price(entry_bar.ask)
            entry_cost = self.execution.cost(signal.quantity)
            invested = entry_price * signal.quantity + entry_cost
            if invested > capital:
                continue

            exit_bar = None
            exit_reason = None
            for bar in symbol_bars:
                if bar.timestamp <= entry_bar.timestamp:
                    continue

                if bar.close <= signal.stop_price:
                    exit_bar = bar
                    exit_reason = "STOP"
                    break
                if bar.close >= signal.target_price:
                    exit_bar = bar
                    exit_reason = "TARGET"
                    break

                days_held = (bar.timestamp.date() - entry_bar.timestamp.date()).days
                if days_held >= signal.max_holding_days:
                    exit_bar = bar
                    exit_reason = "TIME"
                    break

            if exit_bar is None:
                exit_bar = symbol_bars[-1]
                exit_reason = "END_OF_DATA"

            exit_price = self.execution.sell_price(exit_bar.bid)
            gross = (exit_price - entry_price) * signal.quantity
            costs = entry_cost + self.execution.cost(signal.quantity)
            net = gross - costs
            capital += net
            equity_curve.append(capital)

            trades.append(
                CompletedTrade(
                    option_symbol=signal.option_symbol,
                    entry_time=entry_bar.timestamp,
                    exit_time=exit_bar.timestamp,
                    quantity=signal.quantity,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    gross_pnl=gross,
                    costs=costs,
                    net_pnl=net,
                    exit_reason=exit_reason,
                )
            )

        total_pnl = capital - self.starting_capital
        peak = self.starting_capital
        max_dd = 0.0
        for value in equity_curve:
            peak = max(peak, value)
            if peak > 0:
                max_dd = max(max_dd, (peak - value) / peak)

        wins = [t.net_pnl for t in trades if t.net_pnl > 0]
        losses = [t.net_pnl for t in trades if t.net_pnl < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
        win_rate = 100.0 * len(wins) / len(trades) if trades else 0.0

        return BacktestResult(
            starting_capital=self.starting_capital,
            ending_capital=capital,
            total_pnl=total_pnl,
            return_pct=100.0 * total_pnl / self.starting_capital,
            max_drawdown_pct=100.0 * max_dd,
            win_rate_pct=win_rate,
            profit_factor=profit_factor,
            trades=tuple(trades),
        )
