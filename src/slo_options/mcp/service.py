from slo_options.data.providers.base import MarketDataProvider
from slo_options.data.providers.factory import build_provider
from slo_options.strategy.candidate_engine import CandidateEngine
from slo_options.strategy.selector import select_trade


class SLOMCPService:
    """Application facade for MCP/CLI integration."""

    def __init__(self, provider: MarketDataProvider | None = None) -> None:
        self.provider = provider or build_provider()
        self.engine = CandidateEngine(self.provider)

    def market_snapshot(self, symbol: str):
        return self.provider.get_underlying(symbol)

    def option_chain(self, symbol: str):
        return self.provider.get_option_chain(symbol)

    def scan(self, symbol: str, direction_score: float, hv: float | None = None):
        return self.engine.scan(symbol, direction_score=direction_score, hv=hv)

    def signal(self, symbol: str, direction, direction_score: float, hv: float | None = None):
        candidates = self.engine.scan(symbol, direction_score=direction_score, hv=hv)
        for analytics, score in candidates:
            signal = select_trade(direction, analytics, score)
            if signal.signal.value != "NO_TRADE":
                return signal
        return None
