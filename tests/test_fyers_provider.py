from datetime import datetime

import pytest


class FakeFyersModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def quotes(self, data):
        return {"s": "ok", "d": [{"v": {"lp": 24000.0}}]}

    def optionchain(self, data):
        return {
            "s": "ok",
            "data": {
                "optionsChain": [
                    {
                        "symbol": "NSE:NIFTY50-INDEX-24000-CE",
                        "strike_price": 24000,
                        "option_type": "CE",
                        "expiry": 1788000000,
                        "bid": 100,
                        "ask": 102,
                        "ltp": 101,
                        "volume": 1000,
                        "oi": 2000,
                        "iv": 12.5,
                    }
                ]
            },
        }

    def history(self, data):
        return {"s": "ok", "candles": [[1787000000, 23900, 24100, 23800, 24000, 100000]]}


def test_fyers_provider_uses_api_v3(monkeypatch):
    import slo_options.data.providers.fyers as fyers

    monkeypatch.setattr(fyers.fyersModel, "FyersModel", FakeFyersModel)
    monkeypatch.setenv("FYERS_APP_ID", "APP-123")
    monkeypatch.setenv("FYERS_ACCESS_TOKEN", "TOKEN-123")
    monkeypatch.setenv(
        "SLO_FYERS_SYMBOLS",
        '{"NIFTY":"NSE:NIFTY50-INDEX","BANKNIFTY":"NSE:NIFTYBANK-INDEX"}',
    )

    provider = fyers.FyersMarketDataProvider()

    underlying = provider.get_underlying("NIFTY")
    assert underlying.spot == 24000.0

    chain = provider.get_option_chain("NIFTY", datetime(2026, 9, 1))
    assert len(chain) == 1
    assert chain[0].symbol == "NSE:NIFTY50-INDEX-24000-CE"
    assert chain[0].option_type.value.lower() in {"call", "ce"}
    assert chain[0].bid == 100
    assert chain[0].ask == 102

    closes = provider.get_historical_closes("NIFTY", days=1)
    assert len(closes) == 1
    assert closes[0][1] == 24000.0


def test_fyers_provider_requires_credentials(monkeypatch):
    monkeypatch.delenv("FYERS_APP_ID", raising=False)
    monkeypatch.delenv("FYERS_ACCESS_TOKEN", raising=False)

    from slo_options.data.providers.fyers import FyersMarketDataProvider

    with pytest.raises(ValueError, match="FYERS_APP_ID"):
        FyersMarketDataProvider()
