from dataclasses import dataclass
from typing import Any

from .grid import OptimizationResult


@dataclass(frozen=True)
class RobustnessSummary:
    best_objective: float
    top_quartile_mean: float
    top_quartile_count: int
    objective_range: float
    stability_ratio: float


def summarize(results: list[OptimizationResult]) -> RobustnessSummary:
    if not results:
        raise ValueError("results must not be empty")

    values = [r.objective for r in results]
    ordered = sorted(values, reverse=True)
    q_count = max(1, len(ordered) // 4)
    top = ordered[:q_count]
    best = ordered[0]
    worst = ordered[-1]
    mean_top = sum(top) / len(top)
    ratio = 0.0 if best == 0 else mean_top / best

    return RobustnessSummary(
        best_objective=best,
        top_quartile_mean=mean_top,
        top_quartile_count=q_count,
        objective_range=best - worst,
        stability_ratio=ratio,
    )
