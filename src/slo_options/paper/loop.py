import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from slo_options.analytics.volatility import historical_volatility
from slo_options.data.providers.upstox import UpstoxMarketDataProvider
from slo_options.paper.ledger import PaperLedger, PaperTrade
from slo_options.risk.position_sizing import calculate_position_size
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
        self.capital = float(os.getenv("SLO_PAPER_CAPITAL", "500000"))
        self.lot_sizes = json.loads(os.getenv("SLO_LOT_SIZES", "{}"))

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

        for trade in list(self.ledger.trades):
            if trade.underlying != symbol or trade.exit_price is not None:
                continue
            quote = by_symbol.get(trade.option_symbol)
            if quote is None or quote.bid <= 0:
                continue
            if quote.bid <= trade.stop_price:
                self.ledger.close(trade.trade_id, quote.bid, "STOP")
            elif quote.bid >= trade.target_price:
                self.ledger.close(trade.trade_id, quote.bid, "TARGET")

        if any(t.underlying == symbol and t.exit_price is None for t in self.ledger.trades):
            return

        candidates = self.engine.scan(symbol, direction_score=direction.score, hv=hv)
        for analytics, score in candidates:
            signal = select_trade(direction.direction, analytics, score)
            if signal.signal == Signal.NO_TRADE:
                continue

            quote = by_symbol.get(signal.option_symbol)
            lot_size = int(self.lot_sizes.get(symbol, 0))
            if quote is None or quote.ask <= 0 or lot_size <= 0:
                continue

            entry = quote.ask
            stop = entry * (1.0 - 0.35)
            target = entry * (1.0 + 0.50)
            sizing = calculate_position_size(
                capital=self.capital,
                entry_premium=entry,
                stop_premium=stop,
                lot_size=lot_size,
                risk_per_trade_pct=0.01,
                max_capital_pct=0.10,
            )
            if sizing.quantity <= 0:
                continue

            trade = PaperTrade(
                trade_id=uuid.uuid4().hex[:12],
                timestamp=datetime.now(),
                underlying=symbol,
                option_symbol=quote.symbol,
                side="BUY",
                quantity=sizing.quantity,
                entry_price=entry,
                stop_price=stop,
                target_price=target,
            )
            self.ledger.add(trade)
            print(
                f"{datetime.now().isoformat()} PAPER BUY {symbol} {quote.symbol} "
                f"qty={trade.quantity} entry={entry:.2f} stop={stop:.2f} "
                f"target={target:.2f} score={score.total_score:.1f} max_loss={sizing.max_loss:.0f}"
            )
            break

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
