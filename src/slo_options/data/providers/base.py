from abc import ABC, abstractmethod
from datetime import datetime
from slo_options.models.market import OptionQuote, Underlying

class MarketDataProvider(ABC):
    @abstractmethod
    def get_underlying(self, symbol: str) -> Underlying:
        raise NotImplementedError

    @abstractmethod
    def get_option_chain(self, underlying: str, expiry: datetime | None = None) -> list[OptionQuote]:
        raise NotImplementedError
