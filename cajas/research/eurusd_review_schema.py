"""Frozen EURUSD five-layer review vocabulary and schema helpers."""

from __future__ import annotations

from typing import Any

REVIEW_SCHEMA_VERSION = "eurusd_15m_pattern_review_v3"
COMPATIBLE_SCHEMA_VERSIONS = [
    "eurusd_15m_pattern_review_v1",
    "eurusd_15m_pattern_review_v2",
    REVIEW_SCHEMA_VERSION,
]

FIELD_MARKET_CONTEXT = "market_context"
FIELD_REVIEW_NOTES = "review_notes"
FIELD_HUMAN_RATIONALE_ZH = "human_rationale_zh"
FIELD_HUMAN_COUNTEREXAMPLE_ZH = "human_counterexample_zh"
FIELD_HUMAN_UNCERTAINTY_REASON_ZH = "human_uncertainty_reason_zh"
FIELD_HUMAN_CONTEXT_NOTES_ZH = "human_context_notes_zh"

FIELD_STRUCTURE_LOCATION = "structure_location"
FIELD_LOCAL_BEHAVIOR = "local_behavior"
FIELD_CONFIRMATION_RESULT = "confirmation_result"
FIELD_REVIEW_OUTCOME = "review_outcome"
FIELD_PATTERN_QUALITY = "pattern_quality"
FIELD_FALSE_POSITIVE_REASON = "false_positive_reason"
FIELD_REVIEW_CONFIDENCE = "review_confidence"
FIELD_PRIMARY_CANDIDATE_FAMILY = "primary_candidate_family"
FIELD_SECONDARY_CANDIDATE_FAMILY = "secondary_candidate_family"
FIELD_RECENT_MOVE_CONTEXT = "recent_move_context"
FIELD_TREND_DIRECTION = "trend_direction"
FIELD_TREND_STAGE = "trend_stage"
FIELD_VOLATILITY_STATE = "volatility_state"
FIELD_LEVEL_QUALITY = "level_quality"
FIELD_SESSION_CONTEXT = "session_context"

FIVE_LAYER_ENUM_FIELDS = [
    FIELD_MARKET_CONTEXT,
    FIELD_STRUCTURE_LOCATION,
    FIELD_LOCAL_BEHAVIOR,
    FIELD_CONFIRMATION_RESULT,
    FIELD_REVIEW_OUTCOME,
]

CANONICAL_REVIEW_FIELDS = [
    FIELD_MARKET_CONTEXT,
    FIELD_TREND_DIRECTION,
    FIELD_TREND_STAGE,
    FIELD_VOLATILITY_STATE,
    FIELD_RECENT_MOVE_CONTEXT,
    FIELD_SESSION_CONTEXT,
    FIELD_STRUCTURE_LOCATION,
    FIELD_LEVEL_QUALITY,
    FIELD_LOCAL_BEHAVIOR,
    FIELD_CONFIRMATION_RESULT,
    FIELD_REVIEW_OUTCOME,
    FIELD_PATTERN_QUALITY,
    FIELD_FALSE_POSITIVE_REASON,
    FIELD_REVIEW_CONFIDENCE,
    FIELD_PRIMARY_CANDIDATE_FAMILY,
    FIELD_SECONDARY_CANDIDATE_FAMILY,
    FIELD_REVIEW_NOTES,
    FIELD_HUMAN_RATIONALE_ZH,
    FIELD_HUMAN_COUNTEREXAMPLE_ZH,
    FIELD_HUMAN_UNCERTAINTY_REASON_ZH,
    FIELD_HUMAN_CONTEXT_NOTES_ZH,
]

