from datetime import datetime, timedelta
from slo_options.data.providers.base import MarketDataProvider
from slo_options.models.market import OptionQuote, OptionType, Underlying

class MockMarketDataProvider(MarketDataProvider):
    def get_underlying(self, symbol: str) -> Underlying:
        prices = {"NIFTY": 25000.0, "BANKNIFTY": 55000.0, "RELIANCE": 1400.0}
        return Underlying(symbol=symbol, spot=prices.get(symbol, 1000.0), timestamp=datetime.now())

    def get_option_chain(self, underlying: str, expiry: datetime | None = None) -> list[OptionQuote]:
        spot = self.get_underlying(underlying).spot
        expiry = expiry or (datetime.now() + timedelta(days=14))
        strikes = [round(spot * x / 100) for x in (98, 99, 100, 101, 102)]
        out = []
        for strike in strikes:
            for typ in (OptionType.CALL, OptionType.PUT):
                intrinsic = max(spot - strike, 0) if typ == OptionType.CALL else max(strike - spot, 0)
                premium = intrinsic + spot * 0.005
                out.append(OptionQuote(
                    underlying=underlying,
                    symbol=f"{underlying}-{strike}-{typ.value}",
                    strike=float(strike), option_type=typ, expiry=expiry,
                    bid=max(0.1, premium - 1), ask=premium + 1, last=premium,
                    volume=10000, open_interest=50000, implied_volatility=0.18,
                ))
        return out
