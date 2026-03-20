from __future__ import annotations

import argparse
import json
from copy import deepcopy

from renko_research_engine.backtest.engine import run_backtest
from renko_research_engine.config.loader import load_config
from renko_research_engine.data.loader import load_market_data
from renko_research_engine.optimize.grid import optimize
from renko_research_engine.renko.builder import build_synthetic_renko_features
from renko_research_engine.reporting.blueprint import build_tradingview_blueprint
from renko_research_engine.reporting.writer import write_outputs
from renko_research_engine.strategy.signals import generate_signals



def prepare_dataset(bars: list[dict], strategy) -> list[dict]:
    data = [dict(row) for row in bars]
    trend = build_synthetic_renko_features(data, strategy.trend_renko_size, "trend")
    entry = build_synthetic_renko_features(data, strategy.entry_renko_size, "entry")
    merged = []
    for index, row in enumerate(data):
        combined = dict(row)
        combined.update(trend[index])
        combined.update(entry[index])
        merged.append(combined)
    return merged



def split_dataset(bars: list[dict], fraction: float):
    cut = max(1, int(len(bars) * fraction))
    return bars[:cut], bars[cut:]



def choose_best_strategy(config, optimization_results: list[dict] | None):
    strategy = deepcopy(config.strategy)
    if not optimization_results:
        return strategy
    best = optimization_results[0]
    for key in ["trend_renko_size", "entry_renko_size", "min_trend_blocks", "pullback_min_blocks", "pullback_max_blocks", "target_points", "stop_points", "break_even_trigger"]:
        if key in best:
            setattr(strategy, key, best[key])
    if "trailing_enabled" in best:
        strategy.trailing.enabled = best["trailing_enabled"]
    if "cooldown_bars" in best:
        strategy.filters.cooldown_bars = best["cooldown_bars"]
    return strategy



def main() -> None:
    parser = argparse.ArgumentParser(description="MNQ dual synthetic Renko research engine")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    args = parser.parse_args()

    config = load_config(args.config)
    bars = load_market_data(config)
    in_sample, out_of_sample = split_dataset(bars, config.validation.in_sample_fraction)
    optimization_results = None
    strategy = config.strategy
    if config.run.mode == "optimize" and config.optimization.enabled:
        optimization_results = optimize(in_sample, config.strategy, config.optimization.parameter_grid, config.optimization.max_combinations)
        strategy = choose_best_strategy(config, optimization_results)

    dataset = prepare_dataset(bars, strategy)
    signals = generate_signals(dataset, strategy)
    backtest = run_backtest(signals.bars, strategy)
    blueprint = build_tradingview_blueprint(strategy)
    run_dir = config.run.output_dir / config.run.name
    write_outputs(run_dir, signals.bars, backtest, optimization_results, signals.assumptions, blueprint)
    payload = {
        "run_name": config.run.name,
        "rows_loaded": len(bars),
        "in_sample_rows": len(in_sample),
        "out_of_sample_rows": len(out_of_sample),
        "summary": backtest.summary,
    }
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
