"""Lightweight fundamental/news risk filters for short-term option research."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class FundamentalSnapshot:
    pe: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    debt_to_equity: float | None = None
    peg: float | None = None
    free_cash_flow: float | None = None
    sector_pe: float | None = None
    earnings_days: int | None = None

    @property
    def relative_pe(self) -> float | None:
        if self.pe is None or self.sector_pe in (None, 0): return None
        return self.pe / self.sector_pe

    def score(self) -> float:
        parts: list[float] = []
        if self.relative_pe is not None: parts.append(70.0 if self.relative_pe <= 1 else 40.0 if self.relative_pe <= 1.25 else 20.0)
        if self.peg is not None: parts.append(70.0 if self.peg < 1 else 45.0 if self.peg <= 1.5 else 25.0)
        if self.debt_to_equity is not None: parts.append(70.0 if self.debt_to_equity < 1 else 45.0 if self.debt_to_equity <= 2 else 25.0)
        if self.free_cash_flow is not None: parts.append(65.0 if self.free_cash_flow > 0 else 30.0)
        return sum(parts) / len(parts) if parts else 50.0

def event_risk(earnings_days: int | None, high_impact_event: bool = False) -> Literal["NORMAL", "MEDIUM", "HIGH"]:
    if high_impact_event or (earnings_days is not None and earnings_days <= 1): return "HIGH"
    if earnings_days is not None and earnings_days <= 5: return "MEDIUM"
    return "NORMAL"

def risk_multiplier(risk: str) -> float:
    return {"NORMAL": 1.0, "MEDIUM": 0.75, "HIGH": 0.50}.get(risk.upper(), 0.5)
