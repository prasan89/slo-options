"""Japanese candlestick pattern detection used as a confirmation signal.

Patterns and terminology follow the candlestick chapter supplied with the project:
reversal, continuation, and indecision patterns. Detection is deliberately
structural; confirmation is exposed separately so the strategy can decide how
much weight to give a pattern.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def upper_shadow(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self) -> float:
        return min(self.open, self.close) - self.low


@dataclass(frozen=True)
class PatternSignal:
    name: str
    category: str
    direction: str
    requires_confirmation: bool
    confirmed: bool


def _small(c: Candle) -> bool:
    return c.range > 0 and c.body <= c.range * 0.35


def detect(candles: Sequence[Candle]) -> list[PatternSignal]:
    """Detect patterns in the most recent candles.

    Confirmation is based only on candles supplied after the pattern. A
    reversal pattern requiring next-period confirmation is not marked
    confirmed unless that candle is present and closes in the reversal
    direction.
    """
    if not candles:
        return []
    out: list[PatternSignal] = []
    c = candles[-1]

    if len(candles) >= 2:
        p = candles[-2]
        bullish_engulf = c.close > c.open and p.close < p.open and c.high >= p.high and c.low <= p.low
        bearish_engulf = c.close < c.open and p.close > p.open and c.high >= p.high and c.low <= p.low
        if bullish_engulf:
            out.append(PatternSignal("Bullish Engulfing", "reversal", "bullish", True, False))
        if bearish_engulf:
            out.append(PatternSignal("Bearish Engulfing", "reversal", "bearish", True, False))

        dark_cloud = p.close > p.open and c.open > p.close and c.close < (p.open + p.close) / 2 and c.close > p.open
        piercing = p.close < p.open and c.open < p.close and c.close > (p.open + p.close) / 2 and c.close < p.open
        if dark_cloud:
            out.append(PatternSignal("Dark Cloud Cover", "reversal", "bearish", True, False))
        if piercing:
            out.append(PatternSignal("Piercing Line", "reversal", "bullish", True, False))

        hammer = _small(c) and c.lower_shadow >= max(c.body * 2, c.range * 0.45) and c.upper_shadow <= c.range * 0.2
        hanging = hammer
        if hammer:
            out.append(PatternSignal("Hammer", "reversal", "bullish", True, False))
        if hanging:
            out.append(PatternSignal("Hanging Man", "reversal", "bearish", True, False))

    if len(candles) >= 3:
        a, b, d = candles[-3:]
        morning = a.close < a.open and _small(b) and d.close > d.open and d.close > (a.open + a.close) / 2
        evening = a.close > a.open and _small(b) and d.close < d.open and d.close < (a.open + a.close) / 2
        if morning:
            out.append(PatternSignal("Morning Star", "reversal", "bullish", False, True))
        if evening:
            out.append(PatternSignal("Evening Star", "reversal", "bearish", False, True))

        white_soldiers = all(x.close > x.open for x in (a, b, d)) and a.close < b.close < d.close
        black_crows = all(x.close < x.open for x in (a, b, d)) and a.close > b.close > d.close
        if white_soldiers:
            out.append(PatternSignal("Three Advancing White Soldiers", "continuation", "bullish", False, True))
        if black_crows:
            out.append(PatternSignal("Three Black Crows", "continuation", "bearish", False, True))

    if len(candles) >= 5:
        a, b, c2, d, e = candles[-5:]
        inside = all(x.body <= a.body and min(a.open, a.close) <= min(x.open, x.close) and max(x.open, x.close) <= max(a.open, a.close) for x in (b, c2, d))
        rising = a.close > a.open and inside and e.close > e.open and e.close > a.high
        falling = a.close < a.open and inside and e.close < e.open and e.close < a.low
        if rising:
            out.append(PatternSignal("Rising Three Methods", "continuation", "bullish", False, True))
        if falling:
            out.append(PatternSignal("Falling Three Methods", "continuation", "bearish", False, True))

    if c.range > 0 and c.body <= c.range * 0.1:
        out.append(PatternSignal("Doji", "indecision", "neutral", False, True))
    if _small(c) and c.upper_shadow > c.body and c.lower_shadow > c.body:
        out.append(PatternSignal("Spinning Top", "indecision", "neutral", False, True))

    if len(candles) >= 2:
        p = candles[-2]
        body_low, body_high = sorted((p.open, p.close))
        cur_low, cur_high = sorted((c.open, c.close))
        if cur_low >= body_low and cur_high <= body_high and c.body < p.body:
            direction = "bullish" if p.close < p.open else "bearish"
            out.append(PatternSignal("Harami", "indecision", direction, True, False))

    return out


def confirm(pattern: PatternSignal, confirmation_candle: Candle | None) -> PatternSignal:
    """Apply next-period confirmation for patterns that require it."""
    if not pattern.requires_confirmation or confirmation_candle is None:
        return pattern
    confirmed = (
        confirmation_candle.close > confirmation_candle.open
        if pattern.direction == "bullish"
        else confirmation_candle.close < confirmation_candle.open
    )
    return PatternSignal(pattern.name, pattern.category, pattern.direction, True, confirmed)
