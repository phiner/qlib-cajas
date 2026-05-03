"""Deterministic EURUSD 15m pattern feature scaffold (non-trading)."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

DEFAULT_HORIZONS = (3, 5, 8, 13, 21, 34, 55)


def compute_eurusd_pattern_features(
    df: pd.DataFrame,
    *,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    doji_body_ratio_threshold: float = 0.1,
) -> pd.DataFrame:
    required = {"open", "high", "low", "close"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    out = df.copy(deep=True)
    h = sorted({int(x) for x in horizons if int(x) > 0})

    out["body"] = out["close"] - out["open"]
    out["body_abs"] = out["body"].abs()
    out["range"] = out["high"] - out["low"]
    out["upper_wick"] = out["high"] - out[["open", "close"]].max(axis=1)
    out["lower_wick"] = out[["open", "close"]].min(axis=1) - out["low"]
    out["body_ratio"] = np.where(out["range"] != 0, out["body_abs"] / out["range"], 0.0)

    out["is_bullish"] = out["body"] > 0
    out["is_bearish"] = out["body"] < 0
    out["is_doji_like"] = out["body_ratio"] <= doji_body_ratio_threshold

    for k in h:
        out[f"close_pct_change_{k}"] = out["close"].pct_change(k)

        rolling_high = out["high"].rolling(k, min_periods=1).max()
        rolling_low = out["low"].rolling(k, min_periods=1).min()
        window_range = rolling_high - rolling_low
        out[f"rolling_range_position_{k}"] = np.where(
            window_range != 0,
            (out["close"] - rolling_low) / window_range,
            0.5,
        )

        net_move = out["close"] - out["close"].shift(k)
        total_move = out["close"].diff().abs().rolling(k, min_periods=1).sum()
        out[f"efficiency_ratio_{k}"] = np.where(total_move != 0, net_move.abs() / total_move, 0.0)

        out[f"atr_like_range_mean_{k}"] = out["range"].rolling(k, min_periods=1).mean()
        out[f"vol_norm_move_{k}"] = np.where(
            out[f"atr_like_range_mean_{k}"] != 0,
            net_move / out[f"atr_like_range_mean_{k}"],
            0.0,
        )

    return out


def validate_feature_scaffold_contract() -> dict[str, object]:
    fixture = pd.DataFrame(
        {
            "open": [1.0, 1.01, 1.02, 1.03, 1.04],
            "high": [1.02, 1.03, 1.04, 1.05, 1.06],
            "low": [0.99, 1.00, 1.01, 1.02, 1.03],
            "close": [1.01, 1.02, 1.03, 1.04, 1.05],
        }
    )
    out = compute_eurusd_pattern_features(fixture, horizons=(3, 5))
    required_cols = {
        "body",
        "body_abs",
        "upper_wick",
        "lower_wick",
        "range",
        "body_ratio",
        "is_bullish",
        "is_bearish",
        "is_doji_like",
        "close_pct_change_3",
        "rolling_range_position_3",
        "efficiency_ratio_3",
        "atr_like_range_mean_3",
        "vol_norm_move_3",
    }
    missing = sorted(required_cols.difference(out.columns))
    return {
        "status": "pass" if not missing else "fail",
        "missing_columns": missing,
        "horizons": [3, 5],
    }
