# MNQ Dual Renko Research Engine

A beginner-friendly Python research engine for testing a two-synthetic-Renko MNQ strategy from your own Databento-derived CSV files.

## What this project does

- Loads your Databento-derived CSV without downloading data for you.
- Validates the schema and remaps alternative column names.
- Supports either already-aggregated OHLCV bars or trade-level data that is resampled into OHLCV.
- Rebuilds two synthetic Renko state machines from the 1-minute bar stream.
- Generates bar-close-only, automation-safe signals.
- Runs a backtest and optional grid-search optimization.
- Saves trade logs, summaries, monthly stats, parameter rankings, and a TradingView blueprint.

## Quick start

1. Create and activate a Python 3.10+ virtual environment.
2. Install the project:
   ```bash
   pip install -e .
   ```
3. Put your CSV into `data/`.
4. Copy `config.example.json` and edit the data path / schema map if needed.
5. Run:
   ```bash
   python run_engine.py --config config.example.json
   ```
6. Review the generated files in `outputs/<run_name>/`.

## Input expectations

### Default / recommended
Use a **1-minute OHLCV CSV** with these logical fields:

- timestamp
- open
- high
- low
- close
- volume

If your raw export uses different names, map them in `schema_map`.

### Alternate support
You can also provide **trade-level data** if you set:

```yaml
data:
  input_type: trades
  resample:
    enabled: true
    rule: 1min
```

Trade-level mode expects logical fields:
- timestamp
- price
- size

## Project layout

```text
renko_research_engine/
  config/
  data/
  renko/
  strategy/
  backtest/
  optimize/
  reporting/
  utils/
config.example.json
run_engine.py
data/
outputs/
```
