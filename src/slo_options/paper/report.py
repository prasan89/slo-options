from dataclasses import dataclass
from typing import Iterable

from slo_options.paper.ledger import PaperTrade


@dataclass(frozen=True)
class PaperReport:
    trades: int
    closed_trades: int
    open_trades: int
    pnl: float
    win_rate: float
    profit_factor: float


def build_report(trades: Iterable[PaperTrade]) -> PaperReport:
    items = list(trades)
    closed = [t for t in items if t.exit_price is not None]
    wins = [t.realized_pnl for t in closed if (t.realized_pnl or 0) > 0]
    losses = [t.realized_pnl for t in closed if (t.realized_pnl or 0) < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = float("inf") if gross_loss == 0 and gross_profit > 0 else (gross_profit / gross_loss if gross_loss else 0.0)
    win_rate = len(wins) / len(closed) if closed else 0.0
    return PaperReport(
        trades=len(items),
        closed_trades=len(closed),
        open_trades=len(items) - len(closed),
        pnl=sum((t.realized_pnl or 0.0) for t in items),
        win_rate=win_rate,
        profit_factor=profit_factor,
    )
