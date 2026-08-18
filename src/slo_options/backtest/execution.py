from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionConfig:
    commission_per_unit: float = 0.0
    slippage_pct: float = 0.0025


class ExecutionModel:
    def __init__(self, config: ExecutionConfig | None = None):
        self.config = config or ExecutionConfig()

    def buy_price(self, ask: float) -> float:
        return ask * (1.0 + self.config.slippage_pct)

    def sell_price(self, bid: float) -> float:
        return max(0.0, bid * (1.0 - self.config.slippage_pct))

    def cost(self, quantity: int) -> float:
        return abs(quantity) * self.config.commission_per_unit
