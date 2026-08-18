from math import exp, log, sqrt
from scipy.optimize import brentq
from scipy.stats import norm


def _validate_inputs(spot: float, strike: float, time_years: float, volatility: float) -> None:
    if spot <= 0 or strike <= 0 or time_years <= 0 or volatility <= 0:
        raise ValueError("spot, strike, time and volatility must be positive")


def price(spot, strike, time_years, volatility, rate=0.0, option_type="CE"):
    _validate_inputs(spot, strike, time_years, volatility)
    srt = volatility * sqrt(time_years)
    d1 = (log(spot / strike) + (rate + 0.5 * volatility**2) * time_years) / srt
    d2 = d1 - srt
    if option_type == "CE":
        return spot * norm.cdf(d1) - strike * exp(-rate * time_years) * norm.cdf(d2)
    if option_type == "PE":
        return strike * exp(-rate * time_years) * norm.cdf(-d2) - spot * norm.cdf(-d1)
    raise ValueError("option_type must be CE or PE")


def delta(spot, strike, time_years, volatility, rate=0.0, option_type="CE"):
    _validate_inputs(spot, strike, time_years, volatility)
    d1 = (log(spot / strike) + (rate + 0.5 * volatility**2) * time_years) / (volatility * sqrt(time_years))
    if option_type == "CE":
        return float(norm.cdf(d1))
    if option_type == "PE":
        return float(norm.cdf(d1) - 1.0)
    raise ValueError("option_type must be CE or PE")


def gamma(spot, strike, time_years, volatility, rate=0.0):
    _validate_inputs(spot, strike, time_years, volatility)
    d1 = (log(spot / strike) + (rate + 0.5 * volatility**2) * time_years) / (volatility * sqrt(time_years))
    return float(norm.pdf(d1) / (spot * volatility * sqrt(time_years)))


def theta_per_day(spot, strike, time_years, volatility, rate=0.0, option_type="CE"):
    _validate_inputs(spot, strike, time_years, volatility)
    srt = volatility * sqrt(time_years)
    d1 = (log(spot / strike) + (rate + 0.5 * volatility**2) * time_years) / srt
    d2 = d1 - srt
    first = -(spot * norm.pdf(d1) * volatility) / (2 * sqrt(time_years))
    if option_type == "CE":
        annual = first - rate * strike * exp(-rate * time_years) * norm.cdf(d2)
    elif option_type == "PE":
        annual = first + rate * strike * exp(-rate * time_years) * norm.cdf(-d2)
    else:
        raise ValueError("option_type must be CE or PE")
    return float(annual / 365.0)


def vega_per_1pct(spot, strike, time_years, volatility, rate=0.0):
    _validate_inputs(spot, strike, time_years, volatility)
    d1 = (log(spot / strike) + (rate + 0.5 * volatility**2) * time_years) / (volatility * sqrt(time_years))
    return float(spot * norm.pdf(d1) * sqrt(time_years) * 0.01)


def implied_volatility(market_price, spot, strike, time_years, rate=0.0, option_type="CE"):
    if market_price <= 0:
        raise ValueError("market_price must be positive")
    f = lambda vol: price(spot, strike, time_years, vol, rate, option_type) - market_price
    if f(1e-6) * f(5.0) > 0:
        raise ValueError("market price outside solver range")
    return float(brentq(f, 1e-6, 5.0, maxiter=200))
