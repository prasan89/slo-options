from dataclasses import dataclass, asdict
from datetime import datetime
import csv
from pathlib import Path


@dataclass
class PaperTrade:
    trade_id: str
    timestamp: datetime
    underlying: str
    option_symbol: str
    side: str
    quantity: int
    entry_price: float
    stop_price: float
    target_price: float
    exit_price: float | None = None
    exit_reason: str | None = None

    @property
    def realized_pnl(self) -> float | None:
        if self.exit_price is None:
            return None
        return (self.exit_price - self.entry_price) * self.quantity


class PaperLedger:
    def __init__(self) -> None:
        self.trades: list[PaperTrade] = []

    def add(self, trade: PaperTrade) -> None:
        self.trades.append(trade)

    def close(self, trade_id: str, exit_price: float, reason: str) -> None:
        for trade in self.trades:
            if trade.trade_id == trade_id:
                if trade.exit_price is not None:
                    raise ValueError(f"Trade {trade_id} is already closed")
                trade.exit_price = exit_price
                trade.exit_reason = reason
                return
        raise KeyError(f"Trade {trade_id} not found")

    def realized_pnl(self) -> float:
        return sum((t.realized_pnl or 0.0) for t in self.trades)

    def export_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for trade in self.trades:
            row = asdict(trade)
            row["timestamp"] = trade.timestamp.isoformat()
            row["realized_pnl"] = trade.realized_pnl
            rows.append(row)
        if not rows:
            return
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
