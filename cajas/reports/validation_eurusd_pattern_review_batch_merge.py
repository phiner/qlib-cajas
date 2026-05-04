"""EURUSD 15m pattern review batch merge report."""
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


FORBIDDEN_TRADING_COLUMNS = [
    "buy", "sell", "long", "short", "order", "position",
    "target_position", "signal", "entry", "exit"
]


def build_batch_merge_report(
    batch_completion_report_json: Path,
    completed_batch_csv: Path,
    full_completed_review_csv: Path,
    label_schema_json: Path
) -> Dict[str, Any]:
    """Build batch merge report."""
    if not batch_completion_report_json.exists():
        return {
            "status": "blocked",
            "reason": "batch_completion_report_missing",
            "recommendation": "generate_batch_completion_report"
        }
    
    with open(batch_completion_report_json) as f:
        completion_report = json.load(f)
    
    if completion_report.get("status") == "awaiting_completed_batch":
        return {
            "status": "awaiting_completed_batch",
            "blocking": False,
            "merge_performed": False,
            "reviewed_count_added": 0,
            "output_path": str(full_completed_review_csv),
            "next_action": "fill_batch_001_review"
        }
    
    if not completed_batch_csv.exists():
        return {
            "status": "awaiting_completed_batch",
            "blocking": False,
            "merge_performed": False,
            "reviewed_count_added": 0,
            "output_path": str(full_completed_review_csv),
            "next_action": "fill_batch_001_review"
        }
    
    if not label_schema_json.exists():
        return {
            "status": "blocked",
            "reason": "label_schema_missing",
            "recommendation": "generate_label_schema"
        }
    
    with open(label_schema_json) as f:
        schema = json.load(f)
    
    completed_batch_df = pd.read_csv(completed_batch_csv)
    
    # Check forbidden columns
    forbidden_hits = [c for c in completed_batch_df.columns if c.lower() in FORBIDDEN_TRADING_COLUMNS]
    if forbidden_hits:
        return {
            "status": "blocked",
            "blocking": True,
            "reason": "forbidden_trading_columns_detected",
            "forbidden_columns": forbidden_hits,
            "merge_performed": False,
            "next_action": "fix_completed_batch"
        }
    
    # Validate schema
    allowed_labels = schema.get("allowed_values", {}).get("human_pattern_label", [])
    allowed_market = schema.get("allowed_values", {}).get("market_context", [])
    allowed_direction = schema.get("allowed_values", {}).get("direction_context", [])
    
    invalid_rows = []
    for idx, row in completed_batch_df.iterrows():
        if pd.notna(row.get("human_pattern_label")) and row["human_pattern_label"] not in allowed_labels:
            invalid_rows.append(idx)
        if pd.notna(row.get("market_context")) and row["market_context"] not in allowed_market:
            invalid_rows.append(idx)
        if pd.notna(row.get("direction_context")) and row["direction_context"] not in allowed_direction:
            invalid_rows.append(idx)
    
    if invalid_rows:
        return {
            "status": "blocked",
            "blocking": True,
            "reason": "invalid_enum_values",
            "invalid_row_count": len(set(invalid_rows)),
            "merge_performed": False,
            "next_action": "fix_completed_batch"
        }
    
    # Perform merge
    created_new = False
    backup_path = None
    
    if full_completed_review_csv.exists():
        # Backup existing
        backup_path = full_completed_review_csv.parent / f"{full_completed_review_csv.stem}.backup.csv"
        full_df = pd.read_csv(full_completed_review_csv)
        full_df.to_csv(backup_path, index=False)
        
        # Merge by sample_id
        existing_ids = set(full_df["sample_id"])
        new_rows = []
        updated_count = 0
        
        for _, row in completed_batch_df.iterrows():
            if row["sample_id"] in existing_ids:
                # Update existing
                mask = full_df["sample_id"] == row["sample_id"]
                full_df.loc[mask] = row
                updated_count += 1
            else:
                new_rows.append(row)
        
        if new_rows:
            full_df = pd.concat([full_df, pd.DataFrame(new_rows)], ignore_index=True)
        
        reviewed_count_added = len(new_rows) + updated_count
        duplicate_count = len(completed_batch_df) - reviewed_count_added
    else:
        # Create new
        full_df = completed_batch_df.copy()
        created_new = True
        reviewed_count_added = len(completed_batch_df)
        duplicate_count = 0
        updated_count = 0
    
    full_completed_review_csv.parent.mkdir(parents=True, exist_ok=True)
    full_df.to_csv(full_completed_review_csv, index=False)
    
    reviewed_total = len(full_df[full_df["review_status"] == "reviewed"])
    
    result = {
        "status": "ready",
        "blocking": False,
        "merge_performed": True,
        "reviewed_count_added": reviewed_count_added,
        "reviewed_count_total": reviewed_total,
        "duplicate_sample_id_count": duplicate_count,
        "updated_existing_count": updated_count,
        "created_new_completed_file": created_new,
        "output_path": str(full_completed_review_csv),
        "next_action": "regenerate_review_feedback_summary"
    }
    
    if backup_path:
        result["backup_path"] = str(backup_path)
    
    return result


def format_batch_merge_markdown(report: Dict[str, Any]) -> str:
    """Format batch merge report as markdown."""
    lines = [
        "# EURUSD 15m Pattern Review Batch Merge Report",
        "",
        f"**Status**: `{report['status']}`",
        f"**Blocking**: `{report.get('blocking', False)}`",
        ""
    ]
    
    if report.get("merge_performed"):
        lines.extend([
            "## Merge Summary",
            "",
            f"- Merge performed: {report['merge_performed']}",
            f"- Reviewed count added: {report['reviewed_count_added']}",
            f"- Reviewed count total: {report['reviewed_count_total']}",
            f"- Duplicate sample IDs: {report['duplicate_sample_id_count']}",
            f"- Updated existing: {report['updated_existing_count']}",
            f"- Created new file: {report['created_new_completed_file']}",
            f"- Output path: `{report['output_path']}`",
            ""
        ])
        
        if "backup_path" in report:
            lines.append(f"- Backup path: `{report['backup_path']}`")
            lines.append("")
    else:
        lines.extend([
            "## Status",
            "",
            f"- Merge performed: {report['merge_performed']}",
            f"- Reviewed count added: {report['reviewed_count_added']}",
            ""
        ])
    
    lines.extend([
        "## Next Action",
        "",
        f"`{report['next_action']}`"
    ])
    
    return "\n".join(lines)
