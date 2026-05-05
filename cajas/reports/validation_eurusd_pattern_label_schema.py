"""EURUSD pattern review label schema report."""

from __future__ import annotations

from typing import Any

from cajas.research.eurusd_review_schema import (
    ALLOWED_VALUES,
    COMPATIBLE_SCHEMA_VERSIONS,
    DEFAULT_REVIEW_VALUES,
    FIVE_LAYER_ENUM_FIELDS,
    LEGACY_ALLOWED_VALUES,
    NUMERIC_RANGES,
    REVIEW_SCHEMA_VERSION,
)

FIVE_LAYER_FIELD_DESCRIPTIONS_CN = {
    "market_context": "背景层：先判断趋势/震荡/波动状态，提供环境背景。",
    "structure_location": "结构位置层：标注样本位于关键高低点、区间边界或突破区域。",
    "local_behavior": "局部行为层：描述蜡烛局部动作，如 wick/doji/reclaim。",
    "confirmation_result": "确认/失败层：记录是否出现确认、失败或无跟随。",
    "review_outcome": "人审结论层：给出最终人工结论，不等同于 candidate_type。",
}

QUALITY_CONTROL_FIELD_DESCRIPTIONS_CN = {
    "pattern_quality": "形态质量评估：强/中/弱/无效。",
    "false_positive_reason": "误报原因：无结构位、噪声或上下文不足等。",
    "review_confidence_level": "结论置信度等级：high/medium/low。",
    "primary_candidate_family": "主候选家族：主要归因来源。",
    "secondary_candidate_family": "次候选家族：次要归因来源或重叠来源。",
}


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
        "five_layer_schema": {
            "ordered_fields": list(FIVE_LAYER_ENUM_FIELDS),
            "field_descriptions_cn": FIVE_LAYER_FIELD_DESCRIPTIONS_CN,
            "review_order_cn": "先看背景，再看位置，再看局部行为，再看确认/失败，最后给人审结论。",
        },
        "quality_control_fields": {
            "fields": list(QUALITY_CONTROL_FIELD_DESCRIPTIONS_CN.keys()),
            "field_descriptions_cn": QUALITY_CONTROL_FIELD_DESCRIPTIONS_CN,
        },
        "candidate_type_policy": {
            "entry_tag_only": True,
            "final_pattern_truth": False,
            "note_cn": "candidate_type 是系统把样本送进来的原因，不是最终形态名称。",
        },
        "candidate_family_guidance": {
            "market_context_or_trend": "Context/background only, not the final pattern label.",
            "volatility_state": "Compression/expansion describe state, not a complete setup.",
            "candle_observation": "Wick/doji need structure-location validation.",
            "structure_event": "False-breakout candidates require level, reclaim, and follow-through checks.",
            "mixed_overlap": "Record ambiguity and use secondary family when needed.",
        },
        "scope_boundary": {
            "manual_review_labels_only": True,
            "trading_signal": False,
            "order_generation": False,
        },
        "recommendation": "use_schema_for_review_template",
    }


def render_validation_eurusd_pattern_label_schema_markdown(payload: dict[str, Any]) -> str:
    five_layer = payload.get("five_layer_schema", {})
    allowed = payload.get("allowed_values", {})
    desc_cn = five_layer.get("field_descriptions_cn", {})
    candidate_policy = payload.get("candidate_type_policy", {})
    quality_fields = payload.get("quality_control_fields", {})
    family_guide = payload.get("candidate_family_guidance", {})
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
            "- `candidate_type` is an entry tag, not the final pattern truth.",
            "",
            "## Five-Layer Review Schema",
            "",
            f"- Review order: {five_layer.get('review_order_cn', '')}",
            "",
            "### Fields",
            "",
            *[
                f"- `{field}`: {desc_cn.get(field, '')} Allowed: {', '.join(allowed.get(field, []))}"
                for field in five_layer.get("ordered_fields", [])
            ],
            "",
            "## Quality/Control Fields",
            "",
            *[
                f"- `{field}`: {quality_fields.get('field_descriptions_cn', {}).get(field, '')} Allowed: {', '.join(allowed.get(field, []))}"
                for field in quality_fields.get("fields", [])
            ],
            "",
            "## Candidate Family Guidance",
            "",
            f"- market_context/trend: {family_guide.get('market_context_or_trend', '')}",
            f"- volatility_state: {family_guide.get('volatility_state', '')}",
            f"- candle_observation: {family_guide.get('candle_observation', '')}",
            f"- structure_event: {family_guide.get('structure_event', '')}",
            f"- mixed_overlap: {family_guide.get('mixed_overlap', '')}",
            "",
            "## Candidate Type Clarification",
            "",
            f"- entry_tag_only: `{candidate_policy.get('entry_tag_only')}`",
            f"- final_pattern_truth: `{candidate_policy.get('final_pattern_truth')}`",
            f"- note: {candidate_policy.get('note_cn', '')}",
            "",
        ]
    )
