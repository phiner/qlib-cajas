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


MICRO_EVENT_VALUES = {
    "three_bar_reversal_up",
    "three_bar_reversal_down",
    "lower_sweep_reclaim",
    "upper_sweep_reject",
    "three_bar_exhaustion_up",
    "three_bar_exhaustion_down",
    "micro_pause",
    "micro_compression",
    "failed_followthrough_up",
    "failed_followthrough_down",
    "micro_noise",
    "unknown",
}


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
    state = pd.Series(
        np.where(ratio < 0.6, "compressed", np.where(ratio > 1.4, "expanded", "normal")),
        index=width.index,
    )
    state[ratio.isna()] = "unknown"
    return state


def compute_structure_features_8_24_128(df: pd.DataFrame) -> pd.DataFrame:
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

    out["prev_open_1"] = out["open"].shift(1)
    out["prev_close_1"] = out["close"].shift(1)
    out["prev_high_1"] = out["high"].shift(1)
    out["prev_low_1"] = out["low"].shift(1)
    out["prev_open_2"] = out["open"].shift(2)
    out["prev_close_2"] = out["close"].shift(2)
    out["prev_high_2"] = out["high"].shift(2)
    out["prev_low_2"] = out["low"].shift(2)

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


def compute_market_state_features(df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible alias used by existing tests/report code."""
    return compute_structure_features_8_24_128(df)


def detect_three_bar_micro_event(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    r = row if isinstance(row, dict) else row.to_dict()
    close = float(r.get("close", np.nan))
    open_ = float(r.get("open", np.nan))
    high = float(r.get("high", np.nan))
    low = float(r.get("low", np.nan))
    prev_close = float(r.get("prev_close_1", np.nan))
    prev_open = float(r.get("prev_open_1", np.nan))
    prev2_close = float(r.get("prev_close_2", np.nan))
    prev2_open = float(r.get("prev_open_2", np.nan))
    prev2_low = float(r.get("prev_low_2", np.nan))
    prev2_high = float(r.get("prev_high_2", np.nan))
    prev_low = float(r.get("prev_low_1", np.nan))
    prev_high = float(r.get("prev_high_1", np.nan))
    bw = float(r.get("body_ratio_latest", np.nan))
    up_w = float(r.get("upper_wick_ratio_latest", np.nan))
    low_w = float(r.get("lower_wick_ratio_latest", np.nan))
    returns_in = bool(r.get("latest_bar_returns_inside_prior_3_range", False))

    if any(pd.isna(v) for v in [close, open_, high, low, prev_close, prev_open, prev2_close, prev2_open]):
        return {
            "micro_pattern_event_3": "unknown",
            "micro_pattern_direction_3": "unknown",
            "micro_pattern_strength_3": "unknown",
            "micro_reversal_detected_3": False,
            "micro_rejection_detected_3": False,
            "micro_sweep_detected_3": False,
            "micro_event_rationale_zh": "样本不足，无法判定3K微事件",
        }

    up_seq = prev2_close < prev_close < close
    down_seq = prev2_close > prev_close > close
    current_bull = close > open_
    current_bear = close < open_

    reversal_up = prev2_close > prev_close and current_bull and close > prev_high and bw >= 0.45
    reversal_down = prev2_close < prev_close and current_bear and close < prev_low and bw >= 0.45

    lower_sweep_reclaim = (
        (not pd.isna(prev2_low))
        and (not pd.isna(prev_low))
        and low < min(prev2_low, prev_low)
        and close > min(open_, prev_close)
        and low_w > 0.35
    )
    upper_sweep_reject = (
        (not pd.isna(prev2_high))
        and (not pd.isna(prev_high))
        and high > max(prev2_high, prev_high)
        and close < max(open_, prev_close)
        and up_w > 0.35
    )

    failed_follow_up = high > prev_high and close <= prev_close and current_bear
    failed_follow_down = low < prev_low and close >= prev_close and current_bull

    event = "micro_noise"
    direction = "mixed"
    strength = "weak"
    reversal = False
    rejection = False
    sweep = False
    rationale = "3K形态冲突，归类为微噪音"

    if reversal_up:
        event = "three_bar_reversal_up"
        direction = "up"
        strength = "strong"
        reversal = True
        rationale = "前两根下压后当前阳线突破前高，构成3K向上反转"
    elif reversal_down:
        event = "three_bar_reversal_down"
        direction = "down"
        strength = "strong"
        reversal = True
        rationale = "前两根上推后当前阴线跌破前低，构成3K向下反转"
    elif lower_sweep_reclaim:
        event = "lower_sweep_reclaim"
        direction = "up"
        strength = "medium" if low_w > 0.45 else "weak"
        rejection = True
        sweep = True
        rationale = "下扫前低后收回区间内，表现为下影回收"
    elif upper_sweep_reject:
        event = "upper_sweep_reject"
        direction = "down"
        strength = "medium" if up_w > 0.45 else "weak"
        rejection = True
        sweep = True
        rationale = "上扫前高后收回区间内，表现为上影拒绝"
    elif up_seq and current_bear and up_w > 0.35 and bw < 0.45:
        event = "three_bar_exhaustion_up"
        direction = "down"
        strength = "medium"
        rejection = True
        rationale = "连续上推后实体减弱并出现上影，出现上行动能衰竭"
    elif down_seq and current_bull and low_w > 0.35 and bw < 0.45:
        event = "three_bar_exhaustion_down"
        direction = "up"
        strength = "medium"
        rejection = True
        rationale = "连续下压后实体减弱并出现下影，出现下行动能衰竭"
    elif failed_follow_up:
        event = "failed_followthrough_up"
        direction = "down"
        strength = "medium"
        rejection = True
        rationale = "尝试上破但收盘未跟随，形成上破失败"
    elif failed_follow_down:
        event = "failed_followthrough_down"
        direction = "up"
        strength = "medium"
        rejection = True
        rationale = "尝试下破但收盘未跟随，形成下破失败"
    elif abs(close - prev_close) <= max(1e-8, 0.15 * (high - low)) and bw <= 0.25:
        event = "micro_pause"
        direction = "neutral"
        strength = "weak"
        rationale = "实体很小且收盘变化有限，属于微暂停"
    elif bool(r.get("volatility_state_3", "unknown") == "compressed") and returns_in:
        event = "micro_compression"
        direction = "neutral"
        strength = "weak"
        rationale = "3K区间压缩且收回原区间，属于微压缩"

    if event not in MICRO_EVENT_VALUES:
        event = "unknown"

    return {
        "micro_pattern_event_3": event,
        "micro_pattern_direction_3": direction,
        "micro_pattern_strength_3": strength,
        "micro_reversal_detected_3": reversal,
        "micro_rejection_detected_3": rejection,
        "micro_sweep_detected_3": sweep,
        "micro_event_rationale_zh": rationale,
    }


def classify_structure_state_row(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    r = row if isinstance(row, dict) else row.to_dict()
    r8 = float(r.get("return_8", np.nan))
    r24 = float(r.get("return_24", np.nan))
    r128 = float(r.get("return_128", np.nan))
    pos128 = float(r.get("range_position_128", np.nan))
    breaks_hi = bool(r.get("latest_bar_breaks_prior_3_high", False))
    breaks_lo = bool(r.get("latest_bar_breaks_prior_3_low", False))
    returns_in = bool(r.get("latest_bar_returns_inside_prior_3_range", False))

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
        else:
            short = "transition"

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

    local = "unknown"
    if long_state in {"uptrend", "weakening_uptrend"} and mid == "pullback":
        local = "pullback_in_uptrend"
    elif long_state in {"downtrend", "weakening_downtrend"} and mid == "rebound":
        local = "rebound_in_downtrend"
    elif long_state == "high_level_consolidation":
        local = "high_level_consolidation"
    elif long_state == "low_level_base":
        local = "low_level_base"
    elif long_state == "sideways" and mid in {"sideways", "consolidation"}:
        local = "range_chop"
    elif mid in {"uptrend", "downtrend"} and short in {"impulse_up", "impulse_down"}:
        local = "trend_continuation"

    confidence = "low"
    votes = 0
    if long_state in {"uptrend", "weakening_uptrend"} and mid in {"uptrend", "pullback", "consolidation"}:
        votes += 1
    if long_state in {"downtrend", "weakening_downtrend"} and mid in {"downtrend", "rebound", "consolidation"}:
        votes += 1
    if short in {"impulse_up", "impulse_down", "transition"}:
        votes += 1
    if votes >= 3:
        confidence = "high"
    elif votes >= 2:
        confidence = "medium"

    return {
        "short_term_state_8": short,
        "mid_term_state_24": mid,
        "long_term_state_128": long_state,
        "local_structure_state": local,
        "structure_confidence": confidence,
    }


def combine_micro_event_with_structure(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    r = row if isinstance(row, dict) else row.to_dict()
    micro = str(r.get("micro_pattern_event_3", "unknown"))
    local = str(r.get("local_structure_state", "unknown"))
    long_state = str(r.get("long_term_state_128", "unknown"))

    if local == "pullback_in_uptrend" and micro in {"three_bar_reversal_up", "lower_sweep_reclaim", "failed_followthrough_down"}:
        local = "pullback_in_uptrend"
    elif local == "rebound_in_downtrend" and micro in {"three_bar_reversal_down", "upper_sweep_reject", "failed_followthrough_up"}:
        local = "rebound_in_downtrend"
    elif long_state == "high_level_consolidation" and micro in {"upper_sweep_reject", "three_bar_exhaustion_up"}:
        local = "exhaustion_risk"
    elif long_state == "sideways" and micro in {"micro_noise", "micro_pause", "micro_compression"}:
        local = "range_chop"

    structure = classify_structure_state_row(r)
    short = structure["short_term_state_8"]
    mid = structure["mid_term_state_24"]
    long_final = structure["long_term_state_128"]

    rationale_zh = (
        f"微事件={micro};短期结构={short};中期结构={mid};长期结构={long_final};"
        f"局部结构={local}"
    )
    return {
        "local_structure_state": local,
        "market_state_rationale_zh": rationale_zh,
    }


def classify_market_state_row(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    r = row if isinstance(row, dict) else row.to_dict()
    micro = detect_three_bar_micro_event(r)
    structure = classify_structure_state_row(r)
    merged = {**r, **micro, **structure}
    combined = combine_micro_event_with_structure(merged)

    return {
        **micro,
        **structure,
        **combined,
        "ultra_short_state_3": micro["micro_pattern_event_3"],
        "market_state_rule_version": MARKET_STATE_RULE_VERSION,
    }


def build_market_state_dataset(df: pd.DataFrame) -> pd.DataFrame:
    features = compute_structure_features_8_24_128(df)
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
    required_states = [
        "micro_pattern_event_3",
        "micro_pattern_direction_3",
        "micro_pattern_strength_3",
        "short_term_state_8",
        "mid_term_state_24",
        "long_term_state_128",
        "local_structure_state",
    ]
    missing = [c for c in required_states if c not in df.columns]
    if missing:
        return {"status": "blocked", "missing_state_columns": missing}

    dist = {
        "micro_pattern_event_distribution": {
            str(k): int(v)
            for k, v in df["micro_pattern_event_3"].fillna("unknown").astype(str).value_counts().items()
        },
        "micro_pattern_direction_distribution": {
            str(k): int(v)
            for k, v in df["micro_pattern_direction_3"].fillna("unknown").astype(str).value_counts().items()
        },
        "micro_pattern_strength_distribution": {
            str(k): int(v)
            for k, v in df["micro_pattern_strength_3"].fillna("unknown").astype(str).value_counts().items()
        },
        "short_term_state_distribution": {
            str(k): int(v)
            for k, v in df["short_term_state_8"].fillna("unknown").astype(str).value_counts().items()
        },
        "mid_term_state_distribution": {
            str(k): int(v)
            for k, v in df["mid_term_state_24"].fillna("unknown").astype(str).value_counts().items()
        },
        "long_term_state_distribution": {
            str(k): int(v)
            for k, v in df["long_term_state_128"].fillna("unknown").astype(str).value_counts().items()
        },
        "local_structure_state_distribution": {
            str(k): int(v)
            for k, v in df["local_structure_state"].fillna("unknown").astype(str).value_counts().items()
        },
    }

    conf = {
        str(k): int(v)
        for k, v in df["structure_confidence"].fillna("low").astype(str).value_counts().items()
    } if "structure_confidence" in df.columns else {}
    unknown_count = int((df[required_states].astype(str) == "unknown").sum().sum())
    gap_caveat_count = int(((df.get("gap_count_128", pd.Series([0] * len(df))) > 0).fillna(False)).sum())

    return {
        "status": "ready",
        **dist,
        "confidence_distribution": conf,
        "micro_reversal_count": int(df.get("micro_reversal_detected_3", pd.Series(False)).fillna(False).astype(bool).sum()),
        "micro_rejection_count": int(df.get("micro_rejection_detected_3", pd.Series(False)).fillna(False).astype(bool).sum()),
        "micro_sweep_count": int(df.get("micro_sweep_detected_3", pd.Series(False)).fillna(False).astype(bool).sum()),
        "unknown_state_count": unknown_count,
        "gap_caveat_count": gap_caveat_count,
    }


def write_market_state_jsonl(df: pd.DataFrame, path: str) -> None:
    records = df.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as fp:
        for row in records:
            fp.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
