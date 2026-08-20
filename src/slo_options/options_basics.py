"""Core option-contract calculations used by the SLO option-selection layer."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    option_type: str
    strike: float
    expiry: str
    ltp: float
    bid: float | None = None
    ask: float | None = None
    volume: int = 0
    open_interest: int = 0
    implied_volatility: float | None = None
    delta: float | None = None

    @property
    def spread(self) -> float | None:
        if self.bid is None or self.ask is None: return None
        return max(0.0, self.ask - self.bid)

    @property
    def spread_pct(self) -> float | None:
        if self.spread is None or self.ltp <= 0: return None
        return self.spread / self.ltp * 100

def intrinsic_value(spot: float, strike: float, option_type: str) -> float:
    kind = option_type.upper()
    if kind == "CALL": return max(spot - strike, 0.0)
    if kind == "PUT": return max(strike - spot, 0.0)
    raise ValueError("option_type must be CALL or PUT")

def time_value(quote: OptionQuote, spot: float) -> float:
    return max(0.0, quote.ltp - intrinsic_value(spot, quote.strike, quote.option_type))

def moneyness(spot: float, strike: float, option_type: str) -> str:
    kind = option_type.upper()
    if abs(spot - strike) / max(spot, 1e-12) <= 0.005: return "ATM"
    if kind == "CALL": return "ITM" if spot > strike else "OTM"
    if kind == "PUT": return "ITM" if strike > spot else "OTM"
    raise ValueError("option_type must be CALL or PUT")

def option_cost(quote: OptionQuote, contracts: int = 1, contract_size: int = 1) -> float:
    if contracts <= 0 or contract_size <= 0: raise ValueError("contracts and contract_size must be positive")
    return quote.ltp * contracts * contract_size

def liquidity_score(quote: OptionQuote, max_spread_pct: float = 5.0) -> float:
    volume_score = min(40.0, quote.volume / 1000.0)
    oi_score = min(40.0, quote.open_interest / 5000.0)
    spread_score = 20.0
    if quote.spread_pct is not None:
        spread_score = max(0.0, 20.0 * (1.0 - quote.spread_pct / max_spread_pct))
    return min(100.0, volume_score + oi_score + spread_score)

def select_candidates(quotes: list[OptionQuote], spot: float, direction: str, *, max_spread_pct: float = 5.0) -> list[OptionQuote]:
    """Rank liquid candidates; never places orders."""
    kind = "CALL" if direction.lower() in {"bullish", "call", "long"} else "PUT"
    candidates = [q for q in quotes if q.option_type.upper() == kind and q.ltp > 0]
    return sorted(candidates, key=lambda q: (liquidity_score(q, max_spread_pct), q.open_interest, q.volume), reverse=True)
