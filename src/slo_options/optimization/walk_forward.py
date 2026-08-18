from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True)
class WalkForwardResult:
    window: WalkForwardWindow
    parameters: dict[str, Any]
    train_score: float
    test_score: float


def make_windows(
    length: int,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> list[WalkForwardWindow]:
    if min(length, train_size, test_size) <= 0:
        raise ValueError("window sizes must be positive")
    step = step or test_size
    if step <= 0:
        raise ValueError("step must be positive")

    windows: list[WalkForwardWindow] = []
    start = 0
    while start + train_size + test_size <= length:
        windows.append(
            WalkForwardWindow(
                train_start=start,
                train_end=start + train_size,
                test_start=start + train_size,
                test_end=start + train_size + test_size,
            )
        )
        start += step
    return windows


def run_walk_forward(
    windows: list[WalkForwardWindow],
    data: list[Any],
    optimizer: Callable[[list[Any]], tuple[dict[str, Any], float]],
    evaluator: Callable[[list[Any], dict[str, Any]], float],
) -> list[WalkForwardResult]:
    results: list[WalkForwardResult] = []
    for window in windows:
        train = data[window.train_start:window.train_end]
        test = data[window.test_start:window.test_end]
        params, train_score = optimizer(train)
        test_score = float(evaluator(test, params))
        results.append(
            WalkForwardResult(window, params, float(train_score), test_score)
        )
    return results
