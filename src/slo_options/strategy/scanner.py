from datetime import datetime

from slo_options.models.market import OptionQuote
from slo_options.strategy.config import StrategyConfig


def filter_liquid_candidates(chain: list[OptionQuote], config: StrategyConfig):
    out = []
    now = datetime.now()
    for option in chain:
        if option.bid <= 0 or option.ask <= option.bid:
            continue
        if option.spread_pct > config.max_spread_pct:
            continue
        if option.volume < config.min_volume or option.open_interest < config.min_open_interest:
            continue
        dte = (option.expiry - now).days
        if not (config.min_dte <= dte <= config.max_dte):
            continue
        out.append(option)
    return out
