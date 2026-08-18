from slo_options.optimization.grid import grid_search
from slo_options.optimization.robustness import summarize
from slo_options.optimization.walk_forward import make_windows


def test_grid_search_returns_best_first():
    results = grid_search(
        {"x": [1, 2], "y": [10, 20]},
        lambda p: p["x"] * p["y"],
    )
    assert results[0].parameters == {"x": 2, "y": 20}
    assert results[0].objective == 40


def test_robustness_summary():
    results = grid_search({"x": [1, 2, 3, 4]}, lambda p: float(p["x"]))
    summary = summarize(results)
    assert summary.best_objective == 4
    assert summary.top_quartile_count == 1


def test_walk_forward_windows_are_non_overlapping_by_default():
    windows = make_windows(100, train_size=40, test_size=20)
    assert windows[0].train_start == 0
    assert windows[0].train_end == 40
    assert windows[0].test_start == 40
    assert windows[0].test_end == 60
    assert windows[1].train_start == 20
