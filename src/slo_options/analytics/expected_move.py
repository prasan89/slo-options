from math import sqrt


def expected_move(spot: float, annualized_volatility: float, trading_days: int = 1) -> float:
    if spot <= 0 or annualized_volatility < 0 or trading_days <= 0:
        raise ValueError("invalid inputs")
    return spot * annualized_volatility * sqrt(trading_days / 252)


def expected_move_pct(annualized_volatility: float, trading_days: int = 1) -> float:
    if annualized_volatility < 0 or trading_days <= 0:
        raise ValueError("invalid inputs")
    return annualized_volatility * sqrt(trading_days / 252)
