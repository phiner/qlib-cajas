"""Manual labeling workflow validation for EURUSD micro-pattern packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_ADDED_FIELDS = [
    "human_micro_pattern_label",
    "human_micro_pattern_confidence",
    "human_micro_pattern_rationale_zh",
    "human_rule_suggestion_zh",
    "human_should_create_rule",
    "suggested_event_key",
    "review_updated_at_utc",
]
ALLOWED_CONFIDENCE = {"", "low", "medium", "high", "1", "2", "3", "4", "5"}
ALLOWED_SHOULD_CREATE = {"", "yes", "no", "uncertain"}
FORBIDDEN_FIELDS = {"trade_signal", "entry", "exit", "order", "position_size", "target_position"}


def _empty_report(status: str, reason: str, packet_csv: Path, completed_csv: Path) -> dict[str, Any]:
    return {
        "report_status": status,
        "reason": reason,
        "packet_csv": str(packet_csv),
        "completed_labels_csv": str(completed_csv),
        "labeled_row_count": 0,
        "total_row_count": 0,
        "missing_required_fields": REQUIRED_ADDED_FIELDS,
    }


def build_micro_pattern_manual_labels_report(
    *,
    packet_csv: Path,
    completed_labels_csv: Path,
    output_template_csv: Path,
) -> dict[str, Any]:
    if not packet_csv.exists():
        return _empty_report("blocked", "packet_csv_missing", packet_csv, completed_labels_csv)

    packet = pd.read_csv(packet_csv)
    template = packet.copy()
    for col in REQUIRED_ADDED_FIELDS:
        if col not in template.columns:
            template[col] = ""
    output_template_csv.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(output_template_csv, index=False)

    if not completed_labels_csv.exists():
        return {
            "report_status": "awaiting_manual_micro_pattern_labels",
            "packet_csv": str(packet_csv),
            "completed_labels_csv": str(completed_labels_csv),
            "completed_template_path": str(output_template_csv),
            "labeled_row_count": 0,
            "total_row_count": int(len(template)),
            "missing_required_fields": [],
            "watch_reasons": ["completed_labels_csv_missing"],
            "blocking_reasons": [],
        }

    completed = pd.read_csv(completed_labels_csv)
    missing = [c for c in REQUIRED_ADDED_FIELDS if c not in completed.columns]
    if missing:
        return {
            "report_status": "blocked",
            "packet_csv": str(packet_csv),
            "completed_labels_csv": str(completed_labels_csv),
            "completed_template_path": str(output_template_csv),
            "labeled_row_count": 0,
            "total_row_count": int(len(completed)),
            "missing_required_fields": missing,
            "watch_reasons": [],
            "blocking_reasons": ["missing_required_label_columns"],
        }

    dup = int(completed.get("sample_id", pd.Series(dtype=str)).astype(str).duplicated().sum()) if "sample_id" in completed.columns else 0
    chinese_schema = [c for c in completed.columns if any("\u4e00" <= ch <= "\u9fff" for ch in c)]
    forbidden_present = [c for c in completed.columns if c.lower() in FORBIDDEN_FIELDS]

    if dup > 0 or chinese_schema or forbidden_present:
        return {
            "report_status": "blocked",
            "packet_csv": str(packet_csv),
            "completed_labels_csv": str(completed_labels_csv),
            "completed_template_path": str(output_template_csv),
            "labeled_row_count": 0,
            "total_row_count": int(len(completed)),
            "missing_required_fields": [],
            "watch_reasons": [],
            "blocking_reasons": [
                "duplicate_sample_id" if dup > 0 else "",
                "chinese_schema_keys_present" if chinese_schema else "",
                "forbidden_trading_fields_present" if forbidden_present else "",
            ],
        }

    labeled_mask = (
        completed["human_micro_pattern_label"].fillna("").astype(str).str.strip() != ""
    )
    labeled = completed[labeled_mask].copy()
    labeled_count = int(len(labeled))

    if labeled_count == 0:
        return {
            "report_status": "awaiting_manual_micro_pattern_labels",
            "packet_csv": str(packet_csv),
            "completed_labels_csv": str(completed_labels_csv),
            "completed_template_path": str(output_template_csv),
            "labeled_row_count": 0,
            "total_row_count": int(len(completed)),
            "missing_required_fields": [],
            "watch_reasons": ["all_manual_fields_empty"],
            "blocking_reasons": [],
        }

    invalid_conf = [x for x in labeled["human_micro_pattern_confidence"].fillna("").astype(str).str.strip().unique() if x not in ALLOWED_CONFIDENCE]
    invalid_create = [x for x in labeled["human_should_create_rule"].fillna("").astype(str).str.strip().unique() if x not in ALLOWED_SHOULD_CREATE]
    if invalid_conf or invalid_create:
        return {
            "report_status": "blocked",
            "packet_csv": str(packet_csv),
            "completed_labels_csv": str(completed_labels_csv),
            "completed_template_path": str(output_template_csv),
            "labeled_row_count": labeled_count,
            "total_row_count": int(len(completed)),
            "missing_required_fields": [],
            "watch_reasons": [],
            "blocking_reasons": ["invalid_manual_label_enums"],
        }

    rationale_ok = labeled["human_micro_pattern_rationale_zh"].fillna("").astype(str).str.strip() != ""
    conf_ok = labeled["human_micro_pattern_confidence"].fillna("").astype(str).str.strip() != ""
    if bool((rationale_ok & conf_ok).all()):
        status = "manual_micro_pattern_labels_ready"
        watch = []
    elif bool((rationale_ok | conf_ok).any()):
        status = "manual_micro_pattern_labels_watch"
        watch = ["partial_labels_missing_confidence_or_rationale"]
    else:
        status = "awaiting_manual_micro_pattern_labels"
        watch = ["labels_without_confidence_and_rationale"]

    return {
        "report_status": status,
        "packet_csv": str(packet_csv),
        "completed_labels_csv": str(completed_labels_csv),
        "completed_template_path": str(output_template_csv),
        "labeled_row_count": labeled_count,
        "total_row_count": int(len(completed)),
        "missing_required_fields": [],
        "watch_reasons": watch,
        "blocking_reasons": [],
    }


def render_micro_pattern_manual_labels_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Micro Pattern Manual Labels",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- labeled_row_count: `{report.get('labeled_row_count')}`",
        f"- total_row_count: `{report.get('total_row_count')}`",
        f"- completed_template_path: `{report.get('completed_template_path')}`",
        "",
        "## Watch Reasons",
        "",
    ]
    for r in report.get("watch_reasons", []) or ["none"]:
        lines.append(f"- {r}")
    lines.extend(["", "## Blocking Reasons", ""])
    for r in [x for x in (report.get("blocking_reasons") or ["none"]) if x]:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"
