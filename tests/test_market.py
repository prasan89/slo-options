from slo_options.data.providers.mock import MockMarketDataProvider


def test_mock_provider_returns_underlying():
    provider = MockMarketDataProvider()
    underlying = provider.get_underlying("NIFTY")
    assert underlying.symbol == "NIFTY"
    assert underlying.spot > 0


def test_mock_provider_returns_call_and_puts():
    provider = MockMarketDataProvider()
    chain = provider.get_option_chain("NIFTY")
    types = {option.option_type.value for option in chain}
    assert "CE" in types
    assert "PE" in types
