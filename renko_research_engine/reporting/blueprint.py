from __future__ import annotations

from renko_research_engine.config.models import StrategyConfig



def build_tradingview_blueprint(strategy: StrategyConfig) -> str:
    return f"""
TradingView / Pine Script blueprint
=================================
1. Source timeframe: 1-minute candles.
2. Rebuild two synthetic Renko state machines from the 1-minute OHLC stream.
3. Trend Renko size: {strategy.trend_renko_size} points.
4. Entry Renko size: {strategy.entry_renko_size} points.
5. Trend rule: require >= {strategy.min_trend_blocks} confirmed trend Renko bricks in one direction.
6. Pullback rule: require entry Renko pullback between {strategy.pullback_min_blocks} and {strategy.pullback_max_blocks} bricks against the trend.
7. Trigger: first confirmed entry Renko brick back with the trend; submit order on the close of the same 1-minute bar.
8. Stops/targets: stop {strategy.stop_points} points, target {strategy.target_points} points.
9. Break-even: trigger {strategy.break_even_trigger} points, offset {strategy.break_even_offset} points.
10. Trailing: enabled={strategy.trailing.enabled}, trigger {strategy.trailing.trigger_points}, distance {strategy.trailing.distance_points}.
11. Use `barstate.isconfirmed` so alerts fire only after bar close.
12. Do not use lower-timeframe `request.security()` for signal generation unless you intentionally recreate the same deterministic bar-close state machine.
""".strip()
