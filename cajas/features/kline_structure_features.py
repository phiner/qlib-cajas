"""Build non-forward-looking K-line structure features from prepared datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


@dataclass(frozen=True)
class KlineFeatureBuildReport:
    input_path: str
    output_path: str | None
    input_rows: int
    output_rows: int
    added_features: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def add_kline_structure_features(
    *,
    input_path: str | Path,
    output_path: str | Path | None = None,
    windows: list[int] | None = None,
    row_limit: int | None = None,
    allow_large_data: bool = False,
) -> tuple[pd.DataFrame, KlineFeatureBuildReport]:
    src = Path(input_path).expanduser().resolve()
    
    # Policy guard for large data reads
    policy = CsvLoadingPolicy(row_limit=row_limit, allow_large_data=allow_large_data)
    decision = evaluate_loading_decision(src, policy)
    
    if not decision["can_full_read"] and row_limit is None:
        raise ValueError(f"CSV requires row_limit or allow_large_data: {decision['warnings']}")
    
    read_kwargs = {}
    if row_limit is not None:
        read_kwargs["nrows"] = row_limit
    
    df = pd.read_csv(src, **read_kwargs).copy()
    windows = windows or [4, 8, 16, 32]
    required = {"open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    eps = 1e-12
    o = pd.to_numeric(df["open"], errors="coerce")
    h = pd.to_numeric(df["high"], errors="coerce")
    l = pd.to_numeric(df["low"], errors="coerce")
    c = pd.to_numeric(df["close"], errors="coerce")
    rng = (h - l).clip(lower=eps)
    body = c - o
    body_abs = body.abs()
    upper_wick = (h - np.maximum(o, c)).clip(lower=0.0)
    lower_wick = (np.minimum(o, c) - l).clip(lower=0.0)
    df["body_abs"] = body_abs
    df["body_ratio"] = body_abs / rng
    df["upper_wick"] = upper_wick
    df["lower_wick"] = lower_wick
    df["upper_wick_ratio"] = upper_wick / rng
    df["lower_wick_ratio"] = lower_wick / rng
    df["close_location"] = (c - l) / rng
    df["range_over_close"] = rng / c.abs().clip(lower=eps)
    df["return_1"] = c.pct_change()

    added = [
        "body_abs",
        "body_ratio",
        "upper_wick",
        "lower_wick",
        "upper_wick_ratio",
        "lower_wick_ratio",
        "close_location",
        "range_over_close",
        "return_1",
    ]
    for w in windows:
        roll_c_max = c.rolling(w, min_periods=1).max()
        roll_c_min = c.rolling(w, min_periods=1).min()
        roll_rng = (roll_c_max - roll_c_min).clip(lower=eps)
        df[f"return_mean_{w}"] = df["return_1"].rolling(w, min_periods=1).mean()
        df[f"return_std_{w}"] = df["return_1"].rolling(w, min_periods=1).std().fillna(0.0)
        df[f"rolling_range_pos_{w}"] = (c - roll_c_min) / roll_rng
        df[f"rolling_range_width_{w}"] = roll_rng / c.abs().clip(lower=eps)
        df[f"efficiency_ratio_{w}"] = (c - c.shift(w)).abs() / c.diff().abs().rolling(w, min_periods=1).sum().clip(lower=eps)
        df[f"slope_{w}"] = (c - c.shift(w)) / float(w)
        df[f"atr_like_{w}"] = (h - l).rolling(w, min_periods=1).mean()
        added.extend(
            [
                f"return_mean_{w}",
                f"return_std_{w}",
                f"rolling_range_pos_{w}",
                f"rolling_range_width_{w}",
                f"efficiency_ratio_{w}",
                f"slope_{w}",
                f"atr_like_{w}",
            ]
        )

    out_path = None
    if output_path is not None:
        out_path = str(Path(output_path).expanduser().resolve())
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    report = KlineFeatureBuildReport(
        input_path=str(src),
        output_path=out_path,
        input_rows=int(len(pd.read_csv(src))),
        output_rows=int(len(df)),
        added_features=added,
        warnings=[],
    )
    return df, report
