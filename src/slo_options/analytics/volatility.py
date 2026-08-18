import numpy as np
import pandas as pd


def historical_volatility(prices: pd.Series, window: int = 20, annualization: int = 252) -> float:
    if len(prices) < window + 1:
        raise ValueError("not enough prices")
    returns = np.log(prices / prices.shift(1)).dropna()
    return float(returns.tail(window).std(ddof=1) * np.sqrt(annualization))


def iv_hv_ratio(iv: float, hv: float) -> float:
    if hv <= 0:
        raise ValueError("hv must be positive")
    return iv / hv
