"""EURUSD 15m pattern review batch completion report."""
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


FORBIDDEN_TRADING_COLUMNS = [
    "buy", "sell", "long", "short", "order", "position",
    "target_position", "signal", "entry", "exit"
]


def _allowed_with_legacy(schema: Dict[str, Any], field: str) -> set[str]:
    allowed = {str(v) for v in schema.get("allowed_values", {}).get(field, [])}
    legacy = {str(v) for v in schema.get("legacy_allowed_values", {}).get(field, [])}
    return allowed | legacy


def build_batch_completion_report(
    batch_csv: Path,
    completed_batch_csv: Path,
    label_schema_json: Path
) -> Dict[str, Any]:
    """Build batch completion report."""
    if not batch_csv.exists():
        return {
            "status": "blocked",
            "reason": "batch_csv_missing",
            "recommendation": "generate_review_batch"
        }
    
    if not label_schema_json.exists():
        return {
            "status": "blocked",
            "reason": "label_schema_missing",
            "recommendation": "generate_label_schema"
        }
    
    with open(label_schema_json) as f:
        schema = json.load(f)
    
    batch_df = pd.read_csv(batch_csv)
    batch_row_count = len(batch_df)
    
    if not completed_batch_csv.exists():
        return {
            "status": "awaiting_completed_batch",
            "blocking": False,
            "batch_row_count": batch_row_count,
            "reviewed_count": 0,
            "pending_count": batch_row_count,
            "next_action": "fill_batch_001_review",
            "recommendation": "complete_batch_review"
        }
    
    completed_df = pd.read_csv(completed_batch_csv)
    
    # Check forbidden columns
    forbidden_hits = [c for c in completed_df.columns if c.lower() in FORBIDDEN_TRADING_COLUMNS]
    if forbidden_hits:
        return {
            "status": "blocked",
            "reason": "forbidden_trading_columns_detected",
            "forbidden_columns": forbidden_hits,
            "recommendation": "remove_forbidden_columns"
        }
    
    # Validate schema
    allowed_labels = _allowed_with_legacy(schema, "human_pattern_label")
    allowed_market = _allowed_with_legacy(schema, "market_context")
    allowed_direction = _allowed_with_legacy(schema, "direction_context")
    
    invalid_rows = []
    for idx, row in completed_df.iterrows():
        if pd.notna(row.get("human_pattern_label")) and row["human_pattern_label"] not in allowed_labels:
            invalid_rows.append(idx)
        if pd.notna(row.get("market_context")) and row["market_context"] not in allowed_market:
            invalid_rows.append(idx)
        if pd.notna(row.get("direction_context")) and row["direction_context"] not in allowed_direction:
            invalid_rows.append(idx)
    
    if invalid_rows:
        return {
            "status": "blocked",
            "reason": "invalid_enum_values",
            "invalid_row_count": len(set(invalid_rows)),
            "recommendation": "fix_enum_values"
        }
    
    # Count reviewed
    reviewed_count = len(completed_df[completed_df["review_status"] == "reviewed"])
    pending_count = len(completed_df[completed_df["review_status"] == "pending"])
    skipped_count = len(completed_df[completed_df["human_pattern_label"] == "skip_bad_context"])
    
    status = "ready" if reviewed_count > 0 else "watch"
    
    return {
        "status": status,
        "blocking": False,
        "batch_row_count": batch_row_count,
        "completed_row_count": len(completed_df),
        "reviewed_count": reviewed_count,
        "pending_count": pending_count,
        "skipped_count": skipped_count,
        "invalid_count": 0,
        "next_action": "merge_completed_batch" if reviewed_count > 0 else "continue_batch_review",
        "recommendation": "merge_completed_batch" if reviewed_count > 0 else "continue_batch_review"
    }


def format_batch_completion_markdown(report: Dict[str, Any]) -> str:
    """Format batch completion report as markdown."""
    lines = [
        "# EURUSD 15m Pattern Review Batch Completion Report",
        "",
        f"**Status**: `{report['status']}`",
        f"**Blocking**: `{report['blocking']}`",
        "",
        "## Batch Summary",
        "",
        f"- Batch rows: {report['batch_row_count']}"
    ]
    
    if "completed_row_count" in report:
        lines.extend([
            f"- Completed rows: {report['completed_row_count']}",
            f"- Reviewed: {report['reviewed_count']}",
            f"- Pending: {report['pending_count']}",
            f"- Skipped: {report['skipped_count']}",
            f"- Invalid: {report['invalid_count']}"
        ])
    else:
        lines.extend([
            f"- Reviewed: {report['reviewed_count']}",
            f"- Pending: {report['pending_count']}"
        ])
    
    lines.extend([
        "",
        "## Next Action",
        "",
        f"`{report['next_action']}`",
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation']}`"
    ])
    
    return "\n".join(lines)
