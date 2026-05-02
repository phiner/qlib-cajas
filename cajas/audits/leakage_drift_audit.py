"""Leakage and simple drift audit for train/holdout prepared datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.data_io.chunked_csv_reader import iter_csv_chunks
from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


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
    row_limit: int | None = None,
    chunk_size: int | None = None,
    sample_only: bool = False,
    allow_large_data: bool = False,
    selected_columns: list[str] | None = None,
    use_cache: bool = False,
    manifest: str | None = None,
) -> dict:
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    train_src = Path(train_path).expanduser().resolve()
    hold_src = Path(holdout_path).expanduser().resolve()
    fc = json.loads(Path(feature_columns_path).expanduser().resolve().read_text(encoding="utf-8")).get("feature_columns", [])
    cols: list[str] = ["datetime", label_col]
    for col in fc:
        if str(col) not in cols:
            cols.append(str(col))
    if selected_columns:
        for col in selected_columns:
            if col not in cols:
                cols.append(col)

    effective_row_limit = 1000 if sample_only and row_limit is None else row_limit
    policy = CsvLoadingPolicy(
        row_limit=effective_row_limit,
        chunk_size=chunk_size,
        sample_only=sample_only,
        allow_large_data=allow_large_data,
        selected_columns=cols,
        use_cache=use_cache,
        manifest=manifest,
    )
    train_decision = evaluate_loading_decision(train_src, policy)
    hold_decision = evaluate_loading_decision(hold_src, policy)
    if train_decision["mode"] == "blocked_full_read" or hold_decision["mode"] == "blocked_full_read":
        raise ValueError("large CSV full read blocked; pass allow_large_data or row_limit/chunk_size")

    if chunk_size:
        train = pd.concat(list(iter_csv_chunks(train_src, columns=cols, chunk_size=chunk_size, row_limit=effective_row_limit)), ignore_index=True)
        hold = pd.concat(list(iter_csv_chunks(hold_src, columns=cols, chunk_size=chunk_size, row_limit=effective_row_limit)), ignore_index=True)
    else:
        nrows = effective_row_limit if effective_row_limit is not None else None
        train = pd.read_csv(train_src, usecols=cols, nrows=nrows)
        hold = pd.read_csv(hold_src, usecols=cols, nrows=nrows)
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
        "loading_decisions": {"train": train_decision, "holdout": hold_decision},
        "trading_metrics_present": False,
    }
    (out / "leakage_drift_audit_report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(drift_rows).to_csv(out / "feature_drift_summary.csv", index=False)
    report["output_dir"] = str(out)
    return report
