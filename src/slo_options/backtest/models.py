from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    symbol: str
    close: float


@dataclass(frozen=True)
class OptionBar:
    timestamp: datetime
    symbol: str
    underlying: str
    close: float
    bid: float
    ask: float


@dataclass(frozen=True)
class TradeSignal:
    timestamp: datetime
    option_symbol: str
    action: str
    quantity: int
    entry_price: float
    stop_price: float
    target_price: float
    max_holding_days: int


@dataclass(frozen=True)
class CompletedTrade:
    option_symbol: str
    entry_time: datetime
    exit_time: datetime
    quantity: int
    entry_price: float
    exit_price: float
    gross_pnl: float
    costs: float
    net_pnl: float
    exit_reason: str


@dataclass(frozen=True)
class BacktestResult:
    starting_capital: float
    ending_capital: float
    total_pnl: float
    return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    trades: tuple[CompletedTrade, ...]
