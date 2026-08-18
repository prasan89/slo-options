from pydantic import BaseModel, Field


class StrategyConfig(BaseModel):
    min_dte: int = Field(7, ge=1)
    max_dte: int = Field(30, ge=1)
    max_spread_pct: float = Field(0.05, gt=0)
    min_volume: int = Field(1000, ge=0)
    min_open_interest: int = Field(5000, ge=0)
    max_candidates: int = Field(10, ge=1)
    stop_loss_pct: float = Field(0.35, gt=0, lt=1)
    profit_target_pct: float = Field(0.50, gt=0)
