import os
import time
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from slo_options.analytics.volatility import historical_volatility
from slo_options.data.providers.upstox import UpstoxMarketDataProvider
from slo_options.paper.ledger import PaperLedger
from slo_options.strategy.candidate_engine import CandidateEngine
from slo_options.strategy.direction import calculate_direction
from slo_options.strategy.selector import Signal, select_trade


class LivePaperLoop:
    """Forward paper-trading loop using real market data and no order placement."""

    def __init__(self, output: str | Path = "reports/paper_trades.csv") -> None:
        self.provider = UpstoxMarketDataProvider()
        self.engine = CandidateEngine(self.provider)
        self.ledger = PaperLedger()
        self.output = Path(output)
        self.interval_seconds = int(os.getenv("SLO_PAPER_INTERVAL_SECONDS", "300"))

    def _refresh_symbol(self, symbol: str) -> None:
        closes = self.provider.get_historical_closes(symbol, days=80)
        if len(closes) < 55:
            return

        prices = pd.Series([value for _, value in closes])
        spot = float(prices.iloc[-1])
        fast_ma = float(prices.tail(20).mean())
        slow_ma = float(prices.tail(50).mean())
        momentum_pct = float((prices.iloc[-1] / prices.iloc[-6] - 1.0) * 100.0)
        hv = historical_volatility(prices, window=20)
        direction = calculate_direction(spot, fast_ma, slow_ma, momentum_pct, hv=hv)

        chain = self.provider.get_option_chain(symbol)
        by_symbol = {option.symbol: option for option in chain}

        # First manage existing open paper positions.
        for trade in list(self.ledger.trades):
            if trade.underlying != symbol or trade.exit_price is not None:
                continue
            quote = by_symbol.get(trade.option_symbol)
            if quote is None:
                continue
            price = quote.bid
            if price <= 0:
                continue
            if price <= trade.stop_price:
                self.ledger.close(trade.trade_id, price, "STOP")
            elif price >= trade.target_price:
                self.ledger.close(trade.trade_id, price, "TARGET")

        # Only one open position per underlying in V1.
        if any(t.underlying == symbol and t.exit_price is None for t in self.ledger.trades):
            return

        candidates = self.engine.scan(symbol, direction_score=direction.score, hv=hv)
        for analytics, score in candidates:
            signal = select_trade(direction.direction, analytics, score)
            if signal.signal == Signal.NO_TRADE:
                continue
            quote = by_symbol.get(signal.option_symbol)
            if quote is None or quote.ask <= 0:
                continue

            entry = quote.ask
            stop = entry * (1.0 - 0.35)
            target = entry * (1.0 + 0.50)
            trade = self._open_trade(symbol, quote.symbol, entry, stop, target)
            print(
                f"{datetime.now().isoformat()} PAPER {trade.side} "
                f"{symbol} {quote.symbol} qty={trade.quantity} entry={entry:.2f} "
                f"stop={stop:.2f} target={target:.2f} score={score.total_score:.1f}"
            )
            break

    def _open_trade(self, underlying: str, option_symbol: str, entry: float, stop: float, target: float):
        trade = self.ledger.trades
        quantity = int(os.getenv("SLO_PAPER_DEFAULT_QTY", "1"))
        from slo_options.paper.ledger import PaperTrade
        item = PaperTrade(
            trade_id=uuid.uuid4().hex[:12],
            timestamp=datetime.now(),
            underlying=underlying,
            option_symbol=option_symbol,
            side="BUY",
            quantity=quantity,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
        )
        self.ledger.add(item)
        return item

    def run_forever(self) -> None:
        print("SLO real-data paper trading started. No broker orders will be placed.")
        while True:
            try:
                for symbol in self.provider.underlying_keys:
                    self._refresh_symbol(symbol)
                self.ledger.export_csv(self.output)
            except Exception as exc:
                print(f"Paper loop error: {type(exc).__name__}: {exc}")
            time.sleep(self.interval_seconds)


def main() -> None:
    LivePaperLoop().run_forever()


if __name__ == "__main__":
    main()
