"""Leakage and simple drift audit for train/holdout prepared datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _forbidden_feature(col: str, label_col: str) -> bool:
    c = col.lower()
    return c == label_col.lower() or c.startswith("future_close_") or c.startswith("future_return_") or c.startswith("future_direction_")


def run_leakage_drift_audit(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    feature_columns_path: str | Path,
    label_col: str,
    output_dir: str | Path,
    run_name: str,
) -> dict:
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    train = pd.read_csv(Path(train_path).expanduser().resolve())
    hold = pd.read_csv(Path(holdout_path).expanduser().resolve())
    fc = json.loads(Path(feature_columns_path).expanduser().resolve().read_text(encoding="utf-8")).get("feature_columns", [])
    forbidden = [c for c in fc if _forbidden_feature(str(c), label_col)]
    overlap_count = 0
    if "datetime" in train.columns and "datetime" in hold.columns:
        overlap_count = int(len(set(train["datetime"].astype(str)).intersection(set(hold["datetime"].astype(str)))))

    drift_rows = []
    for col in fc:
        if col in train.columns and col in hold.columns and pd.api.types.is_numeric_dtype(train[col]):
            t_mean = float(pd.to_numeric(train[col], errors="coerce").mean())
            h_mean = float(pd.to_numeric(hold[col], errors="coerce").mean())
            drift_rows.append({"feature": col, "train_mean": t_mean, "holdout_mean": h_mean, "mean_abs_diff": abs(t_mean - h_mean)})
    drift_rows.sort(key=lambda x: x["mean_abs_diff"], reverse=True)

    report = {
        "label_col": label_col,
        "forbidden_feature_columns": forbidden,
        "train_holdout_datetime_overlap_count": overlap_count,
        "drift_feature_count": len(drift_rows),
        "trading_metrics_present": False,
    }
    (out / "leakage_drift_audit_report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(drift_rows).to_csv(out / "feature_drift_summary.csv", index=False)
    report["output_dir"] = str(out)
    return report
