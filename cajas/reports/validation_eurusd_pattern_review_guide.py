"""EURUSD 15m pattern review guide report."""

import json
from pathlib import Path
from typing import Any, Dict


def build_review_guide_report(label_schema_json: Path, batch_report_json: Path = None) -> Dict[str, Any]:
    """Build human review guide."""
    if not label_schema_json.exists():
        return {
            "status": "blocked",
            "reason": "label_schema_missing",
            "recommendation": "generate_label_schema",
        }

    with open(label_schema_json) as f:
        schema = json.load(f)

    batch_id = "eurusd_15m_pattern_review_batch_001"
    if batch_report_json and batch_report_json.exists():
        with open(batch_report_json) as f:
            batch_report = json.load(f)
            batch_id = batch_report.get("batch_id", batch_id)

    guide_sections = {
        "scope": {
            "symbol": "EURUSD",
            "timeframe": "15m",
            "price_side": "Bid",
            "review_type": "human_manual_review",
            "no_trading_signals": True,
            "no_order_generation": True,
        },
        "fields_to_fill": [
            "human_pattern_label",
            "market_context",
            "direction_context",
            "structure_quality",
            "follow_through_quality",
            "review_confidence",
            "review_notes",
            "review_status",
        ],
        "five_layer_review_order": [
            {"field": "market_context", "cn": "背景层"},
            {"field": "structure_location", "cn": "结构位置层"},
            {"field": "local_behavior", "cn": "局部行为层"},
            {"field": "confirmation_result", "cn": "确认/失败层"},
            {"field": "review_outcome", "cn": "人审结论层"},
        ],
        "review_principles_cn": [
            "先看背景，再看位置，再看局部行为，再看确认/失败，最后给人审结论。",
            "不要只按 candidate_type 判断。",
            "candidate_type 是系统把样本送进来的原因，不是最终形态名称。",
        ],
        "candidate_type_clarification": {
            "entry_tag_only": True,
            "final_pattern_truth": False,
            "note": "candidate_type is a system entry tag, not final label truth.",
        },
        "candidate_family_guidance": {
            "market_context_or_trend": "Use as context/background, not final pattern.",
            "volatility_state": "Compression/expansion are states, not complete setups.",
            "candle_observation": "Wick/doji are local observations and need structure location.",
            "structure_event": "possible_false_breakout_candidate is a structure hypothesis and needs level/context validation.",
            "mixed_overlap": "Record ambiguity and secondary family when needed.",
        },
        "label_interpretations": {
            "valid_pattern": "Clear structure with good follow-through",
            "weak_pattern": "Structure present but weak or ambiguous",
            "false_positive": "No meaningful pattern detected",
            "unclear": "Cannot determine from available data",
            "skip_bad_context": "Context makes review unreliable",
        },
        "rating_scale": {
            "1": "poor/unclear",
            "3": "moderate",
            "5": "strong/clear",
        },
        "workflow_steps": [
            "Open batch CSV in spreadsheet or editor",
            "Inspect timestamp, candidate_type, reason_codes, supporting metrics",
            "Optionally inspect nearby bars in charting software",
            "Fill human review fields based on structure clarity",
            "Save completed batch as: tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv",
            "Later merge completed batch into: tmp/eurusd/EURUSD_15m_pattern_review_completed.csv",
        ],
        "warnings": [
            "Candidate tags are NOT trading actions",
            "candidate_type is an entry tag, not final pattern truth",
            "Do not label based on hindsight profit only",
            "Focus on structure clarity and follow-through quality",
            "This is pattern structure review, not strategy validation",
            "Do not resume large-scale GUI review until reviewer instructions are explicit.",
        ],
    }

    return {
        "status": "ready",
        "schema_version": schema.get("schema_version", "unknown"),
        "batch_id": batch_id,
        "guide_sections": guide_sections,
        "output_paths": {},
        "recommendation": "start_batch_review",
    }


def format_review_guide_markdown(report: Dict[str, Any]) -> str:
    """Format review guide as markdown."""
    sections = report["guide_sections"]

    lines = [
        "# EURUSD 15m Pattern Review Guide",
        "",
        f"**Schema Version**: `{report['schema_version']}`",
        f"**Batch ID**: `{report['batch_id']}`",
        "",
        "## Scope",
        "",
        f"- Symbol: {sections['scope']['symbol']}",
        f"- Timeframe: {sections['scope']['timeframe']}",
        f"- Price side: {sections['scope']['price_side']}",
        f"- Review type: {sections['scope']['review_type']}",
        f"- No trading signals: {sections['scope']['no_trading_signals']}",
        f"- No order generation: {sections['scope']['no_order_generation']}",
        "",
        "## Five-Layer Order",
        "",
    ]

    for item in sections["five_layer_review_order"]:
        lines.append(f"- `{item['field']}` ({item['cn']})")

    lines.extend(["", "## Reviewer Principles (CN)", ""])
    for row in sections["review_principles_cn"]:
        lines.append(f"- {row}")

    lines.extend(["", "## Candidate Family Guidance", ""])
    lines.append(f"- market_context/trend: {sections['candidate_family_guidance']['market_context_or_trend']}")
    lines.append(f"- volatility_state: {sections['candidate_family_guidance']['volatility_state']}")
    lines.append(f"- candle_observation: {sections['candidate_family_guidance']['candle_observation']}")
    lines.append(f"- structure_event: {sections['candidate_family_guidance']['structure_event']}")
    lines.append(f"- mixed_overlap: {sections['candidate_family_guidance']['mixed_overlap']}")

    lines.extend(
        [
            "",
            "## Candidate Type Clarification",
            "",
            f"- entry_tag_only: `{sections['candidate_type_clarification']['entry_tag_only']}`",
            f"- final_pattern_truth: `{sections['candidate_type_clarification']['final_pattern_truth']}`",
            f"- note: {sections['candidate_type_clarification']['note']}",
            "",
            "## Fields to Fill",
            "",
        ]
    )

    for field in sections["fields_to_fill"]:
        lines.append(f"- `{field}`")

    lines.extend(["", "## Label Interpretations", ""])
    for label, desc in sections["label_interpretations"].items():
        lines.append(f"- **{label}**: {desc}")

    lines.extend(["", "## Rating Scale (1-5)", ""])
    for rating, desc in sections["rating_scale"].items():
        lines.append(f"- **{rating}**: {desc}")

    lines.extend(["", "## Review Workflow", ""])
    for i, step in enumerate(sections["workflow_steps"], 1):
        lines.append(f"{i}. {step}")

    lines.extend(["", "## Warnings", ""])
    for warning in sections["warnings"]:
        lines.append(f"- {warning}")

    lines.extend(["", "## Recommendation", "", f"`{report['recommendation']}`"])

    return "\n".join(lines)
