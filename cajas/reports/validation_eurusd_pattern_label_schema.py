"""EURUSD pattern review label schema report."""

from __future__ import annotations

from typing import Any


def build_validation_eurusd_pattern_label_schema() -> dict[str, Any]:
    return {
        "schema_version": "eurusd_15m_pattern_review_v1",
        "status": "ready",
        "required_fields": [
            "sample_id",
            "timestamp",
            "candidate_type",
            "human_pattern_label",
            "market_context",
            "direction_context",
            "structure_quality",
            "follow_through_quality",
            "review_confidence",
            "review_notes",
        ],
        "allowed_values": {
            "human_pattern_label": ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
            "market_context": ["trend", "range", "transition", "high_volatility", "low_volatility", "unclear"],
            "direction_context": ["up", "down", "sideways", "mixed", "unclear"],
            "review_status": ["pending", "reviewed"],
        },
        "numeric_ranges": {
            "structure_quality": {"min": 1, "max": 5},
            "follow_through_quality": {"min": 1, "max": 5},
            "review_confidence": {"min": 1, "max": 5},
        },
        "defaults": {
            "human_pattern_label": "unclear",
            "market_context": "unclear",
            "direction_context": "unclear",
            "structure_quality": 3,
            "follow_through_quality": 3,
            "review_confidence": 3,
            "review_notes": "",
            "review_status": "pending",
        },
        "scope_boundary": {
            "manual_review_labels_only": True,
            "trading_signal": False,
            "order_generation": False,
        },
        "recommendation": "use_schema_for_review_template",
    }


def render_validation_eurusd_pattern_label_schema_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation EURUSD Pattern Label Schema",
            "",
            f"- status: `{payload.get('status')}`",
            f"- schema_version: `{payload.get('schema_version')}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "",
            "## Policy",
            "",
            "- Manual review labels only.",
            "- No trading signals or orders.",
            "",
        ]
    )
