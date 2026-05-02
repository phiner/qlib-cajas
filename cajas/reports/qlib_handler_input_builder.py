"""Build normalized offline handler input package from feature/label CSV."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


def build_qlib_handler_input(
    *,
    input_csv: str | Path,
    out_dir: str | Path,
    instrument_col: str = "instrument",
    datetime_col: str = "datetime",
    label_columns: list[str] | None = None,
    sort_rows: bool = True,
    row_limit: int | None = None,
    chunk_size: int | None = None,
    sample_only: bool = False,
    allow_large_data: bool = False,
) -> dict:
    src = Path(input_csv).expanduser().resolve()
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    policy = CsvLoadingPolicy(
        row_limit=row_limit,
        chunk_size=chunk_size,
        sample_only=sample_only,
        allow_large_data=allow_large_data,
    )
    decision = evaluate_loading_decision(src, policy)
    if decision["mode"] == "blocked_full_read":
        raise ValueError("large CSV full read blocked; use allow_large_data or row_limit/chunk_size")
    if decision["mode"] in {"sampled_read", "chunked_read"} and chunk_size:
        chunks = []
        consumed = 0
        for chunk in pd.read_csv(src, chunksize=chunk_size):
            if row_limit is not None and consumed >= row_limit:
                break
            if row_limit is not None and consumed + len(chunk) > row_limit:
                chunk = chunk.iloc[: row_limit - consumed]
            chunks.append(chunk)
            consumed += len(chunk)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    else:
        nrows = row_limit if decision["mode"] == "sampled_read" else None
        df = pd.read_csv(src, nrows=nrows)
    labels = label_columns or ["future_direction_8"]
    required = [instrument_col, datetime_col] + labels

    warnings: list[dict] = []
    blocking: list[dict] = []

    for col in required:
        if col not in df.columns:
            blocking.append({"severity": "error", "code": "missing_required_column", "message": f"missing required column: {col}", "field": col})

    if instrument_col in df.columns and datetime_col in df.columns:
        dup_count = int(df.duplicated([instrument_col, datetime_col]).sum())
        if dup_count > 0:
            warnings.append({"severity": "warning", "code": "duplicate_keys", "message": f"duplicate instrument/datetime rows: {dup_count}", "field": f"{instrument_col},{datetime_col}"})

    feature_columns = [c for c in df.columns if c not in {instrument_col, datetime_col, *labels}]
    non_numeric = [c for c in feature_columns if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        warnings.append({"severity": "warning", "code": "non_numeric_features", "message": "non-numeric feature columns detected", "field": "feature_columns"})

    null_heavy = [c for c in df.columns if len(df) > 0 and float(df[c].isna().mean()) >= 0.2]
    if null_heavy:
        warnings.append({"severity": "warning", "code": "null_heavy_columns", "message": "columns with >=20% null values detected", "field": ",".join(null_heavy)})

    ordered_cols = [c for c in [instrument_col, datetime_col] if c in df.columns]
    ordered_cols += [c for c in feature_columns if c not in ordered_cols]
    ordered_cols += [c for c in labels if c in df.columns and c not in ordered_cols]
    ordered_cols += [c for c in df.columns if c not in ordered_cols]
    out_df = df[ordered_cols]

    if sort_rows and instrument_col in out_df.columns and datetime_col in out_df.columns:
        out_df = out_df.sort_values([instrument_col, datetime_col], kind="stable")

    out_df.to_csv(out / "handler_input.csv", index=False)
    (out / "columns.json").write_text(
        json.dumps(
            {
                "instrument_col": instrument_col,
                "datetime_col": datetime_col,
                "feature_columns": feature_columns,
                "label_columns": labels,
                "required_columns": required,
                "non_numeric_feature_columns": non_numeric,
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "splits.json").write_text(json.dumps({"available": False, "reason": "offline_ingestion_smoke_only"}, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out / "warnings.jsonl").open("w", encoding="utf-8") as f:
        for row in warnings + blocking:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    manifest = {
        "schema_version": "v1",
        "source_csv": str(src),
        "row_count": int(len(out_df)),
        "column_count": int(len(out_df.columns)),
        "feature_count": int(len(feature_columns)),
        "label_count": int(sum(1 for c in labels if c in out_df.columns)),
        "required_columns": required,
        "warnings_count": len(warnings),
        "blocking_count": len(blocking),
        "status": "blocked" if blocking else ("ready_with_warnings" if warnings else "ready_for_handler_smoke"),
    }
    (out / "handler_input_manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
