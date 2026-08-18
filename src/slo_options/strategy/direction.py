from dataclasses import dataclass
from enum import Enum


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class DirectionSnapshot:
    direction: Direction
    score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    reason: str


def _clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def calculate_direction(
    spot: float,
    fast_ma: float,
    slow_ma: float,
    momentum_pct: float,
    hv: float | None = None,
    neutral_threshold: float = 15.0,
) -> DirectionSnapshot:
    """Transparent V1 directional score.

    This is a research baseline, not a validated trading edge. Numerical
    thresholds remain configurable research parameters for later backtesting.
    """
    if min(spot, fast_ma, slow_ma) <= 0:
        raise ValueError("spot and moving averages must be positive")

    trend_raw = (fast_ma - slow_ma) / slow_ma * 100.0
    trend_score = _clamp(trend_raw * 20.0)
    momentum_score = _clamp(momentum_pct * 10.0)

    if hv is None:
        volatility_score = 0.0
    else:
        # Volatility is deliberately a small modifier in V1 rather than a
        # standalone directional signal.
        volatility_score = _clamp((hv - 0.15) * 100.0, -20.0, 20.0)

    score = _clamp(0.55 * trend_score + 0.35 * momentum_score + 0.10 * volatility_score)

    if score >= neutral_threshold:
        direction = Direction.BULLISH
        reason = "Trend and momentum favor upside."
    elif score <= -neutral_threshold:
        direction = Direction.BEARISH
        reason = "Trend and momentum favor downside."
    else:
        direction = Direction.NEUTRAL
        reason = "Directional evidence is insufficient."

    return DirectionSnapshot(
        direction=direction,
        score=score,
        trend_score=trend_score,
        momentum_score=momentum_score,
        volatility_score=volatility_score,
        reason=reason,
    )
