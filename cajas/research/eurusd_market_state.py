"""Deterministic EURUSD 15m market-state prototype (research-only)."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

ULTRA_SHORT_WINDOW_BARS = 3
SHORT_WINDOW_BARS = 8
MID_WINDOW_BARS = 24
LONG_WINDOW_BARS = 128
MARKET_STATE_RULE_VERSION = "eurusd_market_state_rules_v0"

EXPECTED_BAR_HOURS = 0.25
GAP_HOURS_THRESHOLD = 1.0


REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close"]


def _ensure_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    out = a / b.replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan)


def _range_position(close: pd.Series, low: pd.Series, high: pd.Series) -> pd.Series:
    pos = _safe_div(close - low, high - low)
    return pos.clip(lower=0.0, upper=1.0)


def _vol_state(width: pd.Series, width128: pd.Series) -> pd.Series:
    ratio = _safe_div(width, width128)
    state = pd.Series(np.where(ratio < 0.6, "compressed", np.where(ratio > 1.4, "expanded", "normal")), index=width.index)
    state[ratio.isna()] = "unknown"
    return state


def compute_market_state_features(df: pd.DataFrame) -> pd.DataFrame:
    _ensure_columns(df)
    out = df.copy(deep=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")
    out = out.sort_values("timestamp").reset_index(drop=True)

    out["return_1"] = out["close"].pct_change(1)
    out["return_3"] = out["close"].pct_change(ULTRA_SHORT_WINDOW_BARS)
    out["return_8"] = out["close"].pct_change(SHORT_WINDOW_BARS)
    out["return_24"] = out["close"].pct_change(MID_WINDOW_BARS)
    out["return_128"] = out["close"].pct_change(LONG_WINDOW_BARS)

    out["slope_3"] = _safe_div(out["close"] - out["close"].shift(ULTRA_SHORT_WINDOW_BARS), pd.Series(ULTRA_SHORT_WINDOW_BARS, index=out.index))
    out["slope_8"] = _safe_div(out["close"] - out["close"].shift(SHORT_WINDOW_BARS), pd.Series(SHORT_WINDOW_BARS, index=out.index))
    out["slope_24"] = _safe_div(out["close"] - out["close"].shift(MID_WINDOW_BARS), pd.Series(MID_WINDOW_BARS, index=out.index))
    out["slope_128"] = _safe_div(out["close"] - out["close"].shift(LONG_WINDOW_BARS), pd.Series(LONG_WINDOW_BARS, index=out.index))

    out["range_width_3"] = out["high"].rolling(ULTRA_SHORT_WINDOW_BARS, min_periods=ULTRA_SHORT_WINDOW_BARS).max() - out["low"].rolling(ULTRA_SHORT_WINDOW_BARS, min_periods=ULTRA_SHORT_WINDOW_BARS).min()
    out["range_width_8"] = out["high"].rolling(SHORT_WINDOW_BARS, min_periods=SHORT_WINDOW_BARS).max() - out["low"].rolling(SHORT_WINDOW_BARS, min_periods=SHORT_WINDOW_BARS).min()
    out["range_width_24"] = out["high"].rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).max() - out["low"].rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).min()
    out["range_width_128"] = out["high"].rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).max() - out["low"].rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).min()

    out["normalized_slope_3"] = _safe_div(out["slope_3"], out["range_width_3"])
    out["normalized_slope_8"] = _safe_div(out["slope_8"], out["range_width_8"])
    out["normalized_slope_24"] = _safe_div(out["slope_24"], out["range_width_24"])
    out["normalized_slope_128"] = _safe_div(out["slope_128"], out["range_width_128"])

    out["range_high_3"] = out["high"].rolling(ULTRA_SHORT_WINDOW_BARS, min_periods=ULTRA_SHORT_WINDOW_BARS).max()
    out["range_low_3"] = out["low"].rolling(ULTRA_SHORT_WINDOW_BARS, min_periods=ULTRA_SHORT_WINDOW_BARS).min()
    out["range_high_8"] = out["high"].rolling(SHORT_WINDOW_BARS, min_periods=SHORT_WINDOW_BARS).max()
    out["range_low_8"] = out["low"].rolling(SHORT_WINDOW_BARS, min_periods=SHORT_WINDOW_BARS).min()
    out["range_high_24"] = out["high"].rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).max()
    out["range_low_24"] = out["low"].rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).min()
    out["range_high_128"] = out["high"].rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).max()
    out["range_low_128"] = out["low"].rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).min()

    out["range_position_3"] = _range_position(out["close"], out["range_low_3"], out["range_high_3"])
    out["range_position_8"] = _range_position(out["close"], out["range_low_8"], out["range_high_8"])
    out["range_position_24"] = _range_position(out["close"], out["range_low_24"], out["range_high_24"])
    out["range_position_128"] = _range_position(out["close"], out["range_low_128"], out["range_high_128"])

    out["range_ratio_3_8"] = _safe_div(out["range_width_3"], out["range_width_8"])
    out["range_ratio_8_128"] = _safe_div(out["range_width_8"], out["range_width_128"])
    out["range_ratio_24_128"] = _safe_div(out["range_width_24"], out["range_width_128"])

    out["volatility_state_3"] = _vol_state(out["range_width_3"], out["range_width_128"])
    out["volatility_state_8"] = _vol_state(out["range_width_8"], out["range_width_128"])
    out["volatility_state_24"] = _vol_state(out["range_width_24"], out["range_width_128"])
    out["volatility_state_128"] = _vol_state(out["range_width_128"], out["range_width_128"])

    body = (out["close"] - out["open"]).abs()
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    upper = out["high"] - out[["open", "close"]].max(axis=1)
    lower = out[["open", "close"]].min(axis=1) - out["low"]

    out["body_ratio_latest"] = _safe_div(body, rng)
    out["upper_wick_ratio_latest"] = _safe_div(upper, rng)
    out["lower_wick_ratio_latest"] = _safe_div(lower, rng)
    out["directional_body_latest"] = np.sign(out["close"] - out["open"])
    out["latest_close_position_in_candle"] = _range_position(out["close"], out["low"], out["high"])

    out["three_bar_direction_change"] = np.sign(out["return_3"] * out["return_8"]).map({-1.0: 1, 1.0: 0}).fillna(0).astype(int)
    out["three_bar_reversal_score"] = (
        out["three_bar_direction_change"]
        + (out["body_ratio_latest"] > 0.55).astype(int)
        + (out["latest_close_position_in_candle"].between(0.15, 0.85) == False).astype(int)
    )
    out["three_bar_rejection_score"] = (
        (out["upper_wick_ratio_latest"] > 0.45).astype(int)
        + (out["lower_wick_ratio_latest"] > 0.45).astype(int)
        + (out["body_ratio_latest"] < 0.3).astype(int)
    )

    prior3_high = out["high"].shift(1).rolling(ULTRA_SHORT_WINDOW_BARS, min_periods=ULTRA_SHORT_WINDOW_BARS).max()
    prior3_low = out["low"].shift(1).rolling(ULTRA_SHORT_WINDOW_BARS, min_periods=ULTRA_SHORT_WINDOW_BARS).min()
    out["latest_bar_breaks_prior_3_high"] = (out["high"] > prior3_high).fillna(False)
    out["latest_bar_breaks_prior_3_low"] = (out["low"] < prior3_low).fillna(False)
    out["latest_bar_returns_inside_prior_3_range"] = ((out["close"] <= prior3_high) & (out["close"] >= prior3_low)).fillna(False)

    d_high = out["high"].diff()
    d_low = out["low"].diff()
    out["higher_high_count_24"] = (d_high > 0).rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).sum()
    out["higher_low_count_24"] = (d_low > 0).rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).sum()
    out["lower_high_count_24"] = (d_high < 0).rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).sum()
    out["lower_low_count_24"] = (d_low < 0).rolling(MID_WINDOW_BARS, min_periods=MID_WINDOW_BARS).sum()
    out["higher_high_count_128"] = (d_high > 0).rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).sum()
    out["higher_low_count_128"] = (d_low > 0).rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).sum()
    out["lower_high_count_128"] = (d_high < 0).rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).sum()
    out["lower_low_count_128"] = (d_low < 0).rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).sum()

    delta_hours = out["timestamp"].diff().dt.total_seconds() / 3600.0
    gap_flag = (delta_hours > GAP_HOURS_THRESHOLD).fillna(False)
    out["gap_count_128"] = gap_flag.rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).sum()
    out["largest_gap_hours_128"] = delta_hours.rolling(LONG_WINDOW_BARS, min_periods=LONG_WINDOW_BARS).max()

    return out


def _trend_from_return(ret: float, pos_th: float, neg_th: float) -> str:
    if pd.isna(ret):
        return "unknown"
    if ret >= pos_th:
        return "up"
    if ret <= neg_th:
        return "down"
    return "flat"


def classify_market_state_row(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    r = row if isinstance(row, dict) else row.to_dict()
    r3 = float(r.get("return_3", np.nan))
    r8 = float(r.get("return_8", np.nan))
    r24 = float(r.get("return_24", np.nan))
    r128 = float(r.get("return_128", np.nan))
    pos8 = float(r.get("range_position_8", np.nan))
    pos24 = float(r.get("range_position_24", np.nan))
    pos128 = float(r.get("range_position_128", np.nan))
    body_dir = float(r.get("directional_body_latest", np.nan))
    up_w = float(r.get("upper_wick_ratio_latest", np.nan))
    low_w = float(r.get("lower_wick_ratio_latest", np.nan))
    rev_score = float(r.get("three_bar_reversal_score", 0.0) or 0.0)
    rej_score = float(r.get("three_bar_rejection_score", 0.0) or 0.0)
    breaks_hi = bool(r.get("latest_bar_breaks_prior_3_high", False))
    breaks_lo = bool(r.get("latest_bar_breaks_prior_3_low", False))
    returns_in = bool(r.get("latest_bar_returns_inside_prior_3_range", False))

    # ultra short 3
    ultra = "unknown"
    if pd.notna(r3):
        if r3 > 0.0012 and body_dir > 0:
            ultra = "micro_impulse_up"
        elif r3 < -0.0012 and body_dir < 0:
            ultra = "micro_impulse_down"
        elif rev_score >= 2 and r3 > 0 and body_dir > 0:
            ultra = "micro_reversal_up"
        elif rev_score >= 2 and r3 < 0 and body_dir < 0:
            ultra = "micro_reversal_down"
        elif low_w > 0.5 and returns_in:
            ultra = "micro_rejection_down"
        elif up_w > 0.5 and returns_in:
            ultra = "micro_rejection_up"
        elif abs(r3) < 0.00035:
            ultra = "micro_pause"
        else:
            ultra = "micro_noise"

    # short 8
    short = "unknown"
    if pd.notna(r8):
        if r8 > 0.0025:
            short = "impulse_up"
        elif r8 < -0.0025:
            short = "impulse_down"
        elif abs(r8) <= 0.0008:
            short = "sideways"
        elif breaks_hi and returns_in:
            short = "false_breakout"
        elif breaks_hi or breaks_lo:
            short = "breakout_attempt"
        elif ultra in {"micro_rejection_up", "micro_reversal_down"}:
            short = "rejection_up"
        elif ultra in {"micro_rejection_down", "micro_reversal_up"}:
            short = "rejection_down"
        else:
            short = "transition"

    # long 128
    long_state = "unknown"
    if pd.notna(r128):
        if r128 > 0.01:
            long_state = "uptrend"
        elif r128 < -0.01:
            long_state = "downtrend"
        elif abs(r128) <= 0.004:
            long_state = "sideways"
        else:
            long_state = "transition"

        if long_state == "uptrend" and r24 < -0.003:
            long_state = "weakening_uptrend"
        if long_state == "downtrend" and r24 > 0.003:
            long_state = "weakening_downtrend"
        if pos128 >= 0.75 and abs(r24) < 0.002:
            long_state = "high_level_consolidation"
        if pos128 <= 0.25 and abs(r24) < 0.002:
            long_state = "low_level_base"

    # mid 24
    mid = "unknown"
    if pd.notna(r24):
        if r24 > 0.006:
            mid = "uptrend"
        elif r24 < -0.006:
            mid = "downtrend"
        elif abs(r24) <= 0.0015:
            mid = "sideways"
        elif abs(r24) <= 0.003:
            mid = "consolidation"
        else:
            mid = "transition"

        if long_state in {"uptrend", "weakening_uptrend"} and r24 < -0.002:
            mid = "pullback"
        if long_state in {"downtrend", "weakening_downtrend"} and r24 > 0.002:
            mid = "rebound"

    # enrich short with context
    if short == "transition":
        if long_state in {"uptrend", "weakening_uptrend"} and r8 < -0.001:
            short = "minor_pullback"
        elif long_state in {"downtrend", "weakening_downtrend"} and r8 > 0.001:
            short = "minor_rebound"

    local = "unknown"
    if long_state in {"uptrend", "weakening_uptrend"} and mid == "pullback" and short in {"minor_rebound", "impulse_up", "rejection_down"}:
        local = "pullback_in_uptrend"
    elif long_state in {"downtrend", "weakening_downtrend"} and mid == "rebound" and short in {"minor_pullback", "impulse_down", "rejection_up"}:
        local = "rebound_in_downtrend"
    elif long_state == "high_level_consolidation":
        local = "high_level_consolidation"
    elif long_state == "low_level_base":
        local = "low_level_base"
    elif long_state == "sideways" and mid in {"sideways", "consolidation"}:
        local = "range_chop"
    elif long_state in {"uptrend", "downtrend"} and ultra in {"micro_reversal_up", "micro_reversal_down"} and rej_score >= 2:
        local = "exhaustion_risk"
    elif short == "breakout_attempt" and ultra in {"micro_impulse_up", "micro_impulse_down"}:
        local = "breakout_retest"
    elif short == "false_breakout":
        local = "failed_breakout"
    elif rej_score >= 2 and (breaks_hi or breaks_lo):
        local = "liquidity_sweep"
    elif ultra in {"micro_reversal_up", "micro_reversal_down"} and long_state in {"uptrend", "downtrend", "weakening_uptrend", "weakening_downtrend"}:
        local = "micro_reversal_inside_trend"
    elif mid in {"uptrend", "downtrend"} and short in {"impulse_up", "impulse_down"}:
        local = "trend_continuation"

    confidence = "low"
    direction_votes = 0
    if long_state in {"uptrend", "weakening_uptrend"} and mid in {"uptrend", "pullback", "consolidation"}:
        direction_votes += 1
    if long_state in {"downtrend", "weakening_downtrend"} and mid in {"downtrend", "rebound", "consolidation"}:
        direction_votes += 1
    if short in {"impulse_up", "impulse_down", "minor_pullback", "minor_rebound"}:
        direction_votes += 1
    if ultra in {"micro_impulse_up", "micro_impulse_down", "micro_reversal_up", "micro_reversal_down"}:
        direction_votes += 1
    if direction_votes >= 3:
        confidence = "high"
    elif direction_votes >= 2:
        confidence = "medium"

    rationale_zh = f"超短期={ultra};短期={short};中期={mid};长期={long_state};结构={local}"

    return {
        "ultra_short_state_3": ultra,
        "short_term_state_8": short,
        "mid_term_state_24": mid,
        "long_term_state_128": long_state,
        "local_structure_state": local,
        "structure_confidence": confidence,
        "market_state_rule_version": MARKET_STATE_RULE_VERSION,
        "market_state_rationale_zh": rationale_zh,
    }


def build_market_state_dataset(df: pd.DataFrame) -> pd.DataFrame:
    features = compute_market_state_features(df)
    states = features.apply(classify_market_state_row, axis=1, result_type="expand")
    out = pd.concat([features, states], axis=1)

    out["symbol"] = "EURUSD"
    out["timeframe"] = "15m"
    out["ultra_short_window_bars"] = ULTRA_SHORT_WINDOW_BARS
    out["short_window_bars"] = SHORT_WINDOW_BARS
    out["mid_window_bars"] = MID_WINDOW_BARS
    out["long_window_bars"] = LONG_WINDOW_BARS

    return out


def summarize_market_state_dataset(df: pd.DataFrame) -> dict[str, Any]:
    states = [
        "ultra_short_state_3",
        "short_term_state_8",
        "mid_term_state_24",
        "long_term_state_128",
        "local_structure_state",
    ]
    missing = [c for c in states if c not in df.columns]
    if missing:
        return {"status": "blocked", "missing_state_columns": missing}

    dist = {}
    for c in states:
        dist[c] = {str(k): int(v) for k, v in df[c].fillna("unknown").astype(str).value_counts().items()}

    conf = {str(k): int(v) for k, v in df["structure_confidence"].fillna("low").astype(str).value_counts().items()} if "structure_confidence" in df.columns else {}
    unknown_count = int((df[states].astype(str) == "unknown").sum().sum())
    gap_caveat_count = int(((df.get("gap_count_128", pd.Series([0] * len(df))) > 0).fillna(False)).sum())

    return {
        "status": "ready",
        "state_distribution": dist,
        "confidence_distribution": conf,
        "unknown_state_count": unknown_count,
        "gap_caveat_count": gap_caveat_count,
    }


def write_market_state_jsonl(df: pd.DataFrame, path: str) -> None:
    records = df.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as fp:
        for row in records:
            fp.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
