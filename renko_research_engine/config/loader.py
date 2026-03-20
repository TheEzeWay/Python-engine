from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from renko_research_engine.config.models import (
    AppConfig,
    DataConfig,
    FilterConfig,
    OptimizationConfig,
    ReportingConfig,
    ResampleConfig,
    RunConfig,
    SessionFilterConfig,
    StrategyConfig,
    TrailingConfig,
    ValidationConfig,
    VolatilityFilterConfig,
)


def _merge_dataclass(cls, payload: dict[str, Any]):
    return cls(**payload) if payload else cls()


def load_config(path: str | Path) -> AppConfig:
    raw = json.loads(Path(path).read_text())
    run = RunConfig(name=raw["run"]["name"], data_path=Path(raw["run"]["data_path"]), output_dir=Path(raw["run"].get("output_dir", "outputs")), mode=raw["run"].get("mode", "optimize"))
    data_raw = raw.get("data", {})
    strategy_raw = raw.get("strategy", {})
    filters_raw = strategy_raw.get("filters", {})
    return AppConfig(
        run=run,
        data=DataConfig(
            input_type=data_raw.get("input_type", "ohlcv_1m"),
            timezone=data_raw.get("timezone", "UTC"),
            timestamp_column=data_raw.get("timestamp_column", "ts_event"),
            delimiter=data_raw.get("delimiter", ","),
            schema_map=data_raw.get("schema_map", {}),
            resample=_merge_dataclass(ResampleConfig, data_raw.get("resample", {})),
        ),
        strategy=StrategyConfig(
            trend_renko_size=strategy_raw.get("trend_renko_size", 15.0),
            entry_renko_size=strategy_raw.get("entry_renko_size", 5.0),
            min_trend_blocks=strategy_raw.get("min_trend_blocks", 2),
            pullback_min_blocks=strategy_raw.get("pullback_min_blocks", 2),
            pullback_max_blocks=strategy_raw.get("pullback_max_blocks", 4),
            target_points=strategy_raw.get("target_points", 24.0),
            stop_points=strategy_raw.get("stop_points", 12.0),
            break_even_trigger=strategy_raw.get("break_even_trigger", 0.0),
            break_even_offset=strategy_raw.get("break_even_offset", 0.0),
            trailing=_merge_dataclass(TrailingConfig, strategy_raw.get("trailing", {})),
            filters=FilterConfig(
                session=_merge_dataclass(SessionFilterConfig, filters_raw.get("session", {})),
                max_trades_per_session=filters_raw.get("max_trades_per_session", 999),
                cooldown_bars=filters_raw.get("cooldown_bars", 0),
                volatility=_merge_dataclass(VolatilityFilterConfig, filters_raw.get("volatility", {})),
            ),
        ),
        optimization=_merge_dataclass(OptimizationConfig, raw.get("optimization", {})),
        validation=_merge_dataclass(ValidationConfig, raw.get("validation", {})),
        reporting=_merge_dataclass(ReportingConfig, raw.get("reporting", {})),
    )
