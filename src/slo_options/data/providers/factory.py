import os

from slo_options.data.providers.base import MarketDataProvider
from slo_options.data.providers.groww import GrowwMarketDataProvider
from slo_options.data.providers.mock import MockMarketDataProvider
from slo_options.data.providers.upstox import UpstoxMarketDataProvider


def build_provider() -> MarketDataProvider:
    provider = os.getenv("DATA_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockMarketDataProvider()
    if provider == "upstox":
        return UpstoxMarketDataProvider()
    if provider == "groww":
        return GrowwMarketDataProvider()
    raise ValueError(f"Unsupported DATA_PROVIDER={provider!r}")
