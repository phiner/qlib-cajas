"""EURUSD pattern review label schema report."""

from __future__ import annotations

from typing import Any

from cajas.research.eurusd_review_schema import (
    ALLOWED_VALUES,
    COMPATIBLE_SCHEMA_VERSIONS,
    DEFAULT_REVIEW_VALUES,
    LEGACY_ALLOWED_VALUES,
    NUMERIC_RANGES,
    REVIEW_SCHEMA_VERSION,
)


def build_validation_eurusd_pattern_label_schema() -> dict[str, Any]:
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "compatible_schema_versions": COMPATIBLE_SCHEMA_VERSIONS,
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
        "allowed_values": ALLOWED_VALUES,
        "legacy_allowed_values": LEGACY_ALLOWED_VALUES,
        "numeric_ranges": NUMERIC_RANGES,
        "defaults": DEFAULT_REVIEW_VALUES,
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
