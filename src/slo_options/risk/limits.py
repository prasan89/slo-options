from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_risk_per_trade_pct: float = 0.01
    max_capital_per_trade_pct: float = 0.10
    max_open_positions: int = 3
    max_portfolio_risk_pct: float = 0.03


def validate_portfolio_risk(
    capital: float,
    existing_risk: float,
    new_risk: float,
    open_positions: int,
    limits: RiskLimits,
) -> bool:
    if capital <= 0:
        raise ValueError("capital must be positive")
    if existing_risk < 0 or new_risk < 0:
        raise ValueError("risk cannot be negative")
    if open_positions >= limits.max_open_positions:
        return False
    total_risk_pct = (existing_risk + new_risk) / capital
    return total_risk_pct <= limits.max_portfolio_risk_pct
