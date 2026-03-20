from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from renko_research_engine.config.models import StrategyConfig
from renko_research_engine.utils.metrics import expectancy, max_drawdown, profit_factor, sharpe_ratio, sortino_ratio


@dataclass
class BacktestResult:
    summary: dict
    trades: list[dict]
    equity_curve: list[dict]
    monthly: list[dict]



def run_backtest(bars: list[dict], strategy: StrategyConfig) -> BacktestResult:
    trades = []
    equity_curve = []
    equity_points = 0.0
    position = None
    last_exit_bar = -10**9
    trades_per_day: dict[str, int] = {}

    for index, bar in enumerate(bars):
        day = bar["timestamp"].strftime("%Y-%m-%d")
        trades_per_day.setdefault(day, 0)
        if position:
            exit_price, reason = _check_exit(bar, position, strategy)
            if exit_price is not None:
                pnl = (exit_price - position["entry_price"]) * position["direction"]
                trades.append({**position, "exit_time": bar["timestamp"], "exit_price": exit_price, "exit_reason": reason, "pnl_points": pnl, "holding_bars": index - position["entry_index"]})
                equity_points += pnl
                position = None
                last_exit_bar = index
        equity_curve.append({"timestamp": bar["timestamp"], "equity_points": equity_points})
        if position is not None:
            continue
        if index - last_exit_bar <= strategy.filters.cooldown_bars:
            continue
        if trades_per_day[day] >= strategy.filters.max_trades_per_session:
            continue
        if not _passes_filters(bar, strategy):
            continue
        if bar.get("signal", 0) == 0:
            continue
        direction = bar["signal"]
        entry = bar["close"]
        position = {
            "entry_time": bar["timestamp"],
            "entry_index": index,
            "entry_price": entry,
            "direction": direction,
            "stop_price": entry - strategy.stop_points * direction,
            "target_price": entry + strategy.target_points * direction,
            "max_favorable": 0.0,
        }
        trades_per_day[day] += 1

    monthly = _monthly_stats(trades)
    summary = _summary(trades, equity_curve)
    return BacktestResult(summary=summary, trades=trades, equity_curve=equity_curve, monthly=monthly)



def _passes_filters(bar: dict, strategy: StrategyConfig) -> bool:
    if strategy.filters.session.enabled:
        current = bar["timestamp"].strftime("%H:%M")
        if current < strategy.filters.session.start or current > strategy.filters.session.end:
            return False
    if strategy.filters.volatility.enabled and bar.get("atr", 0.0) < strategy.filters.volatility.min_atr:
        return False
    return True



def _check_exit(bar: dict, position: dict, strategy: StrategyConfig):
    direction = position["direction"]
    favorable = (bar["high"] - position["entry_price"]) if direction == 1 else (position["entry_price"] - bar["low"])
    position["max_favorable"] = max(position["max_favorable"], favorable)

    if strategy.break_even_trigger > 0 and position["max_favorable"] >= strategy.break_even_trigger:
        breakeven_stop = position["entry_price"] + strategy.break_even_offset * direction
        if direction == 1:
            position["stop_price"] = max(position["stop_price"], breakeven_stop)
        else:
            position["stop_price"] = min(position["stop_price"], breakeven_stop)
    if strategy.trailing.enabled and position["max_favorable"] >= strategy.trailing.trigger_points:
        trailing_stop = bar["close"] - strategy.trailing.distance_points * direction
        if direction == 1:
            position["stop_price"] = max(position["stop_price"], trailing_stop)
        else:
            position["stop_price"] = min(position["stop_price"], trailing_stop)

    if direction == 1:
        if bar["low"] <= position["stop_price"]:
            return position["stop_price"], "stop"
        if bar["high"] >= position["target_price"]:
            return position["target_price"], "target"
    else:
        if bar["high"] >= position["stop_price"]:
            return position["stop_price"], "stop"
        if bar["low"] <= position["target_price"]:
            return position["target_price"], "target"
    return None, None



def _monthly_stats(trades: list[dict]) -> list[dict]:
    bucket: dict[str, list[dict]] = {}
    for trade in trades:
        month = trade["entry_time"].strftime("%Y-%m")
        bucket.setdefault(month, []).append(trade)
    out = []
    for month, chunk in sorted(bucket.items()):
        pnls = [trade["pnl_points"] for trade in chunk]
        out.append({"month": month, "trades": len(chunk), "pnl_points": sum(pnls), "win_rate": sum(1 for x in pnls if x > 0) / len(pnls) if pnls else 0.0})
    return out



def _summary(trades: list[dict], equity_curve: list[dict]) -> dict:
    pnls = [trade["pnl_points"] for trade in trades]
    longs = [trade for trade in trades if trade["direction"] == 1]
    shorts = [trade for trade in trades if trade["direction"] == -1]
    return {
        "total_trades": len(trades),
        "win_rate": (sum(1 for x in pnls if x > 0) / len(pnls)) if pnls else 0.0,
        "profit_factor": profit_factor(pnls),
        "sharpe": sharpe_ratio(pnls),
        "sortino": sortino_ratio(pnls),
        "expectancy": expectancy(pnls),
        "max_drawdown": max_drawdown([row["equity_points"] for row in equity_curve]),
        "average_winner": sum(x for x in pnls if x > 0) / max(1, sum(1 for x in pnls if x > 0)),
        "average_loser": sum(x for x in pnls if x < 0) / max(1, sum(1 for x in pnls if x < 0)),
        "long_trades": len(longs),
        "short_trades": len(shorts),
        "long_win_rate": (sum(1 for t in longs if t["pnl_points"] > 0) / len(longs)) if longs else 0.0,
        "short_win_rate": (sum(1 for t in shorts if t["pnl_points"] > 0) / len(shorts)) if shorts else 0.0,
    }
