"""Deterministic EURUSD 15m pattern candidate detection (review-only)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from cajas.research.eurusd_pattern_features import compute_eurusd_pattern_features

HORIZONS = [3, 5, 8, 13, 21, 34, 55]

TREND_SEGMENT_DEFAULTS = {
    "max_candidates_per_segment": 1,
    "target_fraction": 0.5,
    "avoid_last_n_bars": 4,
    "max_segment_position_fraction": 0.75,
    "rebound_lookahead_bars": 4,
    "rebound_threshold_atr_multiple": 0.5,
    "exclude_late_rebound_anchor": True,
}

CAUSAL_PAST_ONLY = {
    "causal_candidate": True,
    "candidate_logic_uses_future_bars": False,
    "candidate_logic_future_bars_used": 0,
    "review_filter_uses_future_bars": False,
    "review_filter_future_bars_used": 0,
    "label_uses_future_bars": True,
    "future_usage_role": "label_evaluation",
    "not_for_live_signal": True,
    "candidate_logic_window": "past_only",
    "review_filter_window": "",
    "label_window": "human_visible_forward_context",
}


def _priority(conf: float) -> str:
    if conf >= 0.85:
        return "high"
    if conf >= 0.7:
        return "medium"
    return "low"


def _add_candidate(rows: list[dict[str, Any]], base: dict[str, Any]) -> None:
    rows.append(base)


def detect_trend_segments_from_mask(mask: pd.Series, *, max_false_gap: int = 0) -> list[tuple[int, int]]:
    flags = [bool(x) for x in mask.fillna(False).tolist()]
    segments: list[tuple[int, int]] = []
    start: int | None = None
    false_run = 0
    for idx, flag in enumerate(flags):
        if flag:
            if start is None:
                start = idx
            false_run = 0
            continue
        if start is None:
            continue
        false_run += 1
        if false_run > int(max_false_gap):
            end = idx - false_run
            if end >= start:
                segments.append((start, end))
            start = None
            false_run = 0
    if start is not None:
        segments.append((start, len(flags) - 1))
    return segments


def select_segment_representative_anchor(
    *,
    segment_start: int,
    segment_end: int,
    target_fraction: float,
    avoid_last_n_bars: int,
    max_segment_position_fraction: float,
) -> int:
    indices = list(range(int(segment_start), int(segment_end) + 1))
    if not indices:
        return int(segment_start)
    length = len(indices)
    target_idx = int(round((length - 1) * float(target_fraction)))

    eligible = []
    for pos, idx in enumerate(indices):
        frac = float(pos / (length - 1)) if length > 1 else 0.0
        is_late_tail = pos >= max(0, length - int(avoid_last_n_bars))
        if frac > float(max_segment_position_fraction) or is_late_tail:
            continue
        eligible.append((idx, pos))

    pool = eligible if eligible else [(idx, pos) for pos, idx in enumerate(indices)]
    pool.sort(key=lambda item: (abs(item[1] - target_idx), item[1]))
    return int(pool[0][0])


def _trend_conf(row: pd.Series, direction: str) -> float:
    s3 = float(row.get("close_pct_change_3", 0.0) or 0.0)
    s5 = float(row.get("close_pct_change_5", 0.0) or 0.0)
    s8 = float(row.get("close_pct_change_8", 0.0) or 0.0)
    if direction == "down":
        return min(1.0, 0.6 + max(0.0, -(s3 + s5 + s8)) * 20)
    return min(1.0, 0.6 + max(0.0, s3 + s5 + s8) * 20)


def _emit_trend_segment_candidates(
    rows: list[dict[str, Any]],
    work: pd.DataFrame,
    *,
    direction: str,
    min_confidence: float,
    cfg: dict[str, Any],
) -> None:
    if direction == "down":
        mask = (
            (work["close_pct_change_3"] < 0)
            & (work["close_pct_change_5"] < 0)
            & (work["close_pct_change_8"] < 0)
            & (work["rolling_range_position_8"] < 0.25)
        )
        candidate_type = "short_trend_down_candidate"
        base_reasons = ["negative_short_slopes", "low_range_position"]
        segment_direction = "down"
    else:
        mask = (
            (work["close_pct_change_3"] > 0)
            & (work["close_pct_change_5"] > 0)
            & (work["close_pct_change_8"] > 0)
            & (work["rolling_range_position_8"] > 0.75)
        )
        candidate_type = "short_trend_up_candidate"
        base_reasons = ["positive_short_slopes", "high_range_position"]
        segment_direction = "up"

    segments = detect_trend_segments_from_mask(mask)
    for seg_no, (start, end) in enumerate(segments, start=1):
        seg = work.iloc[start : end + 1].copy()
        if seg.empty:
            continue

        segment_id = f"{segment_direction}_seg_{seg_no:04d}"
        raw_trigger_count = int(len(seg))
        suppressed_count = max(0, raw_trigger_count - int(cfg["max_candidates_per_segment"]))

        anchor_idx = select_segment_representative_anchor(
            segment_start=start,
            segment_end=end,
            target_fraction=float(cfg["target_fraction"]),
            avoid_last_n_bars=int(cfg["avoid_last_n_bars"]),
            max_segment_position_fraction=float(cfg["max_segment_position_fraction"]),
        )
        row = work.iloc[anchor_idx]
        if pd.isna(row.get("timestamp")):
            continue

        seg_pos = anchor_idx - start
        seg_len = len(seg)
        seg_frac = float(seg_pos / (seg_len - 1)) if seg_len > 1 else 0.0
        is_late_tail = seg_pos >= max(0, seg_len - int(cfg["avoid_last_n_bars"]))
        late_segment_anchor = bool(seg_frac > float(cfg["max_segment_position_fraction"]) or is_late_tail)

        close_anchor = float(row["close"])
        atr8 = float(row.get("atr_like_range_mean_8", 0.0) or 0.0)
        rebound_threshold = atr8 * float(cfg["rebound_threshold_atr_multiple"])
        if rebound_threshold <= 0:
            rebound_threshold = max(float(row.get("range", 0.0) or 0.0) * 0.5, 1e-9)

        fwd = work.iloc[anchor_idx + 1 : anchor_idx + 1 + int(cfg["rebound_lookahead_bars"])]
        rebound_after_anchor = False
        weak_follow_through = False
        if not fwd.empty:
            if direction == "down":
                rebound_move = float(fwd["high"].max()) - close_anchor
                continuation_move = close_anchor - float(fwd["low"].min())
            else:
                rebound_move = close_anchor - float(fwd["low"].min())
                continuation_move = float(fwd["high"].max()) - close_anchor
            rebound_after_anchor = rebound_move >= rebound_threshold
            weak_follow_through = continuation_move < (rebound_threshold * 0.2)

        segment_low_idx = int(seg["low"].idxmin())
        segment_high_idx = int(seg["high"].idxmax())
        near_segment_low = direction == "down" and anchor_idx >= max(start, segment_low_idx - 1)
        near_segment_high = direction == "up" and anchor_idx >= max(start, segment_high_idx - 1)
        excluded_late_reversal_anchor = bool(
            late_segment_anchor or rebound_after_anchor or weak_follow_through or near_segment_low or near_segment_high
        )
        preferred_review_candidate = not excluded_late_reversal_anchor
        if not bool(cfg["exclude_late_rebound_anchor"]):
            preferred_review_candidate = True

        candidate_reasons = list(base_reasons)
        selection_reasons = ["segment_representative", "segment_midpoint_anchor", "trend_continuation_context", "sufficient_pre_context"]
        exclusion_reasons: list[str] = []
        if suppressed_count > 0:
            selection_reasons.append("same_segment_duplicate_suppressed")
        if late_segment_anchor:
            exclusion_reasons.append("late_segment_anchor")
        if near_segment_low:
            exclusion_reasons.append("near_segment_low")
        if near_segment_high:
            exclusion_reasons.append("near_segment_high")
        if rebound_after_anchor:
            exclusion_reasons.append("rebound_after_anchor")
        if weak_follow_through:
            exclusion_reasons.append("weak_follow_through_after_anchor")
        if excluded_late_reversal_anchor:
            exclusion_reasons.append("excluded_late_reversal_anchor")

        all_reasons = list(dict.fromkeys(candidate_reasons + selection_reasons + exclusion_reasons))
        conf = _trend_conf(row, direction)
        if conf < min_confidence:
            continue

        seg_start_close = float(seg.iloc[0]["close"])
        seg_end_close = float(seg.iloc[-1]["close"])
        segment_price_change = seg_end_close - seg_start_close
        segment_return = (seg_end_close / seg_start_close - 1.0) if seg_start_close != 0 else 0.0

        item = {
            "timestamp": row["timestamp"].isoformat(),
            "source_row_index": int(row.get("source_row_index", anchor_idx)),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": close_anchor,
            "candidate_type": candidate_type,
            "confidence_score": round(float(max(0.0, min(1.0, conf))), 4),
            "reason_codes": "|".join(all_reasons),
            "candidate_reason_codes": "|".join(candidate_reasons),
            "selection_reason_codes": "|".join(selection_reasons),
            "exclusion_reason_codes": "|".join(exclusion_reasons),
            "segment_reason_codes": "|".join(selection_reasons),
            "review_sampling_reason_codes": "|".join(exclusion_reasons),
            "primary_selection_reason": "segment_midpoint_anchor",
            "body_ratio": round(float(row.get("body_ratio", 0.0) or 0.0), 6),
            "upper_wick_ratio": round(float((row.get("upper_wick", 0.0) or 0.0) / max(float(row.get("range", 0.0) or 1e-9), 1e-9)), 6),
            "lower_wick_ratio": round(float((row.get("lower_wick", 0.0) or 0.0) / max(float(row.get("range", 0.0) or 1e-9), 1e-9)), 6),
            "range": round(float(row.get("range", 0.0) or 0.0), 6),
            "slope_3": round(float(row.get("close_pct_change_3", 0.0) or 0.0), 8),
            "slope_5": round(float(row.get("close_pct_change_5", 0.0) or 0.0), 8),
            "slope_8": round(float(row.get("close_pct_change_8", 0.0) or 0.0), 8),
            "slope_13": round(float(row.get("close_pct_change_13", 0.0) or 0.0), 8),
            "slope_21": round(float(row.get("close_pct_change_21", 0.0) or 0.0), 8),
            "efficiency_ratio_21": round(float(row.get("efficiency_ratio_21", 0.0) or 0.0), 6),
            "rolling_range_position_8": round(float(row.get("rolling_range_position_8", 0.5) or 0.5), 6),
            "compression_ratio": round(float((float(row.get("atr_like_range_mean_8", 0.0) or 0.0) / float(row.get("atr_like_range_mean_34", 1e-9) or 1e-9))), 6),
            "expansion_ratio": round(float((float(row.get("range", 0.0) or 0.0) / max(float(row.get("atr_like_range_mean_8", 0.0) or 1e-9), 1e-9))), 6),
            "lookback_bars_used": "3|5|8",
            "review_priority": _priority(conf),
            "segment_id": segment_id,
            "segment_direction": segment_direction,
            "segment_start_timestamp": seg.iloc[0]["timestamp"].isoformat(),
            "segment_end_timestamp": seg.iloc[-1]["timestamp"].isoformat(),
            "segment_length_bars": int(seg_len),
            "segment_start_index": int(start),
            "segment_end_index": int(end),
            "segment_price_change": round(float(segment_price_change), 8),
            "segment_return": round(float(segment_return), 8),
            "segment_low_index": int(segment_low_idx),
            "segment_high_index": int(segment_high_idx),
            "segment_position_fraction": round(float(seg_frac), 6),
            "segment_anchor_rank": 1,
            "segment_raw_trigger_count": int(raw_trigger_count),
            "segment_duplicate_suppressed_count": int(max(0, suppressed_count)),
            "representative_anchor": True,
            "late_segment_anchor": bool(late_segment_anchor),
            "rebound_after_anchor": bool(rebound_after_anchor),
            "weak_follow_through_after_anchor": bool(weak_follow_through),
            "excluded_late_reversal_anchor": bool(excluded_late_reversal_anchor),
            "preferred_review_candidate": bool(preferred_review_candidate),
        }
        item.update(CAUSAL_PAST_ONLY)
        item["review_filter_uses_future_bars"] = True
        item["review_filter_future_bars_used"] = int(cfg["rebound_lookahead_bars"])
        item["future_usage_role"] = "review_sampling_filter"
        item["review_filter_window"] = f"next_{int(cfg['rebound_lookahead_bars'])}_bars"
        _add_candidate(rows, item)


def detect_eurusd_pattern_candidates(
    clean_df: pd.DataFrame,
    *,
    min_confidence: float = 0.6,
) -> pd.DataFrame:
    work = compute_eurusd_pattern_features(clean_df, horizons=HORIZONS)
    if "timestamp" in work.columns:
        work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", utc=True)

    rows: list[dict[str, Any]] = []

    _emit_trend_segment_candidates(rows, work, direction="up", min_confidence=min_confidence, cfg=TREND_SEGMENT_DEFAULTS)
    _emit_trend_segment_candidates(rows, work, direction="down", min_confidence=min_confidence, cfg=TREND_SEGMENT_DEFAULTS)

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

        s13 = float(row.get("close_pct_change_13", 0.0) or 0.0)
        s21 = float(row.get("close_pct_change_21", 0.0) or 0.0)
        eff21 = float(row.get("efficiency_ratio_21", 0.0) or 0.0)

        ts = row.get("timestamp")
        ts_text = ts.isoformat() if pd.notna(ts) else None
        src_idx = int(row.get("source_row_index", i))

        def emit(candidate_type: str, conf: float, reasons: list[str], lookback: list[int], primary_reason: str) -> None:
            if conf < min_confidence:
                return
            item = {
                "timestamp": ts_text,
                "source_row_index": src_idx,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "candidate_type": candidate_type,
                "confidence_score": round(float(max(0.0, min(1.0, conf))), 4),
                "reason_codes": "|".join(reasons),
                "candidate_reason_codes": "|".join(reasons),
                "selection_reason_codes": "|".join(reasons),
                "exclusion_reason_codes": "",
                "segment_reason_codes": "",
                "review_sampling_reason_codes": "",
                "primary_selection_reason": primary_reason,
                "body_ratio": round(body_ratio, 6),
                "upper_wick_ratio": round(upper_ratio, 6),
                "lower_wick_ratio": round(lower_ratio, 6),
                "range": round(r, 6),
                "slope_3": round(float(row.get("close_pct_change_3", 0.0) or 0.0), 8),
                "slope_5": round(float(row.get("close_pct_change_5", 0.0) or 0.0), 8),
                "slope_8": round(float(row.get("close_pct_change_8", 0.0) or 0.0), 8),
                "slope_13": round(s13, 8),
                "slope_21": round(s21, 8),
                "efficiency_ratio_21": round(eff21, 6),
                "rolling_range_position_8": round(float(row.get("rolling_range_position_8", 0.5) or 0.5), 6),
                "compression_ratio": round(compression_ratio, 6),
                "expansion_ratio": round(expansion_ratio, 6),
                "lookback_bars_used": "|".join(str(x) for x in lookback),
                "review_priority": _priority(conf),
                "representative_anchor": False,
                "late_segment_anchor": False,
                "rebound_after_anchor": False,
                "weak_follow_through_after_anchor": False,
                "excluded_late_reversal_anchor": False,
                "preferred_review_candidate": True,
            }
            item.update(CAUSAL_PAST_ONLY)
            _add_candidate(rows, item)

        if compression_ratio > 0 and compression_ratio < 0.75:
            emit("compression_candidate", 1.0 - min(1.0, compression_ratio), ["low_short_vs_long_range"], [8, 34], "low_short_vs_long_range")

        if expansion_ratio > 1.6:
            emit("expansion_candidate", min(1.0, expansion_ratio / 3.0), ["current_range_vs_recent_atr"], [8], "current_range_vs_recent_atr")

        if s13 > 0 and s21 > 0 and eff21 >= 0.35:
            emit("mid_trend_up_candidate", min(1.0, 0.55 + eff21), ["positive_mid_slopes", "efficiency_above_threshold"], [13, 21], "efficiency_above_threshold")

        if s13 < 0 and s21 < 0 and eff21 >= 0.35:
            emit("mid_trend_down_candidate", min(1.0, 0.55 + eff21), ["negative_mid_slopes", "efficiency_above_threshold"], [13, 21], "efficiency_above_threshold")

        midpoint = (high + low) / 2.0
        if upper_ratio >= 0.45 and (close < midpoint or close < open_):
            emit("upper_wick_rejection_candidate", min(1.0, 0.55 + upper_ratio), ["upper_wick_large", "close_rejected_lower"], [1], "upper_wick_large")

        if lower_ratio >= 0.45 and (close > midpoint or close > open_):
            emit("lower_wick_rejection_candidate", min(1.0, 0.55 + lower_ratio), ["lower_wick_large", "close_rejected_upper"], [1], "lower_wick_large")

        if body_ratio <= 0.12 and r > 0:
            emit("doji_indecision_candidate", min(1.0, 0.65 + (0.12 - body_ratio)), ["small_body_ratio"], [1], "small_body_ratio")

        if i >= 9:
            prev8 = work.iloc[max(0, i - 8):i]
            local_high = float(prev8["high"].max()) if not prev8.empty else high
            local_low = float(prev8["low"].min()) if not prev8.empty else low
            if high > local_high and close < local_high:
                conf = min(1.0, 0.6 + ((high - close) / r))
                emit("possible_false_breakout_candidate", conf, ["break_above_local_high_then_close_inside"], [8], "break_above_local_high_then_close_inside")
            elif low < local_low and close > local_low:
                conf = min(1.0, 0.6 + ((close - low) / r))
                emit("possible_false_breakout_candidate", conf, ["break_below_local_low_then_close_inside"], [8], "break_below_local_low_then_close_inside")

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=[
            "timestamp", "source_row_index", "open", "high", "low", "close", "candidate_type", "confidence_score",
            "reason_codes", "candidate_reason_codes", "selection_reason_codes", "exclusion_reason_codes", "segment_reason_codes",
            "review_sampling_reason_codes", "primary_selection_reason", "body_ratio", "upper_wick_ratio", "lower_wick_ratio", "range",
            "slope_3", "slope_5", "slope_8", "slope_13", "slope_21", "efficiency_ratio_21", "rolling_range_position_8",
            "compression_ratio", "expansion_ratio", "lookback_bars_used", "review_priority", "segment_id", "segment_direction",
            "segment_start_timestamp", "segment_end_timestamp", "segment_length_bars", "segment_start_index", "segment_end_index",
            "segment_price_change", "segment_return", "segment_low_index", "segment_high_index", "segment_position_fraction",
            "segment_anchor_rank", "segment_raw_trigger_count", "segment_duplicate_suppressed_count", "representative_anchor",
            "late_segment_anchor", "rebound_after_anchor", "weak_follow_through_after_anchor", "excluded_late_reversal_anchor",
            "preferred_review_candidate", "causal_candidate", "candidate_logic_uses_future_bars", "candidate_logic_future_bars_used",
            "review_filter_uses_future_bars", "review_filter_future_bars_used", "label_uses_future_bars", "future_usage_role",
            "not_for_live_signal", "candidate_logic_window", "review_filter_window", "label_window",
        ])
    return out.sort_values(["timestamp", "candidate_type"]).reset_index(drop=True)
