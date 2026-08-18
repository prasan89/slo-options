from dataclasses import dataclass

from slo_options.analytics.candidate import OptionAnalytics


@dataclass(frozen=True)
class CandidateScore:
    symbol: str
    direction_score: float
    liquidity_score: float
    theta_score: float
    volatility_score: float
    total_score: float


def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def score_candidate(a: OptionAnalytics, direction_score: float):
    direction = _clamp(direction_score)
    liquidity = _clamp(100 * (1 - a.spread_pct / 0.10))
    theta_ratio = abs(a.theta_per_day) / max(a.premium, 0.01)
    theta_score = _clamp(100 * (1 - theta_ratio / 0.10))
    volatility = 50.0 if a.iv_hv_ratio is None else _clamp(100 - abs(a.iv_hv_ratio - 1.0) * 100)
    total = 0.45 * direction + 0.20 * liquidity + 0.20 * theta_score + 0.15 * volatility
    return CandidateScore(a.symbol, direction, liquidity, theta_score, volatility, total)
