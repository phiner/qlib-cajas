#!/usr/bin/env python3
"""Prepare a lightweight EURUSD 15m research dataset for Phase 0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare FX dataset with lightweight K-line features and future-direction label."
    )
    parser.add_argument("--input", required=True, help="Path to raw CSV input (supports ~ expansion).")
    parser.add_argument("--output-dir", required=True, help="Directory for prepared outputs.")
    parser.add_argument("--symbol", default="EURUSD", help="Symbol name for output rows.")
    parser.add_argument("--timeframe", default="15m", help="Timeframe label for output rows.")
    parser.add_argument("--horizon", type=int, default=8, help="Future horizon in bars.")
    parser.add_argument("--row-limit", type=int, default=None, help="Optional row limit for sampled reads.")
    parser.add_argument("--chunk-size", type=int, default=None, help="Optional chunk size; enables chunked read path.")
    parser.add_argument("--sample-only", action="store_true", help="Prefer sampled/chunked reads instead of full read.")
    parser.add_argument("--allow-large-data", action="store_true", help="Allow full reads for large CSV files.")
    return parser.parse_args()


def load_raw_csv(input_path: Path, policy: CsvLoadingPolicy) -> pd.DataFrame:
    decision = evaluate_loading_decision(input_path, policy)
    if decision["mode"] == "blocked_full_read":
        raise ValueError("large CSV full read blocked; use --allow-large-data or --row-limit/--chunk-size")
    if decision["warnings"]:
        print("warning:", "; ".join(decision["warnings"]))
    if decision["mode"] in {"sampled_read", "chunked_read"}:
        kwargs = {}
        if policy.selected_columns:
            kwargs["usecols"] = policy.selected_columns
        if policy.chunk_size:
            chunks = []
            consumed = 0
            for chunk in pd.read_csv(input_path, chunksize=policy.chunk_size, **kwargs):
                if policy.row_limit is not None and consumed >= policy.row_limit:
                    break
                if policy.row_limit is not None and consumed + len(chunk) > policy.row_limit:
                    chunk = chunk.iloc[: policy.row_limit - consumed]
                chunks.append(chunk)
                consumed += len(chunk)
            if not chunks:
                return pd.DataFrame()
            return pd.concat(chunks, ignore_index=True)
        nrows = policy.row_limit if policy.row_limit is not None else None
        return pd.read_csv(input_path, nrows=nrows, **kwargs)
    return pd.read_csv(input_path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    rename_map = {
        "Time (UTC)": "datetime",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=rename_map)

    required = {"datetime", "open", "high", "low", "close", "volume"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns after standardization: {missing}")

    return df


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    stats: dict[str, int] = {
        "input_rows": int(len(df)),
        "duplicate_rows_removed": 0,
        "invalid_datetime_rows_dropped": 0,
        "invalid_numeric_rows_dropped": 0,
    }

    df = df.copy()

    before_dedup = len(df)
    df = df.drop_duplicates()
    stats["duplicate_rows_removed"] = int(before_dedup - len(df))

    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    invalid_dt_mask = df["datetime"].isna()
    stats["invalid_datetime_rows_dropped"] = int(invalid_dt_mask.sum())
    df = df.loc[~invalid_dt_mask].copy()

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    invalid_num_mask = df[["open", "high", "low", "close", "volume"]].isna().any(axis=1)
    stats["invalid_numeric_rows_dropped"] = int(invalid_num_mask.sum())
    df = df.loc[~invalid_num_mask].copy()

    df = df.sort_values("datetime").reset_index(drop=True)
    df["datetime"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    stats["rows_after_cleaning"] = int(len(df))
    return df, stats


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    price_range = (df["high"] - df["low"]).replace(0.0, np.nan)
    body_abs = (df["close"] - df["open"]).abs()

    df["return_1"] = df["close"].pct_change(1)
    df["log_return_1"] = np.log(df["close"]).diff(1)
    df["hl_range"] = df["high"] - df["low"]
    df["body_size"] = body_abs
    df["upper_shadow"] = df["high"] - np.maximum(df["open"], df["close"])
    df["lower_shadow"] = np.minimum(df["open"], df["close"]) - df["low"]
    df["body_ratio"] = body_abs / price_range
    df["close_position_in_range"] = (df["close"] - df["low"]) / price_range
    df["range_pct"] = df["hl_range"] / df["close"].replace(0.0, np.nan)
    df["volume_change_1"] = df["volume"].pct_change(1)

    df["return_mean_4"] = df["return_1"].rolling(4).mean()
    df["return_mean_8"] = df["return_1"].rolling(8).mean()
    df["return_mean_16"] = df["return_1"].rolling(16).mean()
    df["return_std_8"] = df["return_1"].rolling(8).std()
    df["return_std_16"] = df["return_1"].rolling(16).std()
    df["range_mean_8"] = df["hl_range"].rolling(8).mean()
    df["range_mean_16"] = df["hl_range"].rolling(16).mean()

    return df


def add_future_direction_label(df: pd.DataFrame, horizon: int) -> tuple[pd.DataFrame, int]:
    if horizon <= 0:
        raise ValueError("--horizon must be a positive integer")

    df = df.copy()
    future_return_col = f"future_return_{horizon}"
    future_close_col = f"future_close_{horizon}"
    future_direction_col = f"future_direction_{horizon}"

    df[future_close_col] = df["close"].shift(-horizon)
    df[future_return_col] = df["close"].shift(-horizon) / df["close"] - 1.0

    df[future_direction_col] = np.where(
        df[future_return_col] > 0.0,
        "up",
        np.where(df[future_return_col] < 0.0, "down", "flat"),
    )

    unlabeled_rows = int(df[future_return_col].isna().sum())
    df = df.dropna(subset=[future_return_col]).copy()

    return df, unlabeled_rows


def write_manifest(
    manifest_path: Path,
    input_path: Path,
    output_dir: Path,
    output_csv: Path,
    symbol: str,
    timeframe: str,
    horizon: int,
    dataset: pd.DataFrame,
    clean_stats: dict,
    unlabeled_rows_dropped: int,
) -> None:
    label_col = f"future_direction_{horizon}"
    label_distribution = {
        k: int(v) for k, v in dataset[label_col].value_counts(dropna=False).sort_index().to_dict().items()
    }
    manifest = {
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "prepared_dataset_path": str(output_csv),
        "symbol": symbol,
        "timeframe": timeframe,
        "horizon": horizon,
        "label": label_col,
        "row_count": int(len(dataset)),
        "start_datetime": dataset["datetime"].iloc[0] if len(dataset) else None,
        "end_datetime": dataset["datetime"].iloc[-1] if len(dataset) else None,
        "columns": list(dataset.columns),
        "feature_columns": [
            c
            for c in dataset.columns
            if c not in {"datetime", "symbol", "timeframe", "open", "high", "low", "close", "volume", label_col}
        ],
        "label_distribution": label_distribution,
        "cleaning": clean_stats,
        "unlabeled_rows_dropped": unlabeled_rows_dropped,
        "created_by": "cajas/scripts/prepare_fx_dataset.py",
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    policy = CsvLoadingPolicy(
        row_limit=args.row_limit,
        chunk_size=args.chunk_size,
        sample_only=args.sample_only,
        allow_large_data=args.allow_large_data,
    )
    raw_df = load_raw_csv(input_path, policy)
    standardized = standardize_columns(raw_df)
    cleaned, clean_stats = clean_dataset(standardized)

    cleaned["symbol"] = args.symbol
    cleaned["timeframe"] = args.timeframe
    featured = add_features(cleaned)
    labeled, unlabeled_rows_dropped = add_future_direction_label(featured, horizon=args.horizon)

    # Backward-compatible simple aliases for downstream checks.
    labeled["range"] = labeled["hl_range"]
    labeled["body"] = labeled["body_size"]

    output_csv = output_dir / "prepared_dataset.csv"
    output_manifest = output_dir / "dataset_manifest.json"

    labeled.to_csv(output_csv, index=False)
    write_manifest(
        manifest_path=output_manifest,
        input_path=input_path,
        output_dir=output_dir,
        output_csv=output_csv,
        symbol=args.symbol,
        timeframe=args.timeframe,
        horizon=args.horizon,
        dataset=labeled,
        clean_stats=clean_stats,
        unlabeled_rows_dropped=unlabeled_rows_dropped,
    )

    print(f"Prepared dataset: {output_csv}")
    print(f"Manifest: {output_manifest}")
    print(f"Rows: {len(labeled)}")
    print(f"Columns: {len(labeled.columns)}")


if __name__ == "__main__":
    main()
