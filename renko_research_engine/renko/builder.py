from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RenkoState:
    brick_size: float
    last_close: float
    last_dir: int = 0
    confirmed_run: int = 0



def build_synthetic_renko_features(bars: list[dict], brick_size: float, prefix: str) -> list[dict]:
    state = RenkoState(brick_size=brick_size, last_close=bars[0]["close"])
    features = []
    for bar in bars:
        bricks = []
        for price in _intrabar_path(bar):
            while True:
                if price >= state.last_close + brick_size:
                    state.last_close += brick_size
                    bricks.append(1)
                elif price <= state.last_close - brick_size:
                    state.last_close -= brick_size
                    bricks.append(-1)
                else:
                    break
        if bricks:
            for brick in bricks:
                if brick == state.last_dir:
                    state.confirmed_run += 1
                else:
                    state.last_dir = brick
                    state.confirmed_run = 1
        features.append({
            f"{prefix}_last_close": state.last_close,
            f"{prefix}_last_dir": state.last_dir,
            f"{prefix}_bricks_this_bar": len(bricks),
            f"{prefix}_brick_sequence": ",".join(str(x) for x in bricks),
            f"{prefix}_bar_has_up_brick": int(1 in bricks),
            f"{prefix}_bar_has_down_brick": int(-1 in bricks),
            f"{prefix}_ending_run": _ending_run(bricks),
            f"{prefix}_confirmed_run": state.confirmed_run,
        })
    return features



def _intrabar_path(bar: dict) -> list[float]:
    if bar["close"] >= bar["open"]:
        return [bar["low"], bar["high"], bar["close"]]
    return [bar["high"], bar["low"], bar["close"]]



def _ending_run(bricks: list[int]) -> int:
    if not bricks:
        return 0
    last = bricks[-1]
    count = 0
    for brick in reversed(bricks):
        if brick == last:
            count += 1
        else:
            break
    return count
