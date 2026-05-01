"""Rolling-year validation planning for available 2020-2025 local data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_rolling_year_validation_plan(*, output_dir: str | Path, run_name: str) -> dict:
    rows = [
        {"name": "train_2020_2021_validate_2022", "train_start": "2020-01-01", "train_end": "2021-12-31", "validate_year": 2022},
        {"name": "train_2020_2022_validate_2023", "train_start": "2020-01-01", "train_end": "2022-12-31", "validate_year": 2023},
        {"name": "train_2020_2023_validate_2024", "train_start": "2020-01-01", "train_end": "2023-12-31", "validate_year": 2024},
        {"name": "train_2020_2024_validate_2025", "train_start": "2020-01-01", "train_end": "2024-12-31", "validate_year": 2025},
    ]
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    report = {"rows": rows, "execution_mode": "plan_only", "trading_metrics_present": False}
    (out / "rolling_year_validation_plan.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(out / "rolling_year_validation_plan.csv", index=False)
    report["output_dir"] = str(out)
    return report
