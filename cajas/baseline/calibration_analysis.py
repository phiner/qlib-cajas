"""Calibration analysis for classification prediction artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


def analyze_calibration(
    *,
    prediction_csv: str | Path,
    split: str,
    bucket_count: int = 10,
    row_limit: int | None = None,
    allow_large_data: bool = False,
) -> dict:
    path = Path(prediction_csv).expanduser().resolve()
    decision = evaluate_loading_decision(path, CsvLoadingPolicy(row_limit=row_limit, allow_large_data=allow_large_data))
    if decision["mode"] == "blocked_full_read":
        raise ValueError("large CSV full read blocked; pass allow_large_data or row_limit")
    df = pd.read_csv(path, nrows=row_limit if row_limit is not None else None)
    proba_cols = [c for c in df.columns if c.startswith("proba_")]
    if not proba_cols:
        raise ValueError("prediction file does not include probability columns")
    probs = df[proba_cols]
    df2 = df.copy()
    df2["confidence"] = probs.max(axis=1)
    df2["correct"] = (df2["label"].astype(str) == df2["predicted_label"].astype(str)).astype(int)
    edges = [i / bucket_count for i in range(bucket_count + 1)]
    df2["bucket"] = pd.cut(df2["confidence"], bins=edges, include_lowest=True, duplicates="drop")
    g = df2.groupby("bucket", observed=False)
    rows = []
    total = max(len(df2), 1)
    ece = 0.0
    for bucket, part in g:
        if len(part) == 0:
            continue
        acc = float(part["correct"].mean())
        conf = float(part["confidence"].mean())
        gap = abs(acc - conf)
        weight = len(part) / total
        ece += gap * weight
        rows.append({"bucket": str(bucket), "count": int(len(part)), "accuracy": acc, "mean_confidence": conf, "abs_gap": gap, "weight": weight})
    return {
        "split": split,
        "row_count": int(len(df2)),
        "bucket_count": bucket_count,
        "ece_like": ece,
        "rows": rows,
        "trading_metrics_present": False,
    }


def write_calibration_artifacts(*, report: dict, output_dir: str | Path) -> list[str]:
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    j = out / "calibration_report.json"
    c = out / "calibration_buckets.csv"
    j.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(report["rows"]).to_csv(c, index=False)
    return [str(j), str(c)]
