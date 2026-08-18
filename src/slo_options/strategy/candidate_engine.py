from datetime import datetime

from slo_options.analytics.candidate import analyze_option
from slo_options.data.providers.base import MarketDataProvider
from slo_options.strategy.config import StrategyConfig
from slo_options.strategy.scanner import filter_liquid_candidates
from slo_options.strategy.scoring import CandidateScore, score_candidate


class CandidateEngine:
    def __init__(self, provider: MarketDataProvider, config: StrategyConfig | None = None):
        self.provider = provider
        self.config = config or StrategyConfig()

    def scan(
        self,
        underlying: str,
        direction_score: float,
        hv: float | None = None,
        expiry: datetime | None = None,
    ) -> list[tuple[object, CandidateScore]]:
        spot = self.provider.get_underlying(underlying).spot
        chain = self.provider.get_option_chain(underlying, expiry)
        liquid = filter_liquid_candidates(chain, self.config)
        analyzed = []
        for option in liquid:
            analytics = analyze_option(option, spot=spot, hv=hv)
            score = score_candidate(analytics, direction_score=direction_score)
            analyzed.append((analytics, score))
        analyzed.sort(key=lambda item: item[1].total_score, reverse=True)
        return analyzed[: self.config.max_candidates]
