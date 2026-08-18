from dataclasses import dataclass
from itertools import product
from typing import Callable, Any


@dataclass(frozen=True)
class OptimizationResult:
    parameters: dict[str, Any]
    objective: float


def grid_search(
    parameter_grid: dict[str, list[Any]],
    objective: Callable[[dict[str, Any]], float],
) -> list[OptimizationResult]:
    if not parameter_grid:
        raise ValueError("parameter_grid must not be empty")

    names = list(parameter_grid)
    results: list[OptimizationResult] = []
    for values in product(*(parameter_grid[name] for name in names)):
        params = dict(zip(names, values))
        results.append(OptimizationResult(parameters=params, objective=float(objective(params))))

    return sorted(results, key=lambda r: r.objective, reverse=True)


def robust_region(results: list[OptimizationResult], percentile: float = 0.8) -> list[OptimizationResult]:
    if not results:
        return []
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be in (0, 1]")
    cutoff_index = max(1, int(len(results) * (1 - percentile)))
    ordered = sorted(results, key=lambda r: r.objective, reverse=True)
    return ordered[:cutoff_index]
