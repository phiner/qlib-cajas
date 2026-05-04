"""EURUSD rejected sample registry validation report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "sample_id",
    "timestamp",
    "candidate_type",
    "rejection_reason",
    "rejection_notes",
    "rejected_at_utc",
    "review_batch_id",
    "source_batch_csv",
    "reviewer_id_optional",
    "schema_version",
]


def build_rejected_samples_report(*, rejected_csv: Path, rejected_events_jsonl: Path) -> dict[str, Any]:
    if not rejected_csv.exists():
        return {
            "status": "not_found",
            "rejected_csv": str(rejected_csv),
            "rejected_events_jsonl": str(rejected_events_jsonl),
            "rejected_count": 0,
            "reason_distribution": {},
            "candidate_type_distribution": {},
            "recent_rejected_samples": [],
        }

    df = pd.read_csv(rejected_csv)
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        return {
            "status": "blocked",
            "reason": "rejected_schema_missing_columns",
            "missing_columns": missing_columns,
            "rejected_csv": str(rejected_csv),
            "rejected_events_jsonl": str(rejected_events_jsonl),
        }

    rows = df[REQUIRED_COLUMNS].copy().drop_duplicates(subset=["sample_id"], keep="last")
    reason_distribution = rows["rejection_reason"].fillna("").astype(str).value_counts().to_dict()
    candidate_distribution = rows["candidate_type"].fillna("").astype(str).value_counts().to_dict()

    events_count = 0
    if rejected_events_jsonl.exists():
        events_count = len([ln for ln in rejected_events_jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()])

    recent = (
        rows.sort_values("rejected_at_utc", ascending=False)
        .head(10)
        [["sample_id", "rejection_reason", "rejected_at_utc", "candidate_type"]]
        .to_dict(orient="records")
    )

    return {
        "status": "ready",
        "rejected_csv": str(rejected_csv),
        "rejected_events_jsonl": str(rejected_events_jsonl),
        "rejected_count": int(len(rows)),
        "events_count": int(events_count),
        "reason_distribution": {str(k): int(v) for k, v in reason_distribution.items()},
        "candidate_type_distribution": {str(k): int(v) for k, v in candidate_distribution.items()},
        "recent_rejected_samples": recent,
    }


def format_rejected_samples_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Rejected Samples Report",
        "",
        f"**Status**: `{report.get('status')}`",
        f"**Rejected count**: `{report.get('rejected_count', 0)}`",
        f"**Events count**: `{report.get('events_count', 0)}`",
        "",
        "## Reason Distribution",
        "",
    ]
    reason_dist = report.get("reason_distribution", {})
    if not reason_dist:
        lines.append("- none")
    else:
        for key, value in reason_dist.items():
            lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Candidate Type Distribution", ""])
    cand_dist = report.get("candidate_type_distribution", {})
    if not cand_dist:
        lines.append("- none")
    else:
        for key, value in cand_dist.items():
            lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Recent Rejected Samples", ""])
    recent = report.get("recent_rejected_samples", [])
    if not recent:
        lines.append("- none")
    else:
        for item in recent:
            lines.append(
                f"- `{item.get('sample_id')}` | reason=`{item.get('rejection_reason')}` "
                f"| type=`{item.get('candidate_type')}` | at=`{item.get('rejected_at_utc')}`"
            )
    return "\n".join(lines) + "\n"
