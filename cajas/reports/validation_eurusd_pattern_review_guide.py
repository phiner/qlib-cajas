"""EURUSD 15m pattern review guide report."""
import json
from pathlib import Path
from typing import Any, Dict


def build_review_guide_report(
    label_schema_json: Path,
    batch_report_json: Path = None
) -> Dict[str, Any]:
    """Build human review guide."""
    if not label_schema_json.exists():
        return {
            "status": "blocked",
            "reason": "label_schema_missing",
            "recommendation": "generate_label_schema"
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
            "no_order_generation": True
        },
        "fields_to_fill": [
            "human_pattern_label",
            "market_context",
            "direction_context",
            "structure_quality",
            "follow_through_quality",
            "review_confidence",
            "review_notes",
            "review_status"
        ],
        "label_interpretations": {
            "valid_pattern": "Clear structure with good follow-through",
            "weak_pattern": "Structure present but weak or ambiguous",
            "false_positive": "No meaningful pattern detected",
            "unclear": "Cannot determine from available data",
            "skip_bad_context": "Context makes review unreliable"
        },
        "rating_scale": {
            "1": "poor/unclear",
            "3": "moderate",
            "5": "strong/clear"
        },
        "workflow_steps": [
            "Open batch CSV in spreadsheet or editor",
            "Inspect timestamp, candidate_type, reason_codes, supporting metrics",
            "Optionally inspect nearby bars in charting software",
            "Fill human review fields based on structure clarity",
            "Save completed batch as: tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv",
            "Later merge completed batch into: tmp/eurusd/EURUSD_15m_pattern_review_completed.csv"
        ],
        "warnings": [
            "Candidate tags are NOT trading actions",
            "Do not label based on hindsight profit only",
            "Focus on structure clarity and follow-through quality",
            "This is pattern structure review, not strategy validation"
        ]
    }
    
    return {
        "status": "ready",
        "schema_version": schema.get("schema_version", "unknown"),
        "batch_id": batch_id,
        "guide_sections": guide_sections,
        "output_paths": {},
        "recommendation": "start_batch_review"
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
        "## Fields to Fill",
        ""
    ]
    
    for field in sections["fields_to_fill"]:
        lines.append(f"- `{field}`")
    
    lines.extend([
        "",
        "## Label Interpretations",
        ""
    ])
    
    for label, desc in sections["label_interpretations"].items():
        lines.append(f"- **{label}**: {desc}")
    
    lines.extend([
        "",
        "## Rating Scale (1-5)",
        ""
    ])
    
    for rating, desc in sections["rating_scale"].items():
        lines.append(f"- **{rating}**: {desc}")
    
    lines.extend([
        "",
        "## Review Workflow",
        ""
    ])
    
    for i, step in enumerate(sections["workflow_steps"], 1):
        lines.append(f"{i}. {step}")
    
    lines.extend([
        "",
        "## Warnings",
        ""
    ])
    
    for warning in sections["warnings"]:
        lines.append(f"- ⚠️ {warning}")
    
    lines.extend([
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation']}`"
    ])
    
    return "\n".join(lines)
