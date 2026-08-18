from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class OptionType(str, Enum):
    CALL = "CE"
    PUT = "PE"

class Underlying(BaseModel):
    symbol: str
    spot: float = Field(gt=0)
    timestamp: datetime

class OptionQuote(BaseModel):
    underlying: str
    symbol: str
    strike: float = Field(gt=0)
    option_type: OptionType
    expiry: datetime
    bid: float = Field(ge=0)
    ask: float = Field(ge=0)
    last: float | None = Field(default=None, ge=0)
    volume: int = Field(default=0, ge=0)
    open_interest: int = Field(default=0, ge=0)
    implied_volatility: float | None = Field(default=None, ge=0)

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread_pct(self) -> float:
        if self.mid <= 0:
            return float("inf")
        return (self.ask - self.bid) / self.mid
