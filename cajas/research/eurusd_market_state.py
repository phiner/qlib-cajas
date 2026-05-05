"""Deterministic EURUSD 15m market-state prototype (research-only)."""

from __future__ import annotations

import json
from pathlib import Path
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
MICRO_RULES_JSON_PATH = Path("cajas/data_examples/eurusd_micro_pattern_rules_v0.json")
MICRO_RULE_VERSION_FALLBACK = "eurusd_micro_pattern_rules_builtin_fallback_v0"
ALLOWED_RULE_CONDITION_KEYS = {
    "breaks_prior_low",
    "breaks_prior_high",
    "close_returns_inside_prior_range",
    "latest_close_position_min",
    "latest_close_position_max",
    "lower_wick_ratio_min",
    "upper_wick_ratio_min",
    "body_ratio_min",
    "body_ratio_max",
    "three_bar_return_min",
    "three_bar_return_max",
    "three_bar_return_abs_max",
    "range_width_max",
    "range_width_min",
    "range_ratio_3_8_max",
    "consecutive_direction",
    "direction_change",
    "latest_body_direction",
    "volatility_state_3",
    "max_wick_ratio_max",
}


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


def _builtin_micro_rules() -> dict[str, Any]:
    return {
        "rule_version": MICRO_RULE_VERSION_FALLBACK,
        "rules": [
            {
                "pattern_id": "micro_noise_fallback",
                "event": "micro_noise",
                "direction": "mixed",
                "strength": "weak",
                "priority": 1,
                "enabled": True,
                "description_zh": "回退规则：未命中其他规则时归类为微噪音",
                "conditions": {},
                "flags": {
                    "micro_reversal_detected_3": False,
                    "micro_rejection_detected_3": False,
                    "micro_sweep_detected_3": False,
                },
                "rationale_template_zh": "回退规则触发：未命中明确三K形态。",
            }
        ],
    }


def load_micro_pattern_rules(path: Path | None = None) -> dict[str, Any]:
    use_path = path or MICRO_RULES_JSON_PATH
    if not use_path.exists():
        return _builtin_micro_rules()
    try:
        payload = json.loads(use_path.read_text(encoding="utf-8"))
    except Exception:
        return _builtin_micro_rules()
    errors = validate_micro_pattern_rules(payload)
    if errors:
        return _builtin_micro_rules()
    return payload


