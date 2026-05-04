"""EURUSD 15m pattern review batch builder report."""
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


FORBIDDEN_TRADING_COLUMNS = [
    "buy", "sell", "long", "short", "order", "position",
    "target_position", "signal", "entry", "exit"
]


def build_review_batch_report(
    template_csv: Path,
    label_schema_json: Path,
    batch_id: str,
    batch_size: int,
    per_type_target: int,
    output_batch_csv: Path,
    output_batch_jsonl: Path,
) -> Dict[str, Any]:
    """Build first review batch from template."""
    if not template_csv.exists():
        return {
            "status": "blocked",
            "reason": "template_csv_missing",
            "recommendation": "generate_review_template"
        }
    
    if not label_schema_json.exists():
        return {
            "status": "blocked",
            "reason": "label_schema_missing",
            "recommendation": "generate_label_schema"
        }
    
    with open(label_schema_json) as f:
        schema = json.load(f)
    
    df = pd.read_csv(template_csv)
    
    # Check forbidden columns
    forbidden_hits = [c for c in df.columns if c.lower() in FORBIDDEN_TRADING_COLUMNS]
    if forbidden_hits:
        return {
            "status": "blocked",
            "reason": "forbidden_trading_columns_detected",
            "forbidden_columns": forbidden_hits,
            "recommendation": "remove_forbidden_columns"
        }
    
    # Select balanced batch
    batch_rows = []
    batch_counts = {}
    
    for ctype in df["candidate_type"].unique():
        ctype_df = df[df["candidate_type"] == ctype].copy()
        ctype_df = ctype_df.sort_values(
            by=["review_priority", "confidence_score", "timestamp"],
            ascending=[True, False, True]
        )
        selected = ctype_df.head(per_type_target)
        batch_rows.append(selected)
        batch_counts[ctype] = len(selected)
    
    batch_df = pd.concat(batch_rows, ignore_index=True)
    batch_df = batch_df.head(batch_size)
    
    output_batch_csv.parent.mkdir(parents=True, exist_ok=True)
    batch_df.to_csv(output_batch_csv, index=False)
    
    batch_df.to_json(output_batch_jsonl, orient="records", lines=True)
    
    status = "ready"
    if any(c < per_type_target for c in batch_counts.values()):
        status = "watch"
    
    return {
        "status": status,
        "batch_id": batch_id,
        "schema_version": schema.get("schema_version", "unknown"),
        "template_row_count": len(df),
        "batch_row_count": len(batch_df),
        "candidate_type_count": len(batch_counts),
        "batch_count_by_type": batch_counts,
        "selection_policy": f"balanced_{per_type_target}_per_type_up_to_{batch_size}",
        "output_paths": {
            "batch_csv": str(output_batch_csv),
            "batch_jsonl": str(output_batch_jsonl)
        },
        "forbidden_trading_column_hits": [],
        "recommendation": "review_batch_001"
    }


def format_batch_report_markdown(report: Dict[str, Any]) -> str:
    """Format batch report as markdown."""
    lines = [
        "# EURUSD 15m Pattern Review Batch Report",
        "",
        f"**Status**: `{report['status']}`",
        f"**Batch ID**: `{report['batch_id']}`",
        f"**Schema Version**: `{report['schema_version']}`",
        "",
        "## Batch Summary",
        "",
        f"- Template rows: {report['template_row_count']}",
        f"- Batch rows: {report['batch_row_count']}",
        f"- Candidate types: {report['candidate_type_count']}",
        f"- Selection policy: {report['selection_policy']}",
        "",
        "## Batch Counts by Type",
        ""
    ]
    
    for ctype, count in report["batch_count_by_type"].items():
        lines.append(f"- `{ctype}`: {count}")
    
    lines.extend([
        "",
        "## Output Paths",
        "",
        f"- Batch CSV: `{report['output_paths']['batch_csv']}`",
        f"- Batch JSONL: `{report['output_paths']['batch_jsonl']}`",
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation']}`"
    ])
    
    return "\n".join(lines)
