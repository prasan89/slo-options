from slo_options.data.providers.base import MarketDataProvider
from slo_options.data.providers.mock import MockMarketDataProvider
from slo_options.strategy.selector import select_signal


class SLOMCPService:
    """Application facade for MCP/CLI integration.

    The MCP transport can call this service without knowing the provider or strategy internals.
    """

    def __init__(self, provider: MarketDataProvider | None = None) -> None:
        self.provider = provider or MockMarketDataProvider()

    def market_snapshot(self, symbol: str):
        return self.provider.get_underlying(symbol)

    def option_chain(self, symbol: str):
        return self.provider.get_option_chain(symbol)

    def signal(self, underlying: str, direction_score: float, hv: float | None = None):
        spot = self.provider.get_underlying(underlying).spot
        chain = self.provider.get_option_chain(underlying)
        return select_signal(
            chain=chain,
            spot=spot,
            direction_score=direction_score,
            hv=hv,
        )
