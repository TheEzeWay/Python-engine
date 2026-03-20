from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TrailingConfig:
    enabled: bool = False
    trigger_points: float = 0.0
    distance_points: float = 0.0


@dataclass
class SessionFilterConfig:
    enabled: bool = False
    start: str = "00:00"
    end: str = "23:59"


@dataclass
class VolatilityFilterConfig:
    enabled: bool = False
    atr_window: int = 14
    min_atr: float = 0.0


@dataclass
class FilterConfig:
    session: SessionFilterConfig = field(default_factory=SessionFilterConfig)
    max_trades_per_session: int = 999
    cooldown_bars: int = 0
    volatility: VolatilityFilterConfig = field(default_factory=VolatilityFilterConfig)


@dataclass
class StrategyConfig:
    trend_renko_size: float = 15.0
    entry_renko_size: float = 5.0
    min_trend_blocks: int = 2
    pullback_min_blocks: int = 2
    pullback_max_blocks: int = 4
    target_points: float = 24.0
    stop_points: float = 12.0
    break_even_trigger: float = 0.0
    break_even_offset: float = 0.0
    trailing: TrailingConfig = field(default_factory=TrailingConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)


@dataclass
class ResampleConfig:
    enabled: bool = False
    rule: str = "1min"


@dataclass
class DataConfig:
    input_type: str = "ohlcv_1m"
    timezone: str = "UTC"
    timestamp_column: str = "ts_event"
    delimiter: str = ","
    schema_map: dict[str, str] = field(default_factory=dict)
    resample: ResampleConfig = field(default_factory=ResampleConfig)


@dataclass
class OptimizationConfig:
    enabled: bool = True
    max_combinations: int = 100
    parameter_grid: dict[str, list[Any]] = field(default_factory=dict)


@dataclass
class ValidationConfig:
    in_sample_fraction: float = 0.7
    walk_forward_windows: int = 3


@dataclass
class ReportingConfig:
    save_charts: bool = True
    save_trade_log: bool = True
    save_monthly_stats: bool = True


@dataclass
class RunConfig:
    name: str
    data_path: Path
    output_dir: Path
    mode: str = "optimize"


@dataclass
class AppConfig:
    run: RunConfig
    data: DataConfig = field(default_factory=DataConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