ALLOWED_VALUES = {
    FIELD_MARKET_CONTEXT: [
        "uptrend",
        "downtrend",
        "range",
        "compression",
        "expansion",
        "transition",
        "choppy",
        "unclear",
        "not_reviewed",
    ],
    FIELD_STRUCTURE_LOCATION: [
        "prior_high",
        "prior_low",
        "range_high",
        "range_low",
        "range_middle",
        "breakdown_area",
        "breakout_area",
        "pullback_area",
        "retest_area",
        "support_area",
        "resistance_area",
        "liquidity_sweep_area",
        "middle_of_range",
        "trend_continuation_area",
        "trend_exhaustion_area",
        "middle_of_nowhere",
        "unclear",
        "not_reviewed",
    ],
    FIELD_LOCAL_BEHAVIOR: [
        "lower_wick_rejection",
        "upper_wick_rejection",
        "doji",
        "small_body_indecision",
        "strong_bull_body",
        "strong_bear_body",
        "strong_body_breakout",
        "failed_breakout_reclaim",
        "compression_cluster",
        "expansion_bar",
        "trend_push",
        "reclaim",
        "unclear",
        "not_reviewed",
    ],
    FIELD_CONFIRMATION_RESULT: [
        "confirmed",
        "failed",
        "no_follow_through",
        "partial_follow_through",
        "delayed_follow_through",
        "unclear",
        "not_reviewed",
    ],
    FIELD_REVIEW_OUTCOME: [
        "valid_pattern",
        "weak_pattern",
        "false_positive",
        "not_enough_context",
        "unclear",
        "not_reviewed",
    ],
    FIELD_PATTERN_QUALITY: ["strong", "medium", "weak", "invalid", "unclear", "not_reviewed"],
    FIELD_FALSE_POSITIVE_REASON: [
        "none",
        "no_structure_level",
        "low_volatility_noise",
        "trend_middle_noise",
        "overlapping_labels",
        "insufficient_context",
        "bad_candidate_anchor",
        "level_too_local",
        "session_noise",
        "spread_or_data_noise",
        "news_spike_like",
        "middle_of_nowhere",
        "weak_follow_through",
        "other",
        "not_reviewed",
    ],
    FIELD_REVIEW_CONFIDENCE: ["high", "medium", "low", "unclear", "not_reviewed"],
    FIELD_PRIMARY_CANDIDATE_FAMILY: [
        "market_context",
        "volatility_state",
        "candle_observation",
        "structure_event",
        "confirmation_event",
        "mixed_overlap",
        "unclear",
        "not_reviewed",
    ],
    FIELD_SECONDARY_CANDIDATE_FAMILY: [
        "market_context",
        "volatility_state",
        "candle_observation",
        "structure_event",
        "confirmation_event",
        "mixed_overlap",
        "none",
        "unclear",
        "not_reviewed",
    ],
    FIELD_TREND_DIRECTION: ["up", "down", "sideways", "mixed", "unclear", "not_reviewed"],
    FIELD_TREND_STAGE: [
        "early_trend",
        "mid_trend",
        "late_trend",
        "trend_exhaustion",
        "pullback",
        "reversal_attempt",
        "consolidation_after_impulse",
        "range_transition",
        "unclear",
        "not_reviewed",
    ],
    FIELD_VOLATILITY_STATE: [
        "low_volatility",
        "normal_volatility",
        "high_volatility",
        "compression",
        "expansion",
        "post_expansion",
        "unclear",
        "not_reviewed",
    ],
    FIELD_RECENT_MOVE_CONTEXT: [
        "sharp_rise",
        "sharp_drop",
        "rise_then_pullback",
        "drop_then_rebound",
        "spike_up_reversal",
        "spike_down_reversal",
        "sharp_rise_then_consolidation",
        "sharp_drop_then_consolidation",
        "range_breakout_attempt",
        "range_breakdown_attempt",
        "sweep_high_then_reclaim",
        "sweep_low_then_reclaim",
        "unclear",
        "not_reviewed",
    ],
    FIELD_LEVEL_QUALITY: ["strong", "medium", "weak", "none", "unclear", "not_reviewed"],
    FIELD_SESSION_CONTEXT: ["asia", "london", "new_york", "overlap", "rollover", "normal", "unclear", "not_reviewed"],
}

LEGACY_ALLOWED_VALUES: dict[str, list[str]] = {}

NUMERIC_RANGES: dict[str, dict[str, float]] = {}

DEFAULT_REVIEW_VALUES = {
    FIELD_MARKET_CONTEXT: "unclear",
    FIELD_REVIEW_NOTES: "",
    FIELD_STRUCTURE_LOCATION: "not_reviewed",
    FIELD_LOCAL_BEHAVIOR: "not_reviewed",
    FIELD_CONFIRMATION_RESULT: "not_reviewed",
    FIELD_REVIEW_OUTCOME: "not_reviewed",
    FIELD_PATTERN_QUALITY: "not_reviewed",
    FIELD_FALSE_POSITIVE_REASON: "not_reviewed",
    FIELD_REVIEW_CONFIDENCE: "not_reviewed",
    FIELD_PRIMARY_CANDIDATE_FAMILY: "not_reviewed",
    FIELD_SECONDARY_CANDIDATE_FAMILY: "not_reviewed",
    FIELD_RECENT_MOVE_CONTEXT: "not_reviewed",
    FIELD_TREND_DIRECTION: "not_reviewed",
    FIELD_TREND_STAGE: "not_reviewed",
    FIELD_VOLATILITY_STATE: "not_reviewed",
    FIELD_LEVEL_QUALITY: "not_reviewed",
    FIELD_SESSION_CONTEXT: "not_reviewed",
    FIELD_HUMAN_RATIONALE_ZH: "",
    FIELD_HUMAN_COUNTEREXAMPLE_ZH: "",
    FIELD_HUMAN_UNCERTAINTY_REASON_ZH: "",
    FIELD_HUMAN_CONTEXT_NOTES_ZH: "",
}


def default_review_values() -> dict[str, Any]:
    return dict(DEFAULT_REVIEW_VALUES)


def validate_review_row(row: dict[str, Any], *, allow_legacy: bool = True) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field, allowed in ALLOWED_VALUES.items():
        if field not in row:
            continue
        value = row[field]
        if value is None:
            continue
        text = str(value)
        if text in allowed:
            continue
        legacy = LEGACY_ALLOWED_VALUES.get(field, []) if allow_legacy else []
        if text in legacy:
            warnings.append(f"legacy_value:{field}:{text}")
            continue
        errors.append(f"invalid_value:{field}:{text}")

    for field, bounds in NUMERIC_RANGES.items():
        if field not in row:
            continue
        value = row[field]
        if value is None:
            continue
        try:
            num = float(value)
        except (TypeError, ValueError):
            errors.append(f"invalid_numeric:{field}:{value}")
            continue
        if num < float(bounds["min"]) or num > float(bounds["max"]):
            errors.append(f"out_of_range:{field}:{num}")

    return {"errors": errors, "warnings": warnings}
