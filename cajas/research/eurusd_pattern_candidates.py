"""Deterministic EURUSD 15m pattern candidate detection (review-only)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from cajas.research.eurusd_pattern_features import compute_eurusd_pattern_features

HORIZONS = [3, 5, 8, 13, 21, 34, 55]


def _priority(conf: float) -> str:
    if conf >= 0.85:
        return "high"
    if conf >= 0.7:
        return "medium"
    return "low"


def _add_candidate(rows: list[dict[str, Any]], base: dict[str, Any]) -> None:
    rows.append(base)


def detect_eurusd_pattern_candidates(
    clean_df: pd.DataFrame,
    *,
    min_confidence: float = 0.6,
) -> pd.DataFrame:
    work = compute_eurusd_pattern_features(clean_df, horizons=HORIZONS)
    if "timestamp" in work.columns:
        work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", utc=True)

    rows: list[dict[str, Any]] = []

    for i, row in work.iterrows():
        r = float(row.get("range", 0.0) or 0.0)
        if r <= 0:
            continue

        close = float(row["close"])
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        body_ratio = float(row.get("body_ratio", 0.0) or 0.0)
        upper_ratio = float((row.get("upper_wick", 0.0) or 0.0) / r)
        lower_ratio = float((row.get("lower_wick", 0.0) or 0.0) / r)

        atr8 = float(row.get("atr_like_range_mean_8", 0.0) or 0.0)
        atr34 = float(row.get("atr_like_range_mean_34", 0.0) or 0.0)
        compression_ratio = (atr8 / atr34) if atr34 > 0 else 0.0
        expansion_ratio = (r / atr8) if atr8 > 0 else 0.0

        s3 = float(row.get("close_pct_change_3", 0.0) or 0.0)
        s5 = float(row.get("close_pct_change_5", 0.0) or 0.0)
        s8 = float(row.get("close_pct_change_8", 0.0) or 0.0)
        s13 = float(row.get("close_pct_change_13", 0.0) or 0.0)
        s21 = float(row.get("close_pct_change_21", 0.0) or 0.0)
        eff21 = float(row.get("efficiency_ratio_21", 0.0) or 0.0)
        pos8 = float(row.get("rolling_range_position_8", 0.5) or 0.5)

        ts = row.get("timestamp")
        ts_text = ts.isoformat() if pd.notna(ts) else None
        src_idx = int(row.get("source_row_index", i))
        lookback_default = [3, 5, 8]

        def emit(candidate_type: str, conf: float, reasons: list[str], lookback: list[int]) -> None:
            if conf < min_confidence:
                return
            _add_candidate(
                rows,
                {
                    "timestamp": ts_text,
                    "source_row_index": src_idx,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "candidate_type": candidate_type,
                    "confidence_score": round(float(max(0.0, min(1.0, conf))), 4),
                    "reason_codes": "|".join(reasons),
                    "body_ratio": round(body_ratio, 6),
                    "upper_wick_ratio": round(upper_ratio, 6),
                    "lower_wick_ratio": round(lower_ratio, 6),
                    "range": round(r, 6),
                    "slope_3": round(s3, 8),
                    "slope_5": round(s5, 8),
                    "slope_8": round(s8, 8),
                    "slope_13": round(s13, 8),
                    "slope_21": round(s21, 8),
                    "efficiency_ratio_21": round(eff21, 6),
                    "rolling_range_position_8": round(pos8, 6),
                    "compression_ratio": round(compression_ratio, 6),
                    "expansion_ratio": round(expansion_ratio, 6),
                    "lookback_bars_used": "|".join(str(x) for x in lookback),
                    "review_priority": _priority(conf),
                },
            )

        if compression_ratio > 0 and compression_ratio < 0.75:
            emit("compression_candidate", 1.0 - min(1.0, compression_ratio), ["low_short_vs_long_range"], [8, 34])

        if expansion_ratio > 1.6:
            emit("expansion_candidate", min(1.0, expansion_ratio / 3.0), ["current_range_vs_recent_atr"], [8])

        if s3 > 0 and s5 > 0 and s8 > 0 and pos8 > 0.75:
            conf = min(1.0, 0.6 + max(0.0, s3 + s5 + s8) * 20)
            emit("short_trend_up_candidate", conf, ["positive_short_slopes", "high_range_position"], lookback_default)

        if s3 < 0 and s5 < 0 and s8 < 0 and pos8 < 0.25:
            conf = min(1.0, 0.6 + max(0.0, -(s3 + s5 + s8)) * 20)
            emit("short_trend_down_candidate", conf, ["negative_short_slopes", "low_range_position"], lookback_default)

        if s13 > 0 and s21 > 0 and eff21 >= 0.35:
            emit("mid_trend_up_candidate", min(1.0, 0.55 + eff21), ["positive_mid_slopes", "efficiency_above_threshold"], [13, 21])

        if s13 < 0 and s21 < 0 and eff21 >= 0.35:
            emit("mid_trend_down_candidate", min(1.0, 0.55 + eff21), ["negative_mid_slopes", "efficiency_above_threshold"], [13, 21])

        midpoint = (high + low) / 2.0
        if upper_ratio >= 0.45 and (close < midpoint or close < open_):
            emit("upper_wick_rejection_candidate", min(1.0, 0.55 + upper_ratio), ["upper_wick_large", "close_rejected_lower"], [1])

        if lower_ratio >= 0.45 and (close > midpoint or close > open_):
            emit("lower_wick_rejection_candidate", min(1.0, 0.55 + lower_ratio), ["lower_wick_large", "close_rejected_upper"], [1])

        if body_ratio <= 0.12 and r > 0:
            emit("doji_indecision_candidate", min(1.0, 0.65 + (0.12 - body_ratio)), ["small_body_ratio"], [1])

        if i >= 9:
            prev8 = work.iloc[max(0, i - 8):i]
            local_high = float(prev8["high"].max()) if not prev8.empty else high
            local_low = float(prev8["low"].min()) if not prev8.empty else low
            if high > local_high and close < local_high:
                conf = min(1.0, 0.6 + ((high - close) / r))
                emit("possible_false_breakout_candidate", conf, ["break_above_local_high_then_close_inside"], [8])
            elif low < local_low and close > local_low:
                conf = min(1.0, 0.6 + ((close - low) / r))
                emit("possible_false_breakout_candidate", conf, ["break_below_local_low_then_close_inside"], [8])

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "source_row_index",
                "open",
                "high",
                "low",
                "close",
                "candidate_type",
                "confidence_score",
                "reason_codes",
                "body_ratio",
                "upper_wick_ratio",
                "lower_wick_ratio",
                "range",
                "slope_3",
                "slope_5",
                "slope_8",
                "slope_13",
                "slope_21",
                "efficiency_ratio_21",
                "rolling_range_position_8",
                "compression_ratio",
                "expansion_ratio",
                "lookback_bars_used",
                "review_priority",
            ]
        )
    return out.sort_values(["timestamp", "candidate_type"]).reset_index(drop=True)
