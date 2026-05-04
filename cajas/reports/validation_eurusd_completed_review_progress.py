"""EURUSD completed review progress and audit report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.research.eurusd_pattern_review_gui import FORBIDDEN_TRADING_COLUMNS

REVIEW_ENUM_FIELDS = ["human_pattern_label", "market_context", "direction_context", "review_status"]
REVIEW_SCORE_FIELDS = ["structure_quality", "follow_through_quality", "review_confidence"]
REQUIRED_IDENTITY_FIELDS = ["sample_id", "timestamp", "candidate_type"]
REQUIRED_REVIEW_FIELDS = [
    "human_pattern_label",
    "market_context",
    "direction_context",
    "review_status",
    "structure_quality",
    "follow_through_quality",
    "review_confidence",
    "review_notes",
    "review_updated_at_utc",
]
COMPARE_REVIEW_FIELDS = [
    "human_pattern_label",
    "market_context",
    "direction_context",
    "review_status",
    "structure_quality",
    "follow_through_quality",
    "review_confidence",
    "review_notes",
]


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_csv(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    try:
        return pd.read_csv(path), None
    except Exception as exc:
        return None, str(exc)


def _safe_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    malformed: list[str] = []
    for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                records.append(parsed)
            else:
                malformed.append(f"line_{ln}_not_object")
        except Exception:
            malformed.append(f"line_{ln}_invalid_json")
    return records, malformed


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v)


def _is_reviewed(v: Any) -> bool:
    return _norm(v).strip().lower() == "reviewed"


def _keyword_counts(values: list[str]) -> dict[str, int]:
    keys = [
        "weekend gap",
        "market closed",
        "unclear",
        "bad sample",
        "good wick",
        "周末",
        "跳空",
        "不清楚",
        "趋势",
        "影线",
    ]
    out: dict[str, int] = {k: 0 for k in keys}
    for val in values:
        text = val.lower()
        for key in keys:
            if key in val or key in text:
                out[key] += 1
    return out


def _allowed_with_legacy(schema: dict[str, Any], field: str) -> set[str]:
    allowed = {str(v) for v in schema.get("allowed_values", {}).get(field, [])}
    legacy = {str(v) for v in schema.get("legacy_allowed_values", {}).get(field, [])}
    return allowed | legacy


def build_completed_review_progress_report(
    *,
    batch_csv: Path,
    completed_csv: Path,
    events_jsonl: Path,
    label_schema_json: Path,
    rejected_csv: Path | None = None,
) -> dict[str, Any]:
    base = {
        "batch_csv": str(batch_csv),
        "completed_csv": str(completed_csv),
        "events_jsonl": str(events_jsonl),
        "batch_count": 0,
        "completed_count": 0,
        "pending_count": 0,
        "completion_ratio": 0.0,
        "completed_sample_ids": [],
        "pending_sample_ids": [],
        "latest_review_updated_at_utc": None,
        "csv_schema_status": "not_evaluated",
        "jsonl_audit_status": "not_evaluated",
        "csv_jsonl_value_compare": "not_evaluated",
        "preliminary_summary_status": "not_evaluated",
        "next_action": "continue_human_review",
        "rejected_count": 0,
        "rejected_sample_ids": [],
        "active_reviewable_count": 0,
        "usable_completed_count": 0,
        "usable_pending_count": 0,
    }
    if not batch_csv.exists():
        return {
            **base,
            "status": "blocked",
            "reason": "batch_csv_missing",
            "blocking": True,
        }

    rejected_ids: set[str] = set()
    if rejected_csv is not None and rejected_csv.exists():
        r_df, _ = _safe_csv(rejected_csv)
        if r_df is not None and "sample_id" in r_df.columns:
            rejected_ids = set(r_df["sample_id"].astype(str).tolist())

    if not completed_csv.exists():
        batch_df, err = _safe_csv(batch_csv)
        if batch_df is None:
            return {
                **base,
                "status": "blocked",
                "reason": "batch_csv_unreadable",
                "error": err,
                "blocking": True,
            }
        batch_ids = batch_df["sample_id"].astype(str).tolist() if "sample_id" in batch_df.columns else []
        return {
            **base,
            "status": "awaiting_review_input",
            "batch_count": len(batch_ids),
            "completed_count": 0,
            "pending_count": len(batch_ids),
            "completion_ratio": 0.0,
            "pending_sample_ids": batch_ids,
            "rejected_count": len(rejected_ids),
            "rejected_sample_ids": sorted(rejected_ids),
            "active_reviewable_count": max(0, len(batch_ids) - len(rejected_ids)),
            "usable_completed_count": 0,
            "usable_pending_count": len([sid for sid in batch_ids if sid not in rejected_ids]),
            "reason": "completed_csv_missing",
            "blocking": False,
            "csv_schema_status": "not_applicable",
            "jsonl_audit_status": "not_applicable",
            "csv_jsonl_value_compare": "not_applicable",
            "preliminary_summary_status": "not_applicable",
            "next_action": "begin_human_review",
        }

    batch_df, batch_err = _safe_csv(batch_csv)
    completed_df, comp_err = _safe_csv(completed_csv)
    if batch_df is None:
        return {
            **base,
            "status": "blocked",
            "reason": "batch_csv_unreadable",
            "error": batch_err,
            "blocking": True,
        }
    if completed_df is None:
        return {
            **base,
            "status": "blocked",
            "reason": "completed_csv_unreadable",
            "error": comp_err,
            "blocking": True,
        }

    schema = _load_json(label_schema_json)
    allowed = schema.get("allowed_values", {}) if isinstance(schema, dict) else {}

    batch_ids = batch_df["sample_id"].astype(str).tolist() if "sample_id" in batch_df.columns else []
    batch_id_set = set(batch_ids)
    batch_count = len(batch_ids)

    forbidden_columns = [c for c in completed_df.columns if c.lower() in FORBIDDEN_TRADING_COLUMNS]
    missing_identity_fields = [c for c in REQUIRED_IDENTITY_FIELDS if c not in completed_df.columns]
    missing_review_fields = [c for c in REQUIRED_REVIEW_FIELDS if c not in completed_df.columns]

    duplicate_sample_ids = []
    completed_not_in_batch = []
    reviewed_ids: list[str] = []
    pending_ids: list[str] = []
    invalid_score_rows: list[str] = []
    invalid_enum_rows: list[str] = []

    if "sample_id" in completed_df.columns:
        counts = completed_df["sample_id"].astype(str).value_counts()
        duplicate_sample_ids = sorted([sid for sid, n in counts.items() if int(n) > 1])

    if "sample_id" in completed_df.columns and "review_status" in completed_df.columns:
        dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
        dedup["sample_id"] = dedup["sample_id"].astype(str)
        dedup["is_reviewed"] = dedup["review_status"].map(_is_reviewed)
        reviewed_ids = sorted(dedup.loc[dedup["is_reviewed"], "sample_id"].tolist())
        pending_ids = sorted([sid for sid in batch_ids if sid not in set(reviewed_ids)])
        completed_not_in_batch = sorted([sid for sid in dedup["sample_id"].tolist() if sid not in batch_id_set])
        for field in REVIEW_SCORE_FIELDS:
            if field in dedup.columns:
                vals = pd.to_numeric(dedup[field], errors="coerce")
                bad = dedup.loc[vals.isna() | (vals < 1) | (vals > 5), "sample_id"].astype(str).tolist()
                invalid_score_rows.extend(bad)
        for field in REVIEW_ENUM_FIELDS:
            if field in dedup.columns and field in allowed:
                allowed_vals = _allowed_with_legacy(schema, field)
                for _, row in dedup.iterrows():
                    if pd.isna(row[field]):
                        continue
                    if str(row[field]) not in allowed_vals:
                        invalid_enum_rows.append(str(row["sample_id"]))
    else:
        pending_ids = batch_ids

    usable_completed_ids = sorted([sid for sid in reviewed_ids if sid not in rejected_ids])
    usable_pending_ids = sorted([sid for sid in pending_ids if sid not in rejected_ids])

    latest_review_updated = None
    if "review_updated_at_utc" in completed_df.columns:
        vals = completed_df["review_updated_at_utc"].dropna().astype(str).tolist()
        latest_review_updated = max(vals) if vals else None

    jsonl_event_count = 0
    jsonl_valid_event_count = 0
    jsonl_malformed_line_count = 0
    jsonl_unique_sample_count = 0
    jsonl_unique_sample_ids: list[str] = []
    completed_without_jsonl: list[str] = []
    jsonl_without_completed: list[str] = []
    jsonl_without_batch: list[str] = []
    csv_jsonl_field_mismatches: list[dict[str, Any]] = []

    if events_jsonl.exists():
        items, malformed = _safe_jsonl(events_jsonl)
        jsonl_event_count = len(items) + len(malformed)
        jsonl_valid_event_count = len(items)
        jsonl_malformed_line_count = len(malformed)
        jsonl_unique_sample_ids = sorted({str(x.get("sample_id")) for x in items if x.get("sample_id") is not None})
        jsonl_unique_sample_count = len(jsonl_unique_sample_ids)
        reviewed_set = set(reviewed_ids)
        jsonl_set = set(jsonl_unique_sample_ids)
        completed_without_jsonl = sorted([sid for sid in reviewed_ids if sid not in jsonl_set])
        jsonl_without_completed = sorted([sid for sid in jsonl_unique_sample_ids if sid not in reviewed_set])
        jsonl_without_batch = sorted([sid for sid in jsonl_unique_sample_ids if sid not in batch_id_set])

        # Compare latest JSONL event review payload to CSV values when shape is stable.
        if "sample_id" in completed_df.columns and all(k in completed_df.columns for k in COMPARE_REVIEW_FIELDS):
            latest_by_sample: dict[str, dict[str, Any]] = {}
            for item in items:
                sid = item.get("sample_id")
                review = item.get("review")
                if sid is None or not isinstance(review, dict):
                    continue
                latest_by_sample[str(sid)] = item
            if latest_by_sample:
                dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
                dedup["sample_id"] = dedup["sample_id"].astype(str)
                for _, row in dedup.iterrows():
                    sid = str(row["sample_id"])
                    item = latest_by_sample.get(sid)
                    if not item:
                        continue
                    review = item.get("review", {})
                    mismatch_fields = []
                    for field in COMPARE_REVIEW_FIELDS:
                        lhs = _norm(row.get(field))
                        rhs = _norm(review.get(field))
                        if lhs != rhs:
                            mismatch_fields.append(field)
                    if mismatch_fields:
                        csv_jsonl_field_mismatches.append({"sample_id": sid, "fields": mismatch_fields})
                csv_jsonl_value_compare = "warning_mismatch" if csv_jsonl_field_mismatches else "matched_latest_event"
            else:
                csv_jsonl_value_compare = "skipped_payload_shape_not_stable"
        else:
            csv_jsonl_value_compare = "skipped_payload_shape_not_stable"
    else:
        csv_jsonl_value_compare = "warning_events_jsonl_missing"

    reviewed_df = pd.DataFrame()
    if "sample_id" in completed_df.columns and "review_status" in completed_df.columns:
        dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
        reviewed_df = dedup[dedup["review_status"].map(_is_reviewed)].copy()

    def _dist(series: pd.Series) -> dict[str, int]:
        if series.empty:
            return {}
        counts = series.fillna("<NA>").astype(str).value_counts()
        return {str(k): int(v) for k, v in counts.items()}

    completed_type_dist = _dist(reviewed_df["candidate_type"]) if "candidate_type" in reviewed_df.columns else {}
    pending_df = batch_df[~batch_df["sample_id"].astype(str).isin(set(reviewed_ids))].copy() if "sample_id" in batch_df.columns else batch_df.iloc[0:0].copy()
    pending_type_dist = _dist(pending_df["candidate_type"]) if "candidate_type" in pending_df.columns else {}

    reviewed_ts = pd.to_datetime(reviewed_df.get("timestamp", pd.Series([], dtype=str)), utc=True, errors="coerce")
    pending_ts = pd.to_datetime(pending_df.get("timestamp", pd.Series([], dtype=str)), utc=True, errors="coerce")
    completed_unique_days = int(reviewed_ts.dropna().dt.strftime("%Y-%m-%d").nunique()) if not reviewed_ts.empty else 0
    pending_unique_days = int(pending_ts.dropna().dt.strftime("%Y-%m-%d").nunique()) if not pending_ts.empty else 0

    coverage_status = "ok"
    if len(reviewed_ids) > 0 and (len(completed_type_dist) < 2 or completed_unique_days < 2):
        coverage_status = "watch"

    note_vals = reviewed_df.get("review_notes", pd.Series([], dtype=str)).fillna("").astype(str).tolist()
    nonblank_notes = [x for x in note_vals if x.strip()]

    completed_count = len(reviewed_ids)
    pending_count = max(0, batch_count - completed_count)
    completion_ratio = (completed_count / batch_count) if batch_count else 0.0
    active_reviewable_count = max(0, batch_count - len(rejected_ids))
    usable_completion_ratio = (len(usable_completed_ids) / active_reviewable_count) if active_reviewable_count else 0.0

    csv_schema_status = "valid"
    if missing_identity_fields or missing_review_fields or forbidden_columns or duplicate_sample_ids or completed_not_in_batch:
        csv_schema_status = "blocked"
    elif invalid_score_rows or invalid_enum_rows:
        csv_schema_status = "warning"

    jsonl_audit_status = "valid"
    if jsonl_malformed_line_count > 0:
        jsonl_audit_status = "warning"
    if not events_jsonl.exists():
        jsonl_audit_status = "warning"

    status = "valid_in_progress"
    blocking = False
    if csv_schema_status == "blocked":
        status = "blocked"
        blocking = True
    elif len(usable_completed_ids) >= active_reviewable_count and active_reviewable_count > 0:
        status = "valid_ready_for_summary"
    elif jsonl_audit_status == "warning" or jsonl_without_batch or completed_without_jsonl or jsonl_without_completed:
        status = "warning"

    next_action = "continue_human_review" if status != "valid_ready_for_summary" else "run_full_review_summary"

    return {
        **base,
        "status": status,
        "blocking": blocking,
        "reason": None,
        "batch_count": batch_count,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "completion_ratio": completion_ratio,
        "completed_sample_ids": reviewed_ids,
        "pending_sample_ids": pending_ids,
        "rejected_count": int(len(rejected_ids)),
        "rejected_sample_ids": sorted(rejected_ids),
        "active_reviewable_count": int(active_reviewable_count),
        "usable_completed_count": int(len(usable_completed_ids)),
        "usable_pending_count": int(len(usable_pending_ids)),
        "usable_completion_ratio": usable_completion_ratio,
        "latest_review_updated_at_utc": latest_review_updated,
        "next_action": next_action,
        "csv_schema_status": csv_schema_status,
        "jsonl_audit_status": jsonl_audit_status,
        "preliminary_summary_status": "ready" if completed_count > 0 else "awaiting_review_input",
        "forbidden_columns_detected": forbidden_columns,
        "missing_identity_fields": missing_identity_fields,
        "missing_review_fields": missing_review_fields,
        "duplicate_sample_ids": duplicate_sample_ids,
        "completed_samples_not_in_batch": completed_not_in_batch,
        "invalid_score_rows": sorted(set(invalid_score_rows)),
        "invalid_enum_rows": sorted(set(invalid_enum_rows)),
        "jsonl_event_count": jsonl_event_count,
        "jsonl_valid_event_count": jsonl_valid_event_count,
        "jsonl_malformed_line_count": jsonl_malformed_line_count,
        "jsonl_unique_sample_count": jsonl_unique_sample_count,
        "completed_without_jsonl": completed_without_jsonl,
        "jsonl_without_completed": jsonl_without_completed,
        "jsonl_without_batch": jsonl_without_batch,
        "csv_jsonl_value_compare": csv_jsonl_value_compare,
        "csv_jsonl_field_mismatches": csv_jsonl_field_mismatches,
        "reviewed_candidate_type_distribution": completed_type_dist,
        "pending_candidate_type_distribution": pending_type_dist,
        "completed_unique_days": completed_unique_days,
        "pending_unique_days": pending_unique_days,
        "completed_first_timestamp": str(reviewed_ts.dropna().min()) if not reviewed_ts.dropna().empty else None,
        "completed_last_timestamp": str(reviewed_ts.dropna().max()) if not reviewed_ts.dropna().empty else None,
        "pending_first_timestamp": str(pending_ts.dropna().min()) if not pending_ts.dropna().empty else None,
        "pending_last_timestamp": str(pending_ts.dropna().max()) if not pending_ts.dropna().empty else None,
        "coverage_status": coverage_status,
        "blank_notes_count": len(note_vals) - len(nonblank_notes),
        "nonblank_notes_count": len(nonblank_notes),
        "review_note_keyword_counts": _keyword_counts(nonblank_notes),
    }


def render_completed_review_progress_markdown(payload: dict[str, Any]) -> str:
    fresh_start_note = []
    if payload.get("status") == "awaiting_review_input":
        fresh_start_note = [
            "",
            "## Fresh Start",
            "",
            "- CSV schema: `not_applicable` (no completed review rows yet)",
            "- JSONL audit: `not_applicable` (no review events yet)",
            "- Next action: `begin_human_review`",
        ]
    lines = [
        "# EURUSD Completed Review Progress",
        "",
        f"- status: `{payload.get('status')}`",
        f"- blocking: `{payload.get('blocking')}`",
        f"- batch_count: `{payload.get('batch_count')}`",
        f"- completed_count: `{payload.get('completed_count')}`",
        f"- pending_count: `{payload.get('pending_count')}`",
        f"- completion_ratio: `{payload.get('completion_ratio')}`",
        f"- latest_review_updated_at_utc: `{payload.get('latest_review_updated_at_utc')}`",
        f"- csv_schema_status: `{payload.get('csv_schema_status')}`",
        f"- jsonl_audit_status: `{payload.get('jsonl_audit_status')}`",
        f"- csv_jsonl_value_compare: `{payload.get('csv_jsonl_value_compare')}`",
        f"- coverage_status: `{payload.get('coverage_status')}`",
        f"- next_action: `{payload.get('next_action')}`",
        "",
        "## Coverage",
        "",
        f"- completed_unique_days: `{payload.get('completed_unique_days')}`",
        f"- pending_unique_days: `{payload.get('pending_unique_days')}`",
        f"- completed_first_timestamp: `{payload.get('completed_first_timestamp')}`",
        f"- completed_last_timestamp: `{payload.get('completed_last_timestamp')}`",
        f"- pending_first_timestamp: `{payload.get('pending_first_timestamp')}`",
        f"- pending_last_timestamp: `{payload.get('pending_last_timestamp')}`",
        "",
        "## Audit",
        "",
        f"- duplicate_sample_ids: `{payload.get('duplicate_sample_ids')}`",
        f"- completed_samples_not_in_batch: `{payload.get('completed_samples_not_in_batch')}`",
        f"- invalid_score_rows: `{payload.get('invalid_score_rows')}`",
        f"- invalid_enum_rows: `{payload.get('invalid_enum_rows')}`",
        f"- jsonl_malformed_line_count: `{payload.get('jsonl_malformed_line_count')}`",
        f"- completed_without_jsonl: `{payload.get('completed_without_jsonl')}`",
        f"- jsonl_without_completed: `{payload.get('jsonl_without_completed')}`",
        f"- jsonl_without_batch: `{payload.get('jsonl_without_batch')}`",
    ]
    return "\n".join(lines + fresh_start_note) + "\n"
