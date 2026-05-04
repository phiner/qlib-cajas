"""EURUSD pattern review feedback intake validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

FORBIDDEN = {"buy", "sell", "long", "short", "order", "position", "target_position", "signal", "entry", "exit"}


def _load_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        return pd.DataFrame(rows)
    return pd.read_csv(path)


def build_validation_eurusd_pattern_review_feedback(
    *,
    template_csv: Path,
    completed_review_csv: Path,
    label_schema: Path,
) -> dict[str, Any]:
    if not template_csv.exists() or not label_schema.exists():
        return {"schema_version": 1, "status": "blocked", "blocking": True, "blocking_reasons": ["missing_template_or_schema"]}

    template = _load_table(template_csv)
    schema = json.loads(label_schema.read_text(encoding="utf-8"))
    schema_version = schema.get("schema_version")

    if not completed_review_csv.exists():
        return {
            "schema_version": 1,
            "status": "awaiting_review_input",
            "blocking": False,
            "schema_version_expected": schema_version,
            "template_row_count": int(len(template)),
            "completed_row_count": 0,
            "reviewed_count": 0,
            "pending_count": int(len(template)),
            "skipped_count": 0,
            "invalid_row_count": 0,
            "duplicate_sample_id_count": 0,
            "unknown_sample_id_count": 0,
            "forbidden_trading_column_hits": [],
            "label_distribution": {},
            "candidate_type_review_progress": {},
            "review_confidence_distribution": {},
            "quality_score_summary": {},
            "next_action": "complete_human_review_template",
        }

    completed = _load_table(completed_review_csv)

    required_identity = {"sample_id", "timestamp", "candidate_type", "schema_version"}
    required_review = {
        "human_pattern_label",
        "market_context",
        "direction_context",
        "structure_quality",
        "follow_through_quality",
        "review_confidence",
        "review_status",
    }
    missing_cols = sorted((required_identity | required_review).difference(completed.columns))

    forbidden_hits = [c for c in completed.columns if c.lower() in FORBIDDEN]

    invalid_rows = 0
    blockers: list[str] = []
    warnings: list[str] = []

    if missing_cols:
        blockers.append("missing_required_columns")

    if forbidden_hits:
        blockers.append("forbidden_trading_columns")

    if "schema_version" in completed.columns:
        bad_schema = int((completed["schema_version"].astype(str) != str(schema_version)).sum())
        if bad_schema > 0:
            invalid_rows += bad_schema
            blockers.append("schema_version_mismatch")

    allowed = schema.get("allowed_values", {})
    for col in ["human_pattern_label", "market_context", "direction_context", "review_status"]:
        if col in completed.columns and col in allowed:
            bad = ~completed[col].astype(str).isin(set(allowed[col]))
            c = int(bad.sum())
            if c > 0:
                invalid_rows += c
                blockers.append(f"invalid_{col}")

    ranges = schema.get("numeric_ranges", {})
    for col in ["structure_quality", "follow_through_quality", "review_confidence"]:
        if col in completed.columns and col in ranges:
            vals = pd.to_numeric(completed[col], errors="coerce")
            bad = vals.isna() | (vals < ranges[col]["min"]) | (vals > ranges[col]["max"])
            c = int(bad.sum())
            if c > 0:
                invalid_rows += c
                blockers.append(f"invalid_{col}_range")

    duplicate_ids = int(completed.duplicated(subset=["sample_id"]).sum()) if "sample_id" in completed.columns else 0
    if duplicate_ids > 0:
        warnings.append("duplicate_sample_id")

    template_ids = set(template["sample_id"].astype(str)) if "sample_id" in template.columns else set()
    unknown_sample_id_count = 0
    if "sample_id" in completed.columns and template_ids:
        unknown_sample_id_count = int((~completed["sample_id"].astype(str).isin(template_ids)).sum())
        if unknown_sample_id_count > 0:
            warnings.append("unknown_sample_id")

    reviewed_mask = completed.get("review_status", pd.Series([""] * len(completed))).astype(str) == "reviewed"
    reviewed_count = int(reviewed_mask.sum())
    skipped_count = int((completed.get("review_status", pd.Series([""] * len(completed))).astype(str) == "skipped").sum())
    pending_count = int((completed.get("review_status", pd.Series([""] * len(completed))).astype(str) == "pending").sum())

    if "human_pattern_label" in completed.columns:
        empty_label_for_reviewed = int((reviewed_mask & (completed["human_pattern_label"].astype(str).str.strip() == "")).sum())
        if empty_label_for_reviewed > 0:
            invalid_rows += empty_label_for_reviewed
            blockers.append("reviewed_rows_missing_label")

    label_dist = completed.get("human_pattern_label", pd.Series(dtype=str)).fillna("missing").astype(str).value_counts().to_dict()
    candidate_progress = (
        completed.groupby(["candidate_type", "review_status"]).size().unstack(fill_value=0).to_dict(orient="index")
        if {"candidate_type", "review_status"}.issubset(completed.columns)
        else {}
    )
    conf_dist = completed.get("review_confidence", pd.Series(dtype=float)).fillna("missing").astype(str).value_counts().to_dict()

    quality_summary = {}
    for col in ["structure_quality", "follow_through_quality", "review_confidence"]:
        if col in completed.columns:
            vals = pd.to_numeric(completed[col], errors="coerce").dropna()
            quality_summary[col] = {
                "mean": float(vals.mean()) if not vals.empty else None,
                "min": float(vals.min()) if not vals.empty else None,
                "max": float(vals.max()) if not vals.empty else None,
            }

    status = "ready"
    blocking = False
    if blockers:
        status = "blocked"
        blocking = True
    elif warnings:
        status = "watch"

    next_action = "summarize_review_feedback" if status in {"ready", "watch"} else "fix_review_file"

    return {
        "schema_version": 1,
        "status": status,
        "blocking": blocking,
        "schema_version_expected": schema_version,
        "template_row_count": int(len(template)),
        "completed_row_count": int(len(completed)),
        "reviewed_count": reviewed_count,
        "pending_count": pending_count,
        "skipped_count": skipped_count,
        "invalid_row_count": int(invalid_rows),
        "duplicate_sample_id_count": duplicate_ids,
        "unknown_sample_id_count": unknown_sample_id_count,
        "forbidden_trading_column_hits": forbidden_hits,
        "label_distribution": label_dist,
        "candidate_type_review_progress": candidate_progress,
        "review_confidence_distribution": conf_dist,
        "quality_score_summary": quality_summary,
        "warnings": warnings,
        "blocking_reasons": sorted(set(blockers)),
        "next_action": next_action,
    }


def render_validation_eurusd_pattern_review_feedback_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation EURUSD Pattern Review Feedback",
            "",
            f"- status: `{payload.get('status')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- template_row_count: `{payload.get('template_row_count')}`",
            f"- completed_row_count: `{payload.get('completed_row_count')}`",
            f"- reviewed_count: `{payload.get('reviewed_count')}`",
            f"- pending_count: `{payload.get('pending_count')}`",
            f"- next_action: `{payload.get('next_action')}`",
            "",
            "## Policy",
            "",
            "- Feedback intake is review-only and non-trading.",
            "- Missing completed review input is a normal non-blocking state.",
            "",
        ]
    )
