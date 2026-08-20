"""Composable option strategies from the Options Combinations chapter.

This module is a research/paper-trading representation of the chapter's
building blocks. It does not place orders. Premiums are per share/unit and
contract size is applied only by callers when sizing a position.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import inf


class LegSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Instrument(str, Enum):
    CALL = "CALL"
    PUT = "PUT"
    STOCK = "STOCK"


@dataclass(frozen=True)
class OptionLeg:
    side: LegSide
    instrument: Instrument
    strike: float | None
    expiry: datetime | None
    premium: float
    quantity: int = 1

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.premium < 0:
            raise ValueError("premium must be non-negative")
        if self.instrument == Instrument.STOCK:
            if self.strike is not None or self.expiry is not None:
                raise ValueError("stock legs cannot have strike or expiry")
        elif self.strike is None or self.expiry is None:
            raise ValueError("option legs require strike and expiry")

    @property
    def cashflow(self) -> float:
        """Positive = cash received, negative = cash paid."""
        amount = self.premium * self.quantity
        return amount if self.side == LegSide.SELL else -amount


@dataclass(frozen=True)
class Combination:
    name: str
    legs: tuple[OptionLeg, ...]
    description: str

    @property
    def entry_credit(self) -> float:
        return sum(leg.cashflow for leg in self.legs)

    @property
    def entry_debit(self) -> float:
        return max(0.0, -self.entry_credit)

    @property
    def entry_credit_received(self) -> float:
        return max(0.0, self.entry_credit)

    def payoff_at_expiry(self, spot: float, expiry: datetime) -> float:
        """Return per-unit expiry P/L including initial premium cashflows.

        This is intentionally restricted to positions whose option legs share
        the requested expiry. Calendar/diagonal structures need multi-expiry
        valuation and therefore raise ValueError here.
        """
        if spot < 0:
            raise ValueError("spot must be non-negative")
        for leg in self.legs:
            if leg.instrument != Instrument.STOCK and leg.expiry != expiry:
                raise ValueError("multi-expiry combinations need time-value valuation")

        pnl = self.entry_credit
        for leg in self.legs:
            if leg.instrument == Instrument.STOCK:
                intrinsic = spot
            elif leg.instrument == Instrument.CALL:
                intrinsic = max(spot - leg.strike, 0.0)
            else:
                intrinsic = max(leg.strike - spot, 0.0)
            pnl += (intrinsic * leg.quantity if leg.side == LegSide.BUY else -intrinsic * leg.quantity)
        return pnl

    def payoff_range(self, expiry: datetime, spots: list[float]) -> tuple[float, float]:
        values = [self.payoff_at_expiry(s, expiry) for s in spots]
        if not values:
            raise ValueError("spots must not be empty")
        return min(values), max(values)


def _opt(side: LegSide, typ: Instrument, strike: float, expiry: datetime, premium: float, quantity: int = 1) -> OptionLeg:
    return OptionLeg(side, typ, strike, expiry, premium, quantity)


def covered_call(stock_price: float, call_strike: float, call_premium: float, expiry: datetime) -> Combination:
    return Combination("COVERED_CALL", (OptionLeg(LegSide.BUY, Instrument.STOCK, None, None, stock_price), _opt(LegSide.SELL, Instrument.CALL, call_strike, expiry, call_premium)), "Buy stock and sell an OTM call.")


def long_call(strike: float, premium: float, expiry: datetime) -> Combination:
    return Combination("LONG_CALL", (_opt(LegSide.BUY, Instrument.CALL, strike, expiry, premium),), "Buy a call to capture upside movement.")


def long_put(strike: float, premium: float, expiry: datetime) -> Combination:
    return Combination("LONG_PUT", (_opt(LegSide.BUY, Instrument.PUT, strike, expiry, premium),), "Buy a put to capture downside movement.")


def short_call(strike: float, premium: float, expiry: datetime) -> Combination:
    return Combination("SHORT_CALL", (_opt(LegSide.SELL, Instrument.CALL, strike, expiry, premium),), "Sell a call for premium; risk is not defined without a hedge.")


def short_put(strike: float, premium: float, expiry: datetime) -> Combination:
    return Combination("SHORT_PUT", (_opt(LegSide.SELL, Instrument.PUT, strike, expiry, premium),), "Sell a put for premium or as a stock-entry strategy.")


def long_call_spread(long_strike: float, short_strike: float, long_premium: float, short_premium: float, expiry: datetime) -> Combination:
    if short_strike <= long_strike: raise ValueError("short call strike must be higher")
    return Combination("LONG_CALL_SPREAD", (_opt(LegSide.BUY, Instrument.CALL, long_strike, expiry, long_premium), _opt(LegSide.SELL, Instrument.CALL, short_strike, expiry, short_premium)), "Buy lower-strike call and sell higher-strike call with the same expiry.")


def long_put_spread(long_strike: float, short_strike: float, long_premium: float, short_premium: float, expiry: datetime) -> Combination:
    if short_strike >= long_strike: raise ValueError("short put strike must be lower")
    return Combination("LONG_PUT_SPREAD", (_opt(LegSide.BUY, Instrument.PUT, long_strike, expiry, long_premium), _opt(LegSide.SELL, Instrument.PUT, short_strike, expiry, short_premium)), "Buy higher-strike put and sell lower-strike put with the same expiry.")


def short_call_spread(short_strike: float, long_strike: float, short_premium: float, long_premium: float, expiry: datetime) -> Combination:
    return long_call_spread(short_strike, long_strike, short_premium, long_premium, expiry)._replace("SHORT_CALL_SPREAD")


def short_put_spread(short_strike: float, long_strike: float, short_premium: float, long_premium: float, expiry: datetime) -> Combination:
    return long_put_spread(long_strike, short_strike, long_premium, short_premium, expiry)._replace("SHORT_PUT_SPREAD")


def _replace_name(c: Combination, name: str) -> Combination:
    return Combination(name, tuple(OptionLeg(LegSide.SELL if l.side == LegSide.BUY else LegSide.BUY, l.instrument, l.strike, l.expiry, l.premium, l.quantity) for l in c.legs), c.description)

Combination._replace = _replace_name  # type: ignore[attr-defined]


def long_ratio_call_spread(long_strike: float, short_strike: float, long_premium: float, short_premium: float, expiry: datetime, ratio: int = 2) -> Combination:
    if short_strike <= long_strike or ratio < 2: raise ValueError("ratio requires higher short strike and ratio >= 2")
    return Combination("LONG_RATIO_CALL_SPREAD", (_opt(LegSide.BUY, Instrument.CALL, long_strike, expiry, long_premium), _opt(LegSide.SELL, Instrument.CALL, short_strike, expiry, short_premium, ratio)), "Buy one call and sell two or more higher-strike calls.")


def long_ratio_put_spread(long_strike: float, short_strike: float, long_premium: float, short_premium: float, expiry: datetime, ratio: int = 2) -> Combination:
    if short_strike >= long_strike or ratio < 2: raise ValueError("ratio requires lower short strike and ratio >= 2")
    return Combination("LONG_RATIO_PUT_SPREAD", (_opt(LegSide.BUY, Instrument.PUT, long_strike, expiry, long_premium), _opt(LegSide.SELL, Instrument.PUT, short_strike, expiry, short_premium, ratio)), "Buy one put and sell two or more lower-strike puts.")


def calendar(instrument: Instrument, strike: float, near_premium: float, far_premium: float, near_expiry: datetime, far_expiry: datetime, long: bool = True) -> Combination:
    if instrument == Instrument.STOCK or far_expiry <= near_expiry: raise ValueError("calendar requires an option and later far expiry")
    if long:
        legs = (_opt(LegSide.SELL, instrument, strike, near_expiry, near_premium), _opt(LegSide.BUY, instrument, strike, far_expiry, far_premium))
        name = "LONG_CALENDAR"
    else:
        legs = (_opt(LegSide.BUY, instrument, strike, near_expiry, near_premium), _opt(LegSide.SELL, instrument, strike, far_expiry, far_premium))
        name = "SHORT_CALENDAR"
    return Combination(name, legs, "Same strike with different expiries.")


def diagonal(instrument: Instrument, near_strike: float, far_strike: float, near_premium: float, far_premium: float, near_expiry: datetime, far_expiry: datetime, long: bool = True) -> Combination:
    if instrument == Instrument.STOCK or far_expiry <= near_expiry: raise ValueError("diagonal requires an option and later far expiry")
    if long:
        legs = (_opt(LegSide.SELL, instrument, near_strike, near_expiry, near_premium), _opt(LegSide.BUY, instrument, far_strike, far_expiry, far_premium))
        name = "LONG_DIAGONAL"
    else:
        legs = (_opt(LegSide.BUY, instrument, near_strike, near_expiry, near_premium), _opt(LegSide.SELL, instrument, far_strike, far_expiry, far_premium))
        name = "SHORT_DIAGONAL"
    return Combination(name, legs, "Different strikes and expiries.")


def butterfly(instrument: Instrument, lower: float, middle: float, upper: float, lower_premium: float, middle_premium: float, upper_premium: float, expiry: datetime, long: bool = True) -> Combination:
    if not lower < middle < upper or middle - lower != upper - middle: raise ValueError("butterfly strikes must be equidistant")
    if long:
        legs = (_opt(LegSide.BUY, instrument, lower, expiry, lower_premium), _opt(LegSide.SELL, instrument, middle, expiry, middle_premium, 2), _opt(LegSide.BUY, instrument, upper, expiry, upper_premium))
        name = "LONG_BUTTERFLY"
    else:
        legs = (_opt(LegSide.SELL, instrument, lower, expiry, lower_premium), _opt(LegSide.BUY, instrument, middle, expiry, middle_premium, 2), _opt(LegSide.SELL, instrument, upper, expiry, upper_premium))
        name = "SHORT_BUTTERFLY"
    return Combination(name, legs, "Four option legs across three equidistant strikes.")


def straddle(strike: float, call_premium: float, put_premium: float, expiry: datetime, long: bool = True) -> Combination:
    side = LegSide.BUY if long else LegSide.SELL
    return Combination("LONG_STRADDLE" if long else "SHORT_STRADDLE", (_opt(side, Instrument.CALL, strike, expiry, call_premium), _opt(side, Instrument.PUT, strike, expiry, put_premium)), "Call and put at the same strike and expiry.")


def strangle(put_strike: float, call_strike: float, put_premium: float, call_premium: float, expiry: datetime, long: bool = True) -> Combination:
    if put_strike >= call_strike: raise ValueError("put strike must be below call strike")
    side = LegSide.BUY if long else LegSide.SELL
    return Combination("LONG_STRANGLE" if long else "SHORT_STRANGLE", (_opt(side, Instrument.PUT, put_strike, expiry, put_premium), _opt(side, Instrument.CALL, call_strike, expiry, call_premium)), "Put and call at different strikes with the same expiry.")


def iron_condor(short_put_strike: float, long_put_strike: float, short_call_strike: float, long_call_strike: float, short_put_premium: float, long_put_premium: float, short_call_premium: float, long_call_premium: float, expiry: datetime, long: bool = False) -> Combination:
    if not long_put_strike < short_put_strike < short_call_strike < long_call_strike: raise ValueError("iron condor strikes must be ordered LP < SP < SC < LC")
    if long:
        legs = (_opt(LegSide.BUY, Instrument.PUT, long_put_strike, expiry, long_put_premium), _opt(LegSide.SELL, Instrument.PUT, short_put_strike, expiry, short_put_premium), _opt(LegSide.SELL, Instrument.CALL, short_call_strike, expiry, short_call_premium), _opt(LegSide.BUY, Instrument.CALL, long_call_strike, expiry, long_call_premium))
        name = "LONG_IRON_CONDOR"
    else:
        legs = (_opt(LegSide.SELL, Instrument.PUT, short_put_strike, expiry, short_put_premium), _opt(LegSide.BUY, Instrument.PUT, long_put_strike, expiry, long_put_premium), _opt(LegSide.SELL, Instrument.CALL, short_call_strike, expiry, short_call_premium), _opt(LegSide.BUY, Instrument.CALL, long_call_strike, expiry, long_call_premium))
        name = "SHORT_IRON_CONDOR"
    return Combination(name, legs, "Defined-risk four-leg range strategy.")


def risk_reversal(call_strike: float, put_strike: float, call_premium: float, put_premium: float, expiry: datetime, bullish: bool = True) -> Combination:
    if bullish:
        legs = (_opt(LegSide.BUY, Instrument.CALL, call_strike, expiry, call_premium), _opt(LegSide.SELL, Instrument.PUT, put_strike, expiry, put_premium))
        name = "BULLISH_RISK_REVERSAL"
    else:
        legs = (_opt(LegSide.BUY, Instrument.PUT, put_strike, expiry, put_premium), _opt(LegSide.SELL, Instrument.CALL, call_strike, expiry, call_premium))
        name = "BEARISH_RISK_REVERSAL"
    return Combination(name, legs, "Long one option and short the opposite option at the same expiry.")
