from dataclasses import dataclass
from datetime import datetime

from slo_options.analytics.black_scholes import delta, gamma, theta_per_day, vega_per_1pct
from slo_options.models.market import OptionQuote


@dataclass(frozen=True)
class OptionAnalytics:
    symbol: str
    underlying: str
    option_type: str
    strike: float
    expiry: datetime
    premium: float
    spread_pct: float
    dte: int
    delta: float
    gamma: float
    theta_per_day: float
    vega_per_1pct: float
    iv: float | None
    hv: float | None
    iv_hv_ratio: float | None
    breakeven: float


def analyze_option(option: OptionQuote, spot: float, hv: float | None = None, risk_free_rate: float = 0.0):
    premium = option.mid
    dte = max(1, (option.expiry - datetime.now()).days)
    years = dte / 365
    iv = option.implied_volatility or 0.20
    typ = option.option_type.value
    d = delta(spot, option.strike, years, iv, risk_free_rate, typ)
    g = gamma(spot, option.strike, years, iv, risk_free_rate)
    th = theta_per_day(spot, option.strike, years, iv, risk_free_rate, typ)
    vg = vega_per_1pct(spot, option.strike, years, iv, risk_free_rate)
    ratio = None if hv is None or hv <= 0 else iv / hv
    breakeven = option.strike + premium if typ == "CE" else option.strike - premium
    return OptionAnalytics(
        symbol=option.symbol, underlying=option.underlying, option_type=typ,
        strike=option.strike, expiry=option.expiry, premium=premium,
        spread_pct=option.spread_pct, dte=dte, delta=d, gamma=g,
        theta_per_day=th, vega_per_1pct=vg, iv=iv, hv=hv,
        iv_hv_ratio=ratio, breakeven=breakeven
    )
