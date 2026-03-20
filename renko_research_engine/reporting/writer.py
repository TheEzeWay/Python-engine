from __future__ import annotations

import csv
import json
from pathlib import Path



def write_outputs(run_dir: Path, dataset: list[dict], result, optimization_results: list[dict] | None, assumptions: list[str], tradingview_blueprint: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(run_dir / "bars_with_signals.csv", dataset)
    (run_dir / "backtest_summary.json").write_text(json.dumps(result.summary, indent=2, default=str))
    _write_csv(run_dir / "trade_log.csv", result.trades)
    _write_csv(run_dir / "monthly_stats.csv", result.monthly)
    if optimization_results is not None:
        _write_csv(run_dir / "optimization_results.csv", optimization_results)
        _write_csv(run_dir / "parameter_rankings_top25.csv", optimization_results[:25])
    (run_dir / "assumptions.txt").write_text("\n".join(assumptions))
    (run_dir / "tradingview_blueprint.txt").write_text(tradingview_blueprint)



def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: str(v) if hasattr(v, 'isoformat') and k.endswith('time') else v for k, v in row.items()})