def validate_micro_pattern_rules(rules: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rule_items = rules.get("rules")
    if not isinstance(rule_items, list) or not rule_items:
        return ["rules_missing_or_empty"]
    priorities = []
    for idx, rule in enumerate(rule_items):
        if not isinstance(rule, dict):
            errors.append(f"rule_{idx}_not_object")
            continue
        for k in ["pattern_id", "event", "direction", "strength", "priority", "enabled", "conditions", "flags"]:
            if k not in rule:
                errors.append(f"rule_{idx}_missing_{k}")
        cond = rule.get("conditions", {})
        if not isinstance(cond, dict):
            errors.append(f"rule_{idx}_conditions_not_object")
        else:
            bad_keys = [k for k in cond.keys() if k not in ALLOWED_RULE_CONDITION_KEYS]
            if bad_keys:
                errors.append(f"rule_{idx}_invalid_condition_keys:{','.join(sorted(bad_keys))}")
        priorities.append(rule.get("priority"))
    if len(set(priorities)) != len(priorities):
        errors.append("priority_not_unique")
    return errors


def evaluate_micro_pattern_rule(window_metrics: dict[str, Any], rule: dict[str, Any]) -> bool:
    cond = rule.get("conditions", {})
    if not isinstance(cond, dict):
        return False
    for key, expected in cond.items():
        v = window_metrics.get(key)
        if key in {"breaks_prior_low", "breaks_prior_high", "close_returns_inside_prior_range"}:
            if bool(v) != bool(expected):
                return False
        elif key.endswith("_min"):
            if pd.isna(v) or float(v) < float(expected):
                return False
        elif key.endswith("_max"):
            if pd.isna(v) or float(v) > float(expected):
                return False
        elif key in {"consecutive_direction", "direction_change", "latest_body_direction", "volatility_state_3"}:
            if str(v) != str(expected):
                return False
        elif key == "three_bar_return_abs_max":
            if pd.isna(v) or abs(float(v)) > float(expected):
                return False
        else:
            return False
    return True


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
            "micro_event_reason_code": "micro_rule_window_insufficient",
            "micro_reversal_detected_3": False,
            "micro_rejection_detected_3": False,
            "micro_sweep_detected_3": False,
            "micro_event_rationale_zh": "样本不足，无法判定3K微事件",
            "micro_pattern_rule_version": MICRO_RULE_VERSION_FALLBACK,
            "micro_pattern_rule_id": "none",
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

    metrics = {
        "breaks_prior_low": bool(low < min(prev2_low, prev_low)) if not pd.isna(prev2_low) and not pd.isna(prev_low) else False,
        "breaks_prior_high": bool(high > max(prev2_high, prev_high)) if not pd.isna(prev2_high) and not pd.isna(prev_high) else False,
        "close_returns_inside_prior_range": bool(returns_in),
        "latest_close_position_min": float(r.get("latest_close_position_in_candle", np.nan)),
        "latest_close_position_max": float(r.get("latest_close_position_in_candle", np.nan)),
        "lower_wick_ratio_min": low_w,
        "upper_wick_ratio_min": up_w,
        "body_ratio_min": bw,
        "body_ratio_max": bw,
        "three_bar_return_min": float(r.get("return_3", np.nan)),
        "three_bar_return_max": float(r.get("return_3", np.nan)),
        "three_bar_return_abs_max": abs(float(r.get("return_3", np.nan))) if pd.notna(r.get("return_3", np.nan)) else np.nan,
        "range_width_max": float(r.get("range_width_3", np.nan)),
        "range_width_min": float(r.get("range_width_3", np.nan)),
        "range_ratio_3_8_max": float(r.get("range_ratio_3_8", np.nan)),
        "consecutive_direction": "up" if up_seq else ("down" if down_seq else "mixed"),
        "direction_change": "down_to_up" if reversal_up else ("up_to_down" if reversal_down else "none"),
        "latest_body_direction": "bull" if current_bull else ("bear" if current_bear else "flat"),
        "volatility_state_3": str(r.get("volatility_state_3", "unknown")),
        "max_wick_ratio_max": max(up_w, low_w),
    }

    payload = load_micro_pattern_rules()
    rules = sorted([x for x in payload.get("rules", []) if bool(x.get("enabled", False))], key=lambda x: int(x.get("priority", 0)), reverse=True)
    for rule in rules:
        if evaluate_micro_pattern_rule(metrics, rule):
            event = str(rule.get("event", "unknown"))
            if event not in MICRO_EVENT_VALUES:
                event = "unknown"
            flags = rule.get("flags", {})
            return {
                "micro_pattern_event_3": event,
                "micro_pattern_direction_3": str(rule.get("direction", "unknown")),
                "micro_pattern_strength_3": str(rule.get("strength", "unknown")),
                "micro_event_reason_code": str(rule.get("pattern_id", "unknown_rule")),
                "micro_reversal_detected_3": bool(flags.get("micro_reversal_detected_3", False)),
                "micro_rejection_detected_3": bool(flags.get("micro_rejection_detected_3", False)),
                "micro_sweep_detected_3": bool(flags.get("micro_sweep_detected_3", False)),
                "micro_event_rationale_zh": str(rule.get("rationale_template_zh", "规则命中")),
                "micro_pattern_rule_version": str(payload.get("rule_version", MICRO_RULE_VERSION_FALLBACK)),
                "micro_pattern_rule_id": str(rule.get("pattern_id", "unknown_rule")),
            }

    return {
        "micro_pattern_event_3": "micro_noise",
        "micro_pattern_direction_3": "mixed",
        "micro_pattern_strength_3": "weak",
        "micro_event_reason_code": "micro_noise_fallback",
        "micro_reversal_detected_3": False,
        "micro_rejection_detected_3": False,
        "micro_sweep_detected_3": False,
        "micro_event_rationale_zh": "未命中规则，归类为微噪音。",
        "micro_pattern_rule_version": str(payload.get("rule_version", MICRO_RULE_VERSION_FALLBACK)),
        "micro_pattern_rule_id": "micro_noise_fallback",
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
    short_reason = "structure_8_unknown"
    if pd.notna(r8):
        if r8 > 0.0025:
            short = "impulse_up"
            short_reason = "structure_8_impulse_up"
        elif r8 < -0.0025:
            short = "impulse_down"
            short_reason = "structure_8_impulse_down"
        elif abs(r8) <= 0.0008:
            short = "sideways"
            short_reason = "structure_8_sideways_low_return"
        elif breaks_hi and returns_in:
            short = "false_breakout"
            short_reason = "structure_8_false_breakout"
        elif breaks_hi or breaks_lo:
            short = "breakout_attempt"
            short_reason = "structure_8_breakout_attempt"
        else:
            short = "transition"
            short_reason = "structure_8_transition"

    long_state = "unknown"
    long_reason = "structure_128_unknown"
    if pd.notna(r128):
        if r128 > 0.01:
            long_state = "uptrend"
            long_reason = "structure_128_uptrend"
        elif r128 < -0.01:
            long_state = "downtrend"
            long_reason = "structure_128_downtrend"
        elif abs(r128) <= 0.004:
            long_state = "sideways"
            long_reason = "structure_128_sideways_low_slope"
        else:
            long_state = "transition"
            long_reason = "structure_128_transition"

        if long_state == "uptrend" and r24 < -0.003:
            long_state = "weakening_uptrend"
            long_reason = "structure_128_weakening_uptrend"
        if long_state == "downtrend" and r24 > 0.003:
            long_state = "weakening_downtrend"
            long_reason = "structure_128_weakening_downtrend"
        if pos128 >= 0.75 and abs(r24) < 0.002:
            long_state = "high_level_consolidation"
            long_reason = "structure_128_high_level_consolidation"
        if pos128 <= 0.25 and abs(r24) < 0.002:
            long_state = "low_level_base"
            long_reason = "structure_128_low_level_base"

    mid = "unknown"
    mid_reason = "structure_24_unknown"
    if pd.notna(r24):
        if r24 > 0.006:
            mid = "uptrend"
            mid_reason = "structure_24_uptrend"
        elif r24 < -0.006:
            mid = "downtrend"
            mid_reason = "structure_24_downtrend"
        elif abs(r24) <= 0.0015:
            mid = "sideways"
            mid_reason = "structure_24_sideways"
        elif abs(r24) <= 0.003:
            mid = "consolidation"
            mid_reason = "structure_24_consolidation"
        else:
            mid = "transition"
            mid_reason = "structure_24_transition"

        if long_state in {"uptrend", "weakening_uptrend"} and r24 < -0.002:
            mid = "pullback"
            mid_reason = "structure_24_pullback_in_128_uptrend"
        if long_state in {"downtrend", "weakening_downtrend"} and r24 > 0.002:
            mid = "rebound"
            mid_reason = "structure_24_rebound_in_128_downtrend"

    local = "unknown"
    local_reason = "structure_local_unknown"
    if long_state in {"uptrend", "weakening_uptrend"} and mid == "pullback":
        local = "pullback_in_uptrend"
        local_reason = "structure_local_pullback_in_uptrend"
    elif long_state in {"downtrend", "weakening_downtrend"} and mid == "rebound":
        local = "rebound_in_downtrend"
        local_reason = "structure_local_rebound_in_downtrend"
    elif long_state == "high_level_consolidation":
        local = "high_level_consolidation"
        local_reason = "structure_local_high_level_consolidation"
    elif long_state == "low_level_base":
        local = "low_level_base"
        local_reason = "structure_local_low_level_base"
    elif long_state == "sideways" and mid in {"sideways", "consolidation"}:
        local = "range_chop"
        local_reason = "structure_local_range_chop"
    elif mid in {"uptrend", "downtrend"} and short in {"impulse_up", "impulse_down"}:
        local = "trend_continuation"
        local_reason = "structure_local_trend_continuation"

    confidence = "low"
    confidence_reason = "confidence_conflicting_windows"
    votes = 0
    if long_state in {"uptrend", "weakening_uptrend"} and mid in {"uptrend", "pullback", "consolidation"}:
        votes += 1
    if long_state in {"downtrend", "weakening_downtrend"} and mid in {"downtrend", "rebound", "consolidation"}:
        votes += 1
    if short in {"impulse_up", "impulse_down", "transition"}:
        votes += 1
    if votes >= 3:
        confidence = "high"
        confidence_reason = "confidence_aligned_windows"
    elif votes >= 2:
        confidence = "medium"
        confidence_reason = "confidence_partially_aligned_windows"

    return {
        "short_term_state_8": short,
        "mid_term_state_24": mid,
        "long_term_state_128": long_state,
        "local_structure_state": local,
        "structure_confidence": confidence,
        "short_structure_reason_code": short_reason,
        "mid_structure_reason_code": mid_reason,
        "long_structure_reason_code": long_reason,
        "local_structure_reason_code": local_reason,
        "confidence_reason_code": confidence_reason,
    }


def combine_micro_event_with_structure(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    r = row if isinstance(row, dict) else row.to_dict()
    micro = str(r.get("micro_pattern_event_3", "unknown"))
    local = str(r.get("local_structure_state", "unknown"))
    long_state = str(r.get("long_term_state_128", "unknown"))

    combined_reason = "combine_no_adjustment"
    if local == "pullback_in_uptrend" and micro in {"three_bar_reversal_up", "lower_sweep_reclaim", "failed_followthrough_down"}:
        local = "pullback_in_uptrend"
        combined_reason = "combine_pullback_uptrend_supported_by_micro_up"
    elif local == "rebound_in_downtrend" and micro in {"three_bar_reversal_down", "upper_sweep_reject", "failed_followthrough_up"}:
        local = "rebound_in_downtrend"
        combined_reason = "combine_rebound_downtrend_supported_by_micro_down"
    elif long_state == "high_level_consolidation" and micro in {"upper_sweep_reject", "three_bar_exhaustion_up"}:
        local = "exhaustion_risk"
        combined_reason = "combine_high_consolidation_exhaustion_risk"
    elif long_state == "sideways" and micro in {"micro_noise", "micro_pause", "micro_compression"}:
        local = "range_chop"
        combined_reason = "combine_sideways_micro_range_chop"

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
        "combined_reason_code": combined_reason,
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

    loaded_rules = load_micro_pattern_rules()
    rule_version_series = df.get("micro_pattern_rule_version", pd.Series([MICRO_RULE_VERSION_FALLBACK] * len(df))).fillna(MICRO_RULE_VERSION_FALLBACK).astype(str)
    rule_version_value = str(rule_version_series.value_counts().index[0]) if len(rule_version_series) > 0 else MICRO_RULE_VERSION_FALLBACK
    return {
        "status": "ready",
        **dist,
        "micro_pattern_rule_version": rule_version_value,
        "micro_pattern_rule_count": int(len(loaded_rules.get("rules", []))),
        "confidence_distribution": conf,
        "micro_reversal_count": int(df.get("micro_reversal_detected_3", pd.Series(False)).fillna(False).astype(bool).sum()),
        "micro_rejection_count": int(df.get("micro_rejection_detected_3", pd.Series(False)).fillna(False).astype(bool).sum()),
        "micro_sweep_count": int(df.get("micro_sweep_detected_3", pd.Series(False)).fillna(False).astype(bool).sum()),
        "micro_event_reason_code_distribution": {
            str(k): int(v)
            for k, v in df.get("micro_event_reason_code", pd.Series(dtype=str)).fillna("unknown").astype(str).value_counts().items()
        },
        "structure_reason_code_distribution": {
            str(k): int(v)
            for k, v in df.get("local_structure_reason_code", pd.Series(dtype=str)).fillna("unknown").astype(str).value_counts().items()
        },
        "confidence_reason_code_distribution": {
            str(k): int(v)
            for k, v in df.get("confidence_reason_code", pd.Series(dtype=str)).fillna("unknown").astype(str).value_counts().items()
        },
        "unknown_state_count": unknown_count,
        "gap_caveat_count": gap_caveat_count,
    }


def write_market_state_jsonl(df: pd.DataFrame, path: str) -> None:
    records = df.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as fp:
        for row in records:
            fp.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
