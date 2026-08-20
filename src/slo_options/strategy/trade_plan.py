"""End-to-end, read-only trade-plan construction for paper trading."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from slo_options.analytics.fibonacci import levels
from slo_options.analytics.indicators import bollinger, indicator_state, rsi

class PlanStatus(str, Enum):
    WATCH = "WATCH"
    TRIGGERED = "TRIGGERED"
    NO_TRADE = "NO_TRADE"

@dataclass(frozen=True)
class TradePlan:
    underlying: str
    direction: str
    score: float
    driver: str
    trigger: float
    stop: float
    target: float
    expected_move_pct: float
    max_loss: float
    reward_risk: float
    funding: str
    risk_limiter: str
    status: PlanStatus
    reasons: tuple[str, ...]


def build_trade_plan(symbol: str, spot: float, direction: str, direction_score: float, closes: list[float], capital: float = 1_500_000.0, risk_pct: float = .02) -> TradePlan:
    if len(closes) < 50 or spot <= 0:
        return TradePlan(symbol, direction, direction_score, "NONE", spot, spot, spot, 0, 0, 0, "NONE", "NONE", PlanStatus.NO_TRADE, ("Insufficient history",))
    states = indicator_state(closes)
    r = rsi(closes) or 50.0
    b = bollinger(closes)
    recent = closes[-50:]
    fib = levels(min(recent), max(recent))
    reasons: list[str] = []
    if direction == "BULLISH":
        if states.get("rsi") == "bullish": reasons.append("RSI confirms upside")
        if states.get("macd") == "bullish": reasons.append("MACD confirms upside")
        if states.get("trend") == "bullish": reasons.append("50/200 trend is bullish")
        trigger = max(spot, fib.high)
        stop = min(fib.retracement_618, spot * .985)
        target = fib.extension_1272
        driver, funding = "LONG CALL", "CALL SPREAD"
        risk_limiter = "Defined-risk debit structure"
    elif direction == "BEARISH":
        if states.get("rsi") == "bearish": reasons.append("RSI confirms downside")
        if states.get("macd") == "bearish": reasons.append("MACD confirms downside")
        if states.get("trend") == "bearish": reasons.append("50/200 trend is bearish")
        trigger = min(spot, fib.low)
        stop = max(fib.retracement_382, spot * 1.015)
        target = fib.low - (fib.high - fib.low) * .272
        driver, funding = "LONG PUT", "PUT SPREAD"
        risk_limiter = "Defined-risk debit structure"
    else:
        return TradePlan(symbol, direction, direction_score, "NONE", spot, spot, spot, 0, 0, 0, "NONE", "NONE", PlanStatus.NO_TRADE, ("Neutral direction",))
    max_loss = capital * risk_pct
    reward_risk = abs(target - spot) / max(abs(spot - stop), 1e-9)
    expected_move_pct = abs(target - spot) / spot * 100
    confirmed = len(reasons) >= 2 and reward_risk >= 2.0
    reasons.append(f"RSI={r:.1f}")
    if b: reasons.append(f"BB width={b.bandwidth:.3f}")
    status = PlanStatus.WATCH if confirmed else PlanStatus.NO_TRADE
    return TradePlan(symbol, direction, direction_score, driver, trigger, stop, target, expected_move_pct, max_loss, reward_risk, funding, risk_limiter, status, tuple(reasons))
