from __future__ import annotations

from copy import deepcopy
from itertools import islice, product

from renko_research_engine.backtest.engine import run_backtest
from renko_research_engine.renko.builder import build_synthetic_renko_features
from renko_research_engine.strategy.signals import generate_signals



def optimize(bars: list[dict], base_strategy, grid: dict, max_combinations: int) -> list[dict]:
    keys = list(grid.keys())
    combos = list(islice(product(*(grid[key] for key in keys)), max_combinations))
    results = []
    for combo in combos:
        params = dict(zip(keys, combo))
        strategy = _apply(base_strategy, params)
        enriched = _prepare_dataset(bars, strategy)
        signals = generate_signals(enriched, strategy)
        backtest = run_backtest(signals.bars, strategy)
        summary = backtest.summary
        score = max(summary["profit_factor"], 0.0) * max(summary["win_rate"], 0.0) * (1 + max(summary["sharpe"], 0.0))
        results.append({**params, **summary, "score": score})
    return sorted(results, key=lambda row: (row["score"], row["profit_factor"], row["win_rate"]), reverse=True)



def _apply(strategy, params: dict):
    copy = deepcopy(strategy)
    for key, value in params.items():
        if key == "trailing_enabled":
            copy.trailing.enabled = value
        elif key == "cooldown_bars":
            copy.filters.cooldown_bars = value
        elif hasattr(copy, key):
            setattr(copy, key, value)
    return copy



def _prepare_dataset(bars: list[dict], strategy) -> list[dict]:
    data = [dict(row) for row in bars]
    trend = build_synthetic_renko_features(data, strategy.trend_renko_size, "trend")
    entry = build_synthetic_renko_features(data, strategy.entry_renko_size, "entry")
    out = []
    for index, row in enumerate(data):
        merged = dict(row)
        merged.update(trend[index])
        merged.update(entry[index])
        out.append(merged)
    return out
