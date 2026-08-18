from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class PositionSize:
    quantity: int
    premium_capital: float
    max_loss: float
    risk_per_unit: float
    lots: int


def calculate_position_size(
    capital: float,
    entry_premium: float,
    stop_premium: float,
    lot_size: int,
    risk_per_trade_pct: float | None = None,
    max_capital_pct: float = 0.10,
    allocation_per_trade: float | None = None,
) -> PositionSize:
    """Size a long-option position from allocation and an optional risk cap."""
    if capital <= 0 or entry_premium <= 0:
        raise ValueError("capital and entry_premium must be positive")
    if lot_size <= 0:
        raise ValueError("lot_size must be positive")
    if risk_per_trade_pct is not None and not 0 < risk_per_trade_pct < 1:
        raise ValueError("risk_per_trade_pct must be between 0 and 1")
    if not 0 < max_capital_pct <= 1:
        raise ValueError("max_capital_pct must be in (0, 1]")
    if stop_premium < 0 or stop_premium >= entry_premium:
        raise ValueError("stop_premium must be >= 0 and below entry premium")
    if allocation_per_trade is not None and allocation_per_trade <= 0:
        raise ValueError("allocation_per_trade must be positive")

    capital_budget = min(
        capital * max_capital_pct,
        allocation_per_trade if allocation_per_trade is not None else capital * max_capital_pct,
    )

    premium_per_lot = entry_premium * lot_size
    risk_per_lot = (entry_premium - stop_premium) * lot_size
    by_capital = floor(capital_budget / premium_per_lot)

    if risk_per_trade_pct is None:
        lots = by_capital
    else:
        risk_budget = capital * risk_per_trade_pct
        by_risk = floor(risk_budget / risk_per_lot)
        lots = min(by_risk, by_capital)

    return PositionSize(
        quantity=lots * lot_size,
        premium_capital=lots * premium_per_lot,
        max_loss=lots * risk_per_lot,
        risk_per_unit=entry_premium - stop_premium,
        lots=lots,
    )
