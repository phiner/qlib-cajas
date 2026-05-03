"""Sanitize feature matrices to finite numeric values for model input."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NumericSanitizationReport:
    row_count: int
    feature_count: int
    nan_replaced: int
    pos_inf_replaced: int
    neg_inf_replaced: int
    clipped_values: int
    clip_abs_value: float
    fill_value: float
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def sanitize_features_for_model(
    features_df,
    *,
    clip_abs_value: float = 1e6,
    fill_value: float = 0.0,
):
    src = pd.DataFrame(features_df)
    df = src.copy()
    numeric = df.apply(pd.to_numeric, errors="coerce")

    # copy=True avoids read-only array views across pandas/numpy versions.
    vals = numeric.to_numpy(dtype=float, copy=True)
    pos_inf = np.isposinf(vals)
    neg_inf = np.isneginf(vals)

    vals[pos_inf] = float(clip_abs_value)
    vals[neg_inf] = -float(clip_abs_value)

    before_clip = vals.copy()
    vals = np.clip(vals, -float(clip_abs_value), float(clip_abs_value))
    clipped = int(np.sum(np.abs(before_clip) > float(clip_abs_value)))

    nan_mask = np.isnan(vals)
    nan_count = int(nan_mask.sum())
    vals[nan_mask] = float(fill_value)

    out = pd.DataFrame(vals, index=numeric.index, columns=numeric.columns)

    warnings: list[str] = []
    if nan_count > 0:
        warnings.append(f"NaN replaced with fill_value: {nan_count}")
    if int(pos_inf.sum()) > 0 or int(neg_inf.sum()) > 0:
        warnings.append("Infinite values replaced before clipping.")
    if clipped > 0:
        warnings.append(f"Values clipped by abs threshold: {clipped}")

    report = NumericSanitizationReport(
        row_count=int(out.shape[0]),
        feature_count=int(out.shape[1]),
        nan_replaced=nan_count,
        pos_inf_replaced=int(pos_inf.sum()),
        neg_inf_replaced=int(neg_inf.sum()),
        clipped_values=clipped,
        clip_abs_value=float(clip_abs_value),
        fill_value=float(fill_value),
        warnings=warnings,
    )
    return out, report
