"""Error slicing analysis for prediction artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


def analyze_error_slices(
    *,
    prediction_csv: str | Path,
    output_dir: str | Path,
    run_name: str,
    row_limit: int | None = None,
    allow_large_data: bool = False,
) -> dict:
    path = Path(prediction_csv).expanduser().resolve()
    decision = evaluate_loading_decision(path, CsvLoadingPolicy(row_limit=row_limit, allow_large_data=allow_large_data))
    if decision["mode"] == "blocked_full_read":
        raise ValueError("large CSV full read blocked; pass allow_large_data or row_limit")
    df = pd.read_csv(path, nrows=row_limit if row_limit is not None else None)
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    df["is_error"] = (df["label"].astype(str) != df["predicted_label"].astype(str)).astype(int)
    slices: list[dict] = []
    if "datetime" in df.columns:
        dt = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
        df["hour"] = dt.dt.hour
        df["dayofweek"] = dt.dt.dayofweek
        for col in ["hour", "dayofweek"]:
            grp = df.groupby(col, observed=False)["is_error"].agg(["count", "mean"]).reset_index()
            for _, r in grp.iterrows():
                slices.append({"slice_type": col, "slice_value": int(r[col]), "count": int(r["count"]), "error_rate": float(r["mean"])})
    proba_cols = [c for c in df.columns if c.startswith("proba_")]
    if proba_cols:
        df["confidence"] = df[proba_cols].max(axis=1)
        df["confidence_bucket"] = pd.cut(df["confidence"], bins=[0.0, 0.4, 0.6, 0.8, 1.0], include_lowest=True)
        grp = df.groupby("confidence_bucket", observed=False)["is_error"].agg(["count", "mean"]).reset_index()
        for _, r in grp.iterrows():
            slices.append({"slice_type": "confidence_bucket", "slice_value": str(r["confidence_bucket"]), "count": int(r["count"]), "error_rate": float(r["mean"])})

    report = {"row_count": int(len(df)), "slices": slices, "trading_metrics_present": False}
    (out / "error_slice_report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(slices).to_csv(out / "error_slices.csv", index=False)
    report["output_dir"] = str(out)
    return report
