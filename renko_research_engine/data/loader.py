from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from renko_research_engine.config.models import AppConfig


class DataValidationError(ValueError):
    pass



def load_market_data(config: AppConfig) -> list[dict]:
    path = config.run.data_path
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter=config.data.delimiter)
        rows = list(reader)
    if not rows:
        raise DataValidationError("CSV file is empty.")
    mapped = []
    for raw in rows:
        row = _map_row(raw, config)
        mapped.append(row)
    mapped.sort(key=lambda item: item["timestamp"])
    if config.data.input_type == "trades":
        return _resample_trades(mapped)
    return mapped



def _map_row(raw: dict, config: AppConfig) -> dict:
    schema = config.data.schema_map
    timestamp_key = config.data.timestamp_column
    logical = {logical_name: raw.get(actual_name) for logical_name, actual_name in schema.items()}
    if timestamp_key not in raw:
        raise DataValidationError(f"Missing timestamp column '{timestamp_key}'")
    ts = _parse_timestamp(raw[timestamp_key])
    if config.data.input_type == 'trades':
        return {"timestamp": ts, "price": float(raw.get(schema.get("price", "price"), raw.get("price"))), "size": float(raw.get(schema.get("size", "size"), raw.get("size", 0)))}
    required = ["open", "high", "low", "close"]
    for col in required:
        if logical.get(col) is None and raw.get(col) is None:
            raise DataValidationError(f"Missing column mapping for '{col}'")
    return {
        "timestamp": ts,
        "open": float(logical.get("open", raw.get("open"))),
        "high": float(logical.get("high", raw.get("high"))),
        "low": float(logical.get("low", raw.get("low"))),
        "close": float(logical.get("close", raw.get("close"))),
        "volume": float(logical.get("volume", raw.get("volume", 0)) or 0),
    }



def _parse_timestamp(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value).astimezone(timezone.utc)



def _resample_trades(trades: list[dict]) -> list[dict]:
    buckets: dict[datetime, list[dict]] = {}
    for trade in trades:
        ts = trade["timestamp"].replace(second=0, microsecond=0)
        buckets.setdefault(ts, []).append(trade)
    bars = []
    for ts in sorted(buckets):
        chunk = buckets[ts]
        prices = [x["price"] for x in chunk]
        bars.append({
            "timestamp": ts,
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "volume": sum(x["size"] for x in chunk),
        })
    return bars
