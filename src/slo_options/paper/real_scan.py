import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from slo_options.analytics.volatility import historical_volatility
from slo_options.data.providers.upstox import UpstoxMarketDataProvider
from slo_options.strategy.candidate_engine import CandidateEngine
from slo_options.strategy.direction import calculate_direction
from slo_options.strategy.selector import select_trade


def _lot_sizes() -> dict[str, int]:
    raw = os.getenv("SLO_LOT_SIZES", "{}")
    value = json.loads(raw)
    return {str(k): int(v) for k, v in value.items()}


def scan_once(output: str | Path = "reports/paper_signals.csv") -> list[dict]:
    provider = UpstoxMarketDataProvider()
    symbols = list(provider.underlying_keys)
    lots = _lot_sizes()
    rows: list[dict] = []

    for symbol in symbols:
        closes = provider.get_historical_closes(symbol, days=80)
        if len(closes) < 55:
            continue

        prices = pd.Series([p for _, p in closes])
        spot = float(prices.iloc[-1])
        fast_ma = float(prices.tail(20).mean())
        slow_ma = float(prices.tail(50).mean())
        momentum_pct = float((prices.iloc[-1] / prices.iloc[-6] - 1.0) * 100.0)
        hv = historical_volatility(prices, window=20)
        direction = calculate_direction(spot, fast_ma, slow_ma, momentum_pct, hv=hv)

        engine = CandidateEngine(provider)
        candidates = engine.scan(symbol, direction_score=direction.score, hv=hv)

        selected = None
        for analytics, score in candidates:
            candidate = select_trade(direction.direction, analytics, score)
            if candidate.signal.value != "NO_TRADE":
                selected = candidate
                break

        row = {
            "timestamp": datetime.now().isoformat(),
            "underlying": symbol,
            "spot": spot,
            "direction": direction.direction.value,
            "direction_score": direction.score,
            "hv": hv,
            "option_symbol": selected.option_symbol if selected else None,
            "signal": selected.signal.value if selected else "NO_TRADE",
            "entry_premium": selected.entry_premium if selected else None,
            "stop_premium": selected.stop_premium if selected else None,
            "target_premium": selected.target_premium if selected else None,
            "lot_size": lots.get(symbol),
            "reason": selected.reason if selected else "No candidate selected.",
        }
        rows.append(row)

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return rows


def main() -> None:
    rows = scan_once()
    for row in rows:
        print(
            f"{row['underlying']}: {row['signal']} "
            f"score={row['direction_score']:.1f} "
            f"option={row['option_symbol']} entry={row['entry_premium']}"
        )


if __name__ == "__main__":
    main()
