"""Combines macro, relative-strength, expected-range and fundamental context."""
from __future__ import annotations
from dataclasses import dataclass
from slo_options.analytics.fundamental import FundamentalSnapshot, event_risk, risk_multiplier
from slo_options.analytics.market_context import ExpectedRange, MarketRegime, RelativeStrength, context_score

@dataclass(frozen=True)
class TradeContext:
    regime: str
    relative_strength: float
    expected_lower: float | None
    expected_upper: float | None
    fundamental_score: float
    event_risk: str
    risk_multiplier: float
    context_score: float

def build_context(regime: MarketRegime | None, relative: RelativeStrength | None, expected: ExpectedRange | None, fundamental: FundamentalSnapshot | None, direction: str, high_impact_event: bool = False) -> TradeContext:
    days = fundamental.earnings_days if fundamental else None
    erisk = event_risk(days, high_impact_event)
    return TradeContext(regime=regime.label if regime else "unknown", relative_strength=relative.relative_return if relative else 0.0, expected_lower=expected.lower if expected else None, expected_upper=expected.upper if expected else None, fundamental_score=fundamental.score() if fundamental else 50.0, event_risk=erisk, risk_multiplier=risk_multiplier(erisk), context_score=context_score(regime, relative, expected, direction))
