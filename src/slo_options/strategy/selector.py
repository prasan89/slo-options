from dataclasses import dataclass
from enum import Enum

from slo_options.analytics.candidate import OptionAnalytics
from slo_options.strategy.direction import Direction
from slo_options.strategy.scoring import CandidateScore


class Signal(str, Enum):
    BUY_CALL = "BUY_CALL"
    BUY_PUT = "BUY_PUT"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True)
class TradeSignal:
    signal: Signal
    option_symbol: str | None
    score: float
    entry_premium: float | None
    stop_premium: float | None
    target_premium: float | None
    reason: str


def select_trade(
    direction: Direction,
    analytics: OptionAnalytics,
    candidate_score: CandidateScore,
    min_score: float = 65.0,
    stop_loss_pct: float = 0.35,
    profit_target_pct: float = 0.50,
) -> TradeSignal:
    """Map a ranked option candidate to a long-only V1 signal.

    Calls are eligible only under a bullish direction; puts only under a
    bearish direction. No short-option signal is produced.
    """
    if analytics.premium <= 0:
        return TradeSignal(Signal.NO_TRADE, None, 0.0, None, None, None, "Invalid option premium.")

    if candidate_score.total_score < min_score:
        return TradeSignal(
            Signal.NO_TRADE,
            analytics.symbol,
            candidate_score.total_score,
            analytics.premium,
            None,
            None,
            "Candidate score is below the V1 entry threshold.",
        )

    if direction == Direction.BULLISH and analytics.option_type == "CE":
        signal = Signal.BUY_CALL
    elif direction == Direction.BEARISH and analytics.option_type == "PE":
        signal = Signal.BUY_PUT
    else:
        return TradeSignal(
            Signal.NO_TRADE,
            analytics.symbol,
            candidate_score.total_score,
            analytics.premium,
            None,
            None,
            "Option direction does not agree with the underlying direction signal.",
        )

    stop = analytics.premium * (1.0 - stop_loss_pct)
    target = analytics.premium * (1.0 + profit_target_pct)

    return TradeSignal(
        signal=signal,
        option_symbol=analytics.symbol,
        score=candidate_score.total_score,
        entry_premium=analytics.premium,
        stop_premium=stop,
        target_premium=target,
        reason="Direction and candidate score agree; long-only signal generated.",
    )
