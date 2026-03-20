from __future__ import annotations

from dataclasses import dataclass

from renko_research_engine.config.models import StrategyConfig


@dataclass
class SignalResult:
    bars: list[dict]
    assumptions: list[str]



def generate_signals(bars: list[dict], strategy: StrategyConfig) -> SignalResult:
    pullback_count = 0
    last_trend_dir = 0
    had_valid_pullback = False
    for idx, bar in enumerate(bars):
        bar["atr"] = _atr(bars, idx, strategy.filters.volatility.atr_window)
        trend_dir = bar.get("trend_last_dir", 0)
        entry_dir = bar.get("entry_last_dir", 0)
        trend_ready = trend_dir != 0 and bar.get("trend_confirmed_run", 0) >= strategy.min_trend_blocks
        bar["trend_ready"] = trend_ready

        if not trend_ready:
            pullback_count = 0
            had_valid_pullback = False
        else:
            if trend_dir != last_trend_dir:
                pullback_count = 0
                had_valid_pullback = False
            if bar.get("entry_bricks_this_bar", 0) > 0:
                if entry_dir == -trend_dir:
                    pullback_count += bar.get("entry_ending_run", 0)
                elif entry_dir == trend_dir:
                    bar["entry_rejoin"] = had_valid_pullback
                    pullback_count = 0
                    had_valid_pullback = False
            if strategy.pullback_min_blocks <= pullback_count <= strategy.pullback_max_blocks:
                had_valid_pullback = True
            if pullback_count > strategy.pullback_max_blocks:
                had_valid_pullback = False
        bar.setdefault("entry_rejoin", False)
        bar["pullback_blocks"] = pullback_count
        bar["pullback_valid"] = had_valid_pullback
        bar["long_signal"] = bool(bar["entry_rejoin"] and trend_dir == 1)
        bar["short_signal"] = bool(bar["entry_rejoin"] and trend_dir == -1)
        bar["signal"] = 1 if bar["long_signal"] else -1 if bar["short_signal"] else 0
        last_trend_dir = trend_dir or last_trend_dir
    assumptions = [
        "Renko bricks are confirmed only from completed 1-minute bars using a deterministic OHLC path assumption.",
        "Multiple synthetic Renko bricks may form inside one minute, but the engine only acts after that minute closes.",
        "A valid setup allows only one entry: the first entry-Renko brick back in the trend direction after a 2-to-4 brick pullback.",
        "No future bars are referenced when creating signals or trades.",
    ]
    return SignalResult(bars=bars, assumptions=assumptions)



def _atr(bars: list[dict], idx: int, window: int) -> float:
    start = max(0, idx - window + 1)
    chunk = bars[start : idx + 1]
    if not chunk:
        return 0.0
    return sum(bar["high"] - bar["low"] for bar in chunk) / len(chunk)
