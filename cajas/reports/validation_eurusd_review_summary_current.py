"""EURUSD current reviewed-only summary report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from cajas.reports.validation_eurusd_completed_review_progress import _is_reviewed, _keyword_counts


def _dist(series: pd.Series) -> dict[str, int]:
    if series.empty:
        return {}
    counts = series.fillna("<NA>").astype(str).value_counts()
    return {str(k): int(v) for k, v in counts.items()}


def _score_summary(series: pd.Series) -> dict[str, Any]:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "count": int(vals.count()),
        "mean": float(vals.mean()),
        "median": float(vals.median()),
        "min": float(vals.min()),
        "max": float(vals.max()),
    }


def build_review_summary_current_report(*, batch_csv: Path, completed_csv: Path) -> dict[str, Any]:
    if not batch_csv.exists():
        return {"status": "blocked", "reason": "batch_csv_missing"}
    if not completed_csv.exists():
        return {"status": "awaiting_review_input", "reason": "completed_csv_missing"}

    batch_df = pd.read_csv(batch_csv)
    completed_df = pd.read_csv(completed_csv)
    if "sample_id" not in completed_df.columns:
        return {"status": "blocked", "reason": "completed_csv_missing_sample_id"}

    dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
    if "review_status" in dedup.columns:
        reviewed_df = dedup[dedup["review_status"].map(_is_reviewed)].copy()
    else:
        reviewed_df = dedup.iloc[0:0].copy()

    pending_df = batch_df[~batch_df["sample_id"].astype(str).isin(set(reviewed_df["sample_id"].astype(str).tolist()))].copy() if "sample_id" in batch_df.columns else batch_df.iloc[0:0].copy()

    note_values = reviewed_df.get("review_notes", pd.Series([], dtype=str)).fillna("").astype(str).tolist()
    nonblank_notes = [x for x in note_values if x.strip()]

    reviewed_count = int(len(reviewed_df))
    status = "ready" if reviewed_count > 0 else "awaiting_review_input"

    return {
        "status": status,
        "reviewed_count": reviewed_count,
        "pending_count": int(len(pending_df)),
        "counts_by_candidate_type": _dist(reviewed_df.get("candidate_type", pd.Series([], dtype=str))),
        "counts_by_pattern_label": _dist(reviewed_df.get("human_pattern_label", pd.Series([], dtype=str))),
        "counts_by_market_context": _dist(reviewed_df.get("market_context", pd.Series([], dtype=str))),
        "counts_by_direction_context": _dist(reviewed_df.get("direction_context", pd.Series([], dtype=str))),
        "counts_by_review_status": _dist(reviewed_df.get("review_status", pd.Series([], dtype=str))),
        "structure_quality_summary": _score_summary(reviewed_df.get("structure_quality", pd.Series([], dtype=float))),
        "follow_through_quality_summary": _score_summary(reviewed_df.get("follow_through_quality", pd.Series([], dtype=float))),
        "review_confidence_summary": _score_summary(reviewed_df.get("review_confidence", pd.Series([], dtype=float))),
        "blank_notes_count": int(len(note_values) - len(nonblank_notes)),
        "nonblank_notes_count": int(len(nonblank_notes)),
        "review_note_keyword_counts": _keyword_counts(nonblank_notes),
        "completed_candidate_type_distribution": _dist(reviewed_df.get("candidate_type", pd.Series([], dtype=str))),
        "pending_candidate_type_distribution": _dist(pending_df.get("candidate_type", pd.Series([], dtype=str))),
        "completed_unique_days": int(pd.to_datetime(reviewed_df.get("timestamp", pd.Series([], dtype=str)), utc=True, errors="coerce").dropna().dt.strftime("%Y-%m-%d").nunique()) if not reviewed_df.empty else 0,
        "pending_unique_days": int(pd.to_datetime(pending_df.get("timestamp", pd.Series([], dtype=str)), utc=True, errors="coerce").dropna().dt.strftime("%Y-%m-%d").nunique()) if not pending_df.empty else 0,
    }


def render_review_summary_current_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EURUSD Review Summary (Current)",
            "",
            f"- status: `{payload.get('status')}`",
            f"- reviewed_count: `{payload.get('reviewed_count')}`",
            f"- pending_count: `{payload.get('pending_count')}`",
            f"- blank_notes_count: `{payload.get('blank_notes_count')}`",
            f"- nonblank_notes_count: `{payload.get('nonblank_notes_count')}`",
            "",
            "## Distributions",
            "",
            f"- counts_by_candidate_type: `{payload.get('counts_by_candidate_type')}`",
            f"- counts_by_pattern_label: `{payload.get('counts_by_pattern_label')}`",
            f"- counts_by_market_context: `{payload.get('counts_by_market_context')}`",
            f"- counts_by_direction_context: `{payload.get('counts_by_direction_context')}`",
            f"- counts_by_review_status: `{payload.get('counts_by_review_status')}`",
            "",
            "## Scores",
            "",
            f"- structure_quality_summary: `{payload.get('structure_quality_summary')}`",
            f"- follow_through_quality_summary: `{payload.get('follow_through_quality_summary')}`",
            f"- review_confidence_summary: `{payload.get('review_confidence_summary')}`",
            "",
            f"- review_note_keyword_counts: `{payload.get('review_note_keyword_counts')}`",
        ]
    ) + "\n"
