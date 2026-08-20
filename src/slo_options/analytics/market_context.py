"""Market regime, relative strength and expected-range analytics."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Mapping, Sequence

def _pct(a: float, b: float) -> float:
    return 0.0 if b == 0 else (a / b - 1.0) * 100.0

@dataclass(frozen=True)
class MarketRegime:
    label: str
    score: int
    return_20d: float
    above_sma20: bool
    above_sma50: bool

def market_regime(closes: Sequence[float]) -> MarketRegime | None:
    if len(closes) < 50: return None
    p = closes[-1]; sma20 = sum(closes[-20:]) / 20; sma50 = sum(closes[-50:]) / 50
    ret20 = _pct(p, closes[-21])
    score = int(p > sma20) + int(p > sma50) + int(sma20 > sma50) + int(ret20 > 0)
    label = "bullish" if score >= 3 else "bearish" if score <= 1 else "neutral"
    return MarketRegime(label, score, ret20, p > sma20, p > sma50)

@dataclass(frozen=True)
class RelativeStrength:
    stock_return: float
    benchmark_return: float
    relative_return: float
    rank_score: float

def relative_strength(stock_closes: Sequence[float], benchmark_closes: Sequence[float], period: int = 20) -> RelativeStrength | None:
    if len(stock_closes) <= period or len(benchmark_closes) <= period: return None
    sr = _pct(stock_closes[-1], stock_closes[-period-1]); br = _pct(benchmark_closes[-1], benchmark_closes[-period-1])
    return RelativeStrength(sr, br, sr - br, max(0.0, min(100.0, 50.0 + (sr - br) * 5.0)))

def rank_strength(relative_returns: Mapping[str, float]) -> dict[str, float]:
    if not relative_returns: return {}
    ordered = sorted(relative_returns, key=relative_returns.get); n = len(ordered)
    return {s: 50.0 if n == 1 else 100.0 * i / (n - 1) for i, s in enumerate(ordered)}

@dataclass(frozen=True)
class ExpectedRange:
    center: float
    lower: float
    upper: float
    move_pct: float
    method: str

def expected_range(closes: Sequence[float], period: int = 20, deviations: float = 1.0) -> ExpectedRange | None:
    """Estimate a price area from recent return volatility, not an exact forecast."""
    if len(closes) <= period: return None
    window = closes[-period:]; returns = [window[i] / window[i-1] - 1.0 for i in range(1, len(window)) if window[i-1] != 0]
    if not returns: return None
    mean = sum(returns) / len(returns); sd = sqrt(sum((x - mean) ** 2 for x in returns) / len(returns))
    center = closes[-1] * (1.0 + mean); move = abs(sd * deviations)
    return ExpectedRange(center, center * (1.0 - move), center * (1.0 + move), move * 100.0, "20d_return_volatility")

def context_score(regime: MarketRegime | None, relative: RelativeStrength | None, expected: ExpectedRange | None, direction: str) -> float:
    """Context confirmation score; never creates a trade by itself."""
    score = 50.0
    if regime:
        if direction == "bullish": score += 15 if regime.label == "bullish" else -15 if regime.label == "bearish" else 0
        elif direction == "bearish": score += 15 if regime.label == "bearish" else -15 if regime.label == "bullish" else 0
    if relative: score += (relative.rank_score - 50.0) * (0.25 if direction == "bullish" else -0.25)
    if expected and expected.move_pct >= 1.0: score += 5
    return max(0.0, min(100.0, score))
