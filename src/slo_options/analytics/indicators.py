"""RSI, MACD, Bollinger Bands and moving averages for SLO confirmation."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Sequence

def sma(values: Sequence[float], period: int) -> float | None:
    if period <= 0 or len(values) < period: return None
    return sum(values[-period:]) / period

def ema(values: Sequence[float], period: int) -> float | None:
    if period <= 0 or len(values) < period: return None
    value = sum(values[:period]) / period
    alpha = 2 / (period + 1)
    for x in values[period:]: value = alpha * x + (1 - alpha) * value
    return value

def rsi(closes: Sequence[float], period: int = 14) -> float | None:
    if period <= 0 or len(closes) <= period: return None
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(x, 0.0) for x in changes]; losses = [max(-x, 0.0) for x in changes]
    gain = sum(gains[:period]) / period; loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        gain = (gain * (period - 1) + g) / period; loss = (loss * (period - 1) + l) / period
    return 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)

@dataclass(frozen=True)
class MACDResult:
    macd: float; signal: float; histogram: float

def macd(closes: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> MACDResult | None:
    if len(closes) < slow + signal - 1: return None
    series = []
    for i in range(slow, len(closes) + 1):
        f, s = ema(closes[:i], fast), ema(closes[:i], slow)
        if f is not None and s is not None: series.append(f - s)
    sig = ema(series, signal)
    if not series or sig is None: return None
    line = series[-1]
    return MACDResult(line, sig, line - sig)

@dataclass(frozen=True)
class BollingerResult:
    middle: float; upper: float; lower: float; bandwidth: float

def bollinger(closes: Sequence[float], period: int = 20, deviations: float = 2.0) -> BollingerResult | None:
    if len(closes) < period: return None
    window = closes[-period:]; middle = sum(window) / period
    sd = sqrt(sum((x - middle) ** 2 for x in window) / period)
    upper, lower = middle + deviations * sd, middle - deviations * sd
    return BollingerResult(middle, upper, lower, (upper - lower) / middle if middle else 0.0)

@dataclass(frozen=True)
class MovingAverageResult:
    sma20: float | None; sma50: float | None; sma100: float | None; sma200: float | None
    ema9: float | None; ema12: float | None; ema26: float | None

def moving_averages(closes: Sequence[float]) -> MovingAverageResult:
    return MovingAverageResult(sma(closes,20), sma(closes,50), sma(closes,100), sma(closes,200), ema(closes,9), ema(closes,12), ema(closes,26))

def indicator_state(closes: Sequence[float]) -> dict[str, str]:
    """Conservative confirmation labels; these indicators do not create trades alone."""
    out: dict[str, str] = {}; value = rsi(closes)
    if value is not None: out['rsi'] = 'bullish' if value > 60 else 'bearish' if value < 40 else 'neutral'
    m = macd(closes)
    if m: out['macd'] = 'bullish' if m.macd > m.signal else 'bearish' if m.macd < m.signal else 'neutral'
    b = bollinger(closes)
    if b:
        p = closes[-1]; out['bollinger'] = 'upper_break' if p > b.upper else 'lower_break' if p < b.lower else 'inside'
    ma = moving_averages(closes)
    if ma.sma20 is not None: out['sma20'] = 'above' if closes[-1] > ma.sma20 else 'below'
    if ma.sma50 is not None and ma.sma200 is not None: out['trend'] = 'bullish' if ma.sma50 > ma.sma200 else 'bearish'
    return out
