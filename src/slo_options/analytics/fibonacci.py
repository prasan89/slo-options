"""Fibonacci retracement/extension levels for trade-plan context."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FibonacciLevels:
    high: float
    low: float
    retracement_236: float
    retracement_382: float
    retracement_500: float
    retracement_618: float
    retracement_786: float
    extension_1272: float
    extension_1618: float

def levels(low: float, high: float) -> FibonacciLevels:
    if low <= 0 or high <= low:
        raise ValueError("high must be greater than positive low")
    move = high - low
    return FibonacciLevels(high, low, high-move*.236, high-move*.382, high-move*.500, high-move*.618, high-move*.786, high+move*.272, high+move*.618)

def nearest_level(price: float, fib: FibonacciLevels) -> tuple[str, float]:
    values = {"23.6%": fib.retracement_236, "38.2%": fib.retracement_382, "50.0%": fib.retracement_500, "61.8%": fib.retracement_618, "78.6%": fib.retracement_786}
    return min(values.items(), key=lambda item: abs(price-item[1]))
