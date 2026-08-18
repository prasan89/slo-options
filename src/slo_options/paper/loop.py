import os
import time
import uuid
from datetime import datetime, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from slo_options.analytics.volatility import historical_volatility
from slo_options.data.providers.upstox import UpstoxMarketDataProvider
from slo_options.paper.ledger import PaperLedger
from slo_options.strategy.candidate_engine import CandidateEngine
from slo_options.strategy.direction import calculate_direction
from slo_options.strategy.selector import Signal, select_trade


IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)


class LivePaperLoop:
    """Forward paper-trading loop using real market data and no order placement."""

    def __init__(self, output: str | Path = "reports/paper_trades.csv") -> None:
        self.provider = UpstoxMarketDataProvider()
        self.engine = CandidateEngine(self.provider)
        self.ledger = PaperLedger()
        self.output = Path(output)
        self.interval_seconds = int(os.getenv("SLO_PAPER_INTERVAL_SECONDS", "300"))

    @staticmethod
    def _now_ist() -> datetime:
        return datetime.now(IST)

    @classmethod
    def _is_market_open(cls) -> bool:
        current = cls._now_ist().time()
        return MARKET_OPEN <= current < MARKET_CLOSE

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

        # Manage existing positions during market hours using the bid.
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

        # Never open a new position outside market hours.
        if not self._is_market_open():
            return

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
                f"{self._now_ist().isoformat()} PAPER {trade.side} "
                f"{symbol} {quote.symbol} qty={trade.quantity} entry={entry:.2f} "
                f"stop={stop:.2f} target={target:.2f} score={score.total_score:.1f}"
            )
            break

    def _close_all_for_eod(self) -> None:
        """Close all remaining paper positions at the latest bid before/at 15:30 IST."""
        for trade in list(self.ledger.trades):
            if trade.exit_price is not None:
                continue
            chain = self.provider.get_option_chain(trade.underlying)
            quote = next((q for q in chain if q.symbol == trade.option_symbol), None)
            if quote is not None and quote.bid > 0:
                self.ledger.close(trade.trade_id, quote.bid, "EOD")

    def _open_trade(self, underlying: str, option_symbol: str, entry: float, stop: float, target: float):
        from slo_options.paper.ledger import PaperTrade

        quantity = int(os.getenv("SLO_PAPER_DEFAULT_QTY", "1"))
        item = PaperTrade(
            trade_id=uuid.uuid4().hex[:12],
            timestamp=self._now_ist().replace(tzinfo=None),
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
                now = self._now_ist()
                if self._is_market_open():
                    for symbol in self.provider.underlying_keys:
                        self._refresh_symbol(symbol)
                elif now.time() >= MARKET_CLOSE:
                    self._close_all_for_eod()

                self.ledger.export_csv(self.output)
            except Exception as exc:
                print(f"Paper loop error: {type(exc).__name__}: {exc}")
            time.sleep(self.interval_seconds)


def main() -> None:
    LivePaperLoop().run_forever()


if __name__ == "__main__":
    main()
