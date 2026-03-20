from __future__ import annotations

import math
import statistics



def sharpe_ratio(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return 0.0
    return (statistics.mean(values) / stdev) * math.sqrt(len(values))



def sortino_ratio(values: list[float]) -> float:
    downside = [x for x in values if x < 0]
    if len(values) < 2 or len(downside) < 2:
        return 0.0
    stdev = statistics.pstdev(downside)
    if stdev == 0:
        return 0.0
    return (statistics.mean(values) / stdev) * math.sqrt(len(values))



def max_drawdown(equity: list[float]) -> float:
    peak = float('-inf')
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        worst = min(worst, value - peak)
    return worst



def profit_factor(values: list[float]) -> float:
    gross_profit = sum(x for x in values if x > 0)
    gross_loss = abs(sum(x for x in values if x < 0))
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss



def expectancy(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0
