from slo_options.data.providers.mock import MockMarketDataProvider
from slo_options.strategy.candidate_engine import CandidateEngine


def main() -> None:
    provider = MockMarketDataProvider()
    engine = CandidateEngine(provider)
    for symbol in ("NIFTY", "BANKNIFTY"):
        print(f"\n=== {symbol} ===")
        for analytics, score in engine.scan(symbol, direction_score=70.0, hv=0.15):
            print(
                f"{analytics.symbol:<28} {analytics.option_type} "
                f"strike={analytics.strike:.0f} dte={analytics.dte:<3} "
                f"score={score.total_score:.1f}"
            )


if __name__ == "__main__":
    main()
