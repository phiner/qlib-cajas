"""Frozen EURUSD five-layer review vocabulary and schema helpers."""

from __future__ import annotations

from typing import Any

REVIEW_SCHEMA_VERSION = "eurusd_15m_pattern_review_v3"
COMPATIBLE_SCHEMA_VERSIONS = [
    "eurusd_15m_pattern_review_v1",
    "eurusd_15m_pattern_review_v2",
    REVIEW_SCHEMA_VERSION,
]

FIELD_HUMAN_PATTERN_LABEL = "human_pattern_label"
FIELD_MARKET_CONTEXT = "market_context"
FIELD_DIRECTION_CONTEXT = "direction_context"
FIELD_STRUCTURE_QUALITY = "structure_quality"
FIELD_FOLLOW_THROUGH_QUALITY = "follow_through_quality"
FIELD_REVIEW_CONFIDENCE_SCORE = "review_confidence"
FIELD_REVIEW_NOTES = "review_notes"
FIELD_REVIEW_STATUS = "review_status"

FIELD_STRUCTURE_LOCATION = "structure_location"
FIELD_LOCAL_BEHAVIOR = "local_behavior"
FIELD_CONFIRMATION_RESULT = "confirmation_result"
FIELD_REVIEW_OUTCOME = "review_outcome"
FIELD_PATTERN_QUALITY = "pattern_quality"
FIELD_FALSE_POSITIVE_REASON = "false_positive_reason"
FIELD_REVIEW_CONFIDENCE = "review_confidence_level"
FIELD_PRIMARY_CANDIDATE_FAMILY = "primary_candidate_family"
FIELD_SECONDARY_CANDIDATE_FAMILY = "secondary_candidate_family"

LEGACY_ENUM_FIELDS = [FIELD_HUMAN_PATTERN_LABEL, FIELD_MARKET_CONTEXT, FIELD_DIRECTION_CONTEXT, FIELD_REVIEW_STATUS]
FIVE_LAYER_ENUM_FIELDS = [
    FIELD_MARKET_CONTEXT,
    FIELD_STRUCTURE_LOCATION,
    FIELD_LOCAL_BEHAVIOR,
    FIELD_CONFIRMATION_RESULT,
    FIELD_REVIEW_OUTCOME,
]

ALLOWED_VALUES = {
    FIELD_HUMAN_PATTERN_LABEL: ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
    FIELD_MARKET_CONTEXT: [
        "uptrend",
        "downtrend",
        "range",
        "compression",
        "expansion",
        "transition",
        "unclear",
        "not_reviewed",
    ],
    FIELD_DIRECTION_CONTEXT: [
        "up",
        "down",
        "neutral",
        "mixed",
        "up_pullback",
        "down_pullback",
        "reversal_up",
        "reversal_down",
        "unclear",
    ],
    FIELD_REVIEW_STATUS: ["pending", "reviewed", "needs_recheck", "skip"],
    FIELD_STRUCTURE_LOCATION: [
        "prior_high",
        "prior_low",
        "range_high",
        "range_low",
        "breakout_area",
        "pullback_area",
        "middle_of_range",
        "trend_continuation_area",
        "trend_exhaustion_area",
        "unclear",
        "not_reviewed",
    ],
    FIELD_LOCAL_BEHAVIOR: [
        "lower_wick_rejection",
        "upper_wick_rejection",
        "doji",
        "strong_body_breakout",
        "compression_cluster",
        "expansion_bar",
        "trend_push",
        "reclaim",
        "unclear",
        "not_reviewed",
    ],
    FIELD_CONFIRMATION_RESULT: ["confirmed", "failed", "no_follow_through", "unclear", "not_reviewed"],
    FIELD_REVIEW_OUTCOME: ["valid_pattern", "weak_pattern", "false_positive", "unclear", "not_reviewed"],
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
        "other",
        "not_reviewed",
    ],
    FIELD_REVIEW_CONFIDENCE: ["high", "medium", "low", "unclear", "not_reviewed"],
    FIELD_PRIMARY_CANDIDATE_FAMILY: [
        "market_context",
        "volatility_state",
        "candle_observation",
        "structure_event",
        "mixed_overlap",
        "unclear",
        "not_reviewed",
    ],
    FIELD_SECONDARY_CANDIDATE_FAMILY: [
        "market_context",
        "volatility_state",
        "candle_observation",
        "structure_event",
        "mixed_overlap",
        "unclear",
        "not_reviewed",
    ],
}

LEGACY_ALLOWED_VALUES = {
    FIELD_DIRECTION_CONTEXT: ["sideways"],
    FIELD_MARKET_CONTEXT: [
        "trend",
        "pullback",
        "breakout",
        "reversal_attempt",
        "high_volatility",
        "low_volatility",
    ],
}

NUMERIC_RANGES = {
    FIELD_STRUCTURE_QUALITY: {"min": 1, "max": 5},
    FIELD_FOLLOW_THROUGH_QUALITY: {"min": 1, "max": 5},
    FIELD_REVIEW_CONFIDENCE_SCORE: {"min": 1, "max": 5},
}

DEFAULT_REVIEW_VALUES = {
    FIELD_HUMAN_PATTERN_LABEL: "unclear",
    FIELD_MARKET_CONTEXT: "unclear",
    FIELD_DIRECTION_CONTEXT: "unclear",
    FIELD_STRUCTURE_QUALITY: 3,
    FIELD_FOLLOW_THROUGH_QUALITY: 3,
    FIELD_REVIEW_CONFIDENCE_SCORE: 3,
    FIELD_REVIEW_NOTES: "",
    FIELD_REVIEW_STATUS: "pending",
    FIELD_STRUCTURE_LOCATION: "not_reviewed",
    FIELD_LOCAL_BEHAVIOR: "not_reviewed",
    FIELD_CONFIRMATION_RESULT: "not_reviewed",
    FIELD_REVIEW_OUTCOME: "not_reviewed",
    FIELD_PATTERN_QUALITY: "not_reviewed",
    FIELD_FALSE_POSITIVE_REASON: "not_reviewed",
    FIELD_REVIEW_CONFIDENCE: "not_reviewed",
    FIELD_PRIMARY_CANDIDATE_FAMILY: "not_reviewed",
    FIELD_SECONDARY_CANDIDATE_FAMILY: "not_reviewed",
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
