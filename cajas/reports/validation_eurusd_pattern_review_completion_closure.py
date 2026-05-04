"""EURUSD 15m review completion closure report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.research.eurusd_pattern_review_gui import (
    FORBIDDEN_TRADING_COLUMNS,
    REVIEW_FIELDS,
)


def _safe_read_csv(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    try:
        return pd.read_csv(path), None
    except Exception as exc:
        return None, str(exc)


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    malformed: list[str] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        row = line.strip()
        if not row:
            continue
        try:
            parsed = json.loads(row)
            if isinstance(parsed, dict):
                items.append(parsed)
            else:
                malformed.append(f"line_{idx}_not_object")
        except Exception:
            malformed.append(f"line_{idx}_invalid_json")
    return items, malformed


def _invalid_score_rows(df: pd.DataFrame) -> list[str]:
    bad: list[str] = []
    for score_col in ("structure_quality", "follow_through_quality", "review_confidence"):
        if score_col not in df.columns:
            continue
        vals = pd.to_numeric(df[score_col], errors="coerce")
        invalid = vals[(vals < 1) | (vals > 5) | vals.isna()].index
        for idx in invalid.tolist():
            sid = str(df.loc[idx, "sample_id"]) if "sample_id" in df.columns else f"row_{idx}"
            bad.append(sid)
    return sorted(set(bad))


def _invalid_enum_rows(df: pd.DataFrame, schema: dict[str, Any]) -> list[str]:
    allowed = (schema.get("allowed_values") or {})
    legacy = (schema.get("legacy_allowed_values") or {})
    bad: list[str] = []
    enum_fields = ("human_pattern_label", "market_context", "direction_context", "review_status")
    for field in enum_fields:
        if field not in df.columns:
            continue
        allowed_values = {str(x) for x in (allowed.get(field) or [])}
        allowed_values |= {str(x) for x in (legacy.get(field) or [])}
        if not allowed_values:
            continue
        for idx, value in df[field].items():
            if pd.isna(value):
                continue
            if str(value) not in allowed_values:
                sid = str(df.loc[idx, "sample_id"]) if "sample_id" in df.columns else f"row_{idx}"
                bad.append(sid)
    return sorted(set(bad))


def build_review_completion_closure_report(
    *,
    batch_csv: Path,
    completed_csv: Path,
    label_schema_json: Path,
    audit_jsonl: Path | None = None,
) -> dict[str, Any]:
    if not batch_csv.exists():
        return {
            "status": "blocked",
            "review_state": "blocked",
            "blocking": True,
            "reason": "batch_csv_missing",
            "next_action": "generate_review_batch",
        }

    batch_df, batch_err = _safe_read_csv(batch_csv)
    if batch_df is None:
        return {
            "status": "blocked",
            "review_state": "blocked",
            "blocking": True,
            "reason": "batch_csv_unreadable",
            "error": batch_err,
            "next_action": "repair_batch_csv",
        }

    schema: dict[str, Any] = {}
    if label_schema_json.exists():
        schema = json.loads(label_schema_json.read_text(encoding="utf-8"))

    batch_ids = [str(x) for x in batch_df.get("sample_id", pd.Series([], dtype=str)).tolist()]
    batch_id_set = set(batch_ids)
    batch_count = len(batch_ids)

    base: dict[str, Any] = {
        "batch_path": str(batch_csv),
        "completed_csv_path": str(completed_csv),
        "audit_jsonl_path": str(audit_jsonl) if audit_jsonl else None,
        "batch_count": batch_count,
        "completed_count": 0,
        "pending_count": batch_count,
        "completion_ratio": 0.0 if batch_count else 1.0,
        "completed_sample_ids": [],
        "pending_sample_ids": batch_ids,
        "duplicate_completed_sample_ids": [],
        "missing_required_review_fields": [],
        "invalid_review_rows": [],
        "jsonl_event_count": 0,
        "jsonl_unique_sample_count": 0,
        "jsonl_samples_without_completed_csv": [],
        "completed_csv_samples_without_jsonl": [],
        "latest_review_updated_at_utc": None,
    }

    if not completed_csv.exists():
        return {
            **base,
            "status": "awaiting_review_input",
            "review_state": "awaiting_review_input",
            "blocking": False,
            "next_action": "continue_human_review",
        }

    completed_df, completed_err = _safe_read_csv(completed_csv)
    if completed_df is None:
        return {
            **base,
            "status": "blocked",
            "review_state": "blocked",
            "blocking": True,
            "reason": "completed_csv_unreadable",
            "error": completed_err,
            "next_action": "repair_completed_csv",
        }

    forbidden_cols = [c for c in completed_df.columns if c.lower() in FORBIDDEN_TRADING_COLUMNS]
    required_cols = ["sample_id", *REVIEW_FIELDS, "review_updated_at_utc"]
    missing_required = [c for c in required_cols if c not in completed_df.columns]
    if "sample_id" not in completed_df.columns:
        return {
            **base,
            "status": "blocked",
            "review_state": "blocked",
            "blocking": True,
            "reason": "missing_sample_id",
            "missing_required_review_fields": missing_required or ["sample_id"],
            "next_action": "repair_completed_csv_schema",
        }

    dup_ids = sorted(
        {
            str(x)
            for x, n in completed_df["sample_id"].astype(str).value_counts().items()
            if int(n) > 1
        }
    )
    invalid_rows = sorted(set(_invalid_score_rows(completed_df) + _invalid_enum_rows(completed_df, schema)))
    completed_ids = sorted({str(x) for x in completed_df["sample_id"].astype(str).tolist()})
    completed_in_batch = sorted([sid for sid in completed_ids if sid in batch_id_set])
    pending_ids = sorted([sid for sid in batch_ids if sid not in set(completed_in_batch)])
    latest_review_updated_at_utc = None
    if "review_updated_at_utc" in completed_df.columns:
        series = completed_df["review_updated_at_utc"].dropna().astype(str)
        latest_review_updated_at_utc = max(series.tolist()) if not series.empty else None

    jsonl_items: list[dict[str, Any]] = []
    jsonl_malformed: list[str] = []
    if audit_jsonl and audit_jsonl.exists():
        jsonl_items, jsonl_malformed = _safe_read_jsonl(audit_jsonl)
    jsonl_sample_ids = sorted(
        {str(item.get("sample_id")) for item in jsonl_items if item.get("sample_id") is not None}
    )
    completed_set = set(completed_in_batch)
    jsonl_set = set(jsonl_sample_ids)
    jsonl_without_completed = sorted([sid for sid in jsonl_sample_ids if sid not in completed_set])
    completed_without_jsonl = sorted([sid for sid in completed_in_batch if sid not in jsonl_set])

    report = {
        **base,
        "completed_count": len(completed_in_batch),
        "pending_count": len(pending_ids),
        "completion_ratio": (len(completed_in_batch) / batch_count) if batch_count else 1.0,
        "completed_sample_ids": completed_in_batch,
        "pending_sample_ids": pending_ids,
        "duplicate_completed_sample_ids": dup_ids,
        "missing_required_review_fields": missing_required,
        "invalid_review_rows": invalid_rows,
        "jsonl_event_count": len(jsonl_items),
        "jsonl_unique_sample_count": len(jsonl_sample_ids),
        "jsonl_samples_without_completed_csv": jsonl_without_completed,
        "completed_csv_samples_without_jsonl": completed_without_jsonl,
        "latest_review_updated_at_utc": latest_review_updated_at_utc,
        "forbidden_columns_detected": forbidden_cols,
        "jsonl_malformed_lines": jsonl_malformed,
    }

    hard_block = bool(missing_required or forbidden_cols or dup_ids)
    if hard_block:
        report.update(
            {
                "status": "blocked",
                "review_state": "blocked",
                "blocking": True,
                "next_action": "repair_completed_csv_schema",
            }
        )
        return report

    if report["completed_count"] == 0:
        report.update(
            {
                "status": "awaiting_review_input",
                "review_state": "awaiting_review_input",
                "blocking": False,
                "next_action": "continue_human_review",
            }
        )
        return report

    jsonl_warning = bool(jsonl_malformed or completed_without_jsonl or jsonl_without_completed)
    missing_jsonl = bool(audit_jsonl and not audit_jsonl.exists())
    if report["pending_count"] > 0:
        report.update(
            {
                "status": "in_progress",
                "review_state": "in_progress",
                "blocking": False,
                "next_action": "continue_human_review",
            }
        )
    else:
        report.update(
            {
                "status": "ready_for_summary",
                "review_state": "ready_for_summary",
                "blocking": False,
                "next_action": "run_review_summary",
            }
        )

    if invalid_rows:
        report.update(
            {
                "status": "warning",
                "review_state": report["review_state"],
                "blocking": False,
                "next_action": "repair_invalid_review_rows",
            }
        )
    elif missing_jsonl or jsonl_warning:
        report.update(
            {
                "status": "warning",
                "review_state": report["review_state"],
                "blocking": False,
                "next_action": "continue_human_review" if report["pending_count"] > 0 else "run_review_summary",
            }
        )
    return report


def render_review_completion_closure_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EURUSD 15m Review Completion Closure",
        "",
        f"- status: `{payload.get('status')}`",
        f"- review_state: `{payload.get('review_state')}`",
        f"- blocking: `{payload.get('blocking')}`",
        f"- batch_count: `{payload.get('batch_count')}`",
        f"- completed_count: `{payload.get('completed_count')}`",
        f"- pending_count: `{payload.get('pending_count')}`",
        f"- completion_ratio: `{payload.get('completion_ratio')}`",
        f"- jsonl_event_count: `{payload.get('jsonl_event_count')}`",
        f"- jsonl_unique_sample_count: `{payload.get('jsonl_unique_sample_count')}`",
        f"- latest_review_updated_at_utc: `{payload.get('latest_review_updated_at_utc')}`",
        f"- next_action: `{payload.get('next_action')}`",
        "",
        "## Audit",
        "",
        f"- duplicate_completed_sample_ids: `{payload.get('duplicate_completed_sample_ids')}`",
        f"- missing_required_review_fields: `{payload.get('missing_required_review_fields')}`",
        f"- invalid_review_rows: `{payload.get('invalid_review_rows')}`",
        f"- jsonl_malformed_lines: `{payload.get('jsonl_malformed_lines')}`",
        f"- jsonl_samples_without_completed_csv: `{payload.get('jsonl_samples_without_completed_csv')}`",
        f"- completed_csv_samples_without_jsonl: `{payload.get('completed_csv_samples_without_jsonl')}`",
    ]
    return "\n".join(lines)
