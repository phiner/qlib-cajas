"""EURUSD human review quality completeness report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_ZH_FIELDS = [
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]


def _as_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _non_empty_count(df: pd.DataFrame, field: str) -> int:
    if field not in df.columns:
        return 0
    return int((_as_text(df[field]) != "").sum())


def _is_reviewed(df: pd.DataFrame) -> pd.Series:
    if "review_updated_at_utc" in df.columns:
        return _as_text(df["review_updated_at_utc"]) != ""
    return pd.Series([False] * len(df), index=df.index)


def _count_per_candidate(df: pd.DataFrame, field: str) -> dict[str, int]:
    if "candidate_type" not in df.columns or field not in df.columns:
        return {}
    out: dict[str, int] = {}
    for ctype, group in df.groupby(df["candidate_type"].fillna("<NA>").astype(str)):
        out[str(ctype)] = int((_as_text(group[field]) != "").sum())
    return out


def build_human_review_quality_report(*, batch_csv: Path, completed_csv: Path) -> dict[str, Any]:
    if not batch_csv.exists():
        return {"status": "blocked", "reason": "batch_csv_missing", "batch_csv": str(batch_csv)}
    if not completed_csv.exists():
        return {
            "status": "blocked",
            "reason": "completed_csv_missing",
            "batch_csv": str(batch_csv),
            "completed_csv": str(completed_csv),
        }

    batch_df = pd.read_csv(batch_csv)
    completed_df = pd.read_csv(completed_csv)
    if "sample_id" not in completed_df.columns:
        return {"status": "blocked", "reason": "completed_csv_missing_sample_id"}

    dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
    reviewed = dedup[_is_reviewed(dedup)].copy()

    total_samples = int(len(batch_df))
    reviewed_samples = int(len(reviewed))

    human_label_count = _non_empty_count(reviewed, "human_label")
    human_confidence_count = _non_empty_count(reviewed, "human_confidence")
    rationale_count = _non_empty_count(reviewed, "human_rationale_zh")
    counterexample_count = _non_empty_count(reviewed, "human_counterexample_zh")
    uncertainty_reason_count = _non_empty_count(reviewed, "human_uncertainty_reason_zh")
    context_notes_count = _non_empty_count(reviewed, "human_context_notes_zh")

    label_no_rationale = 0
    uncertain_missing_reason = 0
    high_confidence_empty_rationale = 0
    if reviewed_samples > 0:
        human_label = _as_text(reviewed.get("human_label", pd.Series([""] * len(reviewed), index=reviewed.index)))
        human_confidence = _as_text(reviewed.get("human_confidence", pd.Series([""] * len(reviewed), index=reviewed.index)))
        rationale = _as_text(reviewed.get("human_rationale_zh", pd.Series([""] * len(reviewed), index=reviewed.index)))
        uncertainty_reason = _as_text(reviewed.get("human_uncertainty_reason_zh", pd.Series([""] * len(reviewed), index=reviewed.index)))

        label_no_rationale = int(((human_label != "") & (human_label != "not_reviewed") & (rationale == "")).sum())
        uncertain_missing_reason = int(((human_label == "unclear") & (uncertainty_reason == "")).sum())
        high_confidence_empty_rationale = int(((human_confidence == "high") & (rationale == "")).sum())

    status = "human_review_quality_ready"
    reasons: list[str] = []
    if reviewed_samples == 0:
        status = "blocked"
        reasons.append("no_reviewed_samples")
    else:
        if label_no_rationale > 0 or uncertain_missing_reason > 0 or high_confidence_empty_rationale > 0:
            status = "human_review_quality_watch"
            if label_no_rationale > 0:
                reasons.append("label_without_rationale_detected")
            if uncertain_missing_reason > 0:
                reasons.append("uncertain_missing_uncertainty_reason_detected")
            if high_confidence_empty_rationale > 0:
                reasons.append("high_confidence_without_rationale_detected")

    return {
        "status": status,
        "standard_version": "eurusd_15m_review_standard_v0",
        "total_samples": total_samples,
        "reviewed_samples": reviewed_samples,
        "samples_with_human_label": human_label_count,
        "samples_with_human_confidence": human_confidence_count,
        "samples_with_human_rationale_zh": rationale_count,
        "samples_with_human_counterexample_zh": counterexample_count,
        "samples_with_human_uncertainty_reason_zh": uncertainty_reason_count,
        "samples_with_human_context_notes_zh": context_notes_count,
        "samples_with_label_but_no_rationale": label_no_rationale,
        "samples_uncertain_but_missing_uncertainty_reason": uncertain_missing_reason,
        "samples_high_confidence_but_empty_rationale": high_confidence_empty_rationale,
        "per_candidate_type_completeness": {
            "human_label": _count_per_candidate(reviewed, "human_label"),
            "human_confidence": _count_per_candidate(reviewed, "human_confidence"),
            "human_rationale_zh": _count_per_candidate(reviewed, "human_rationale_zh"),
            "human_counterexample_zh": _count_per_candidate(reviewed, "human_counterexample_zh"),
            "human_uncertainty_reason_zh": _count_per_candidate(reviewed, "human_uncertainty_reason_zh"),
            "human_context_notes_zh": _count_per_candidate(reviewed, "human_context_notes_zh"),
        },
        "missing_required_zh_fields": [f for f in REQUIRED_ZH_FIELDS if f not in dedup.columns],
        "reasons": reasons,
    }


def render_human_review_quality_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Human Review Quality",
        "",
        f"- status: `{report.get('status')}`",
        f"- standard_version: `{report.get('standard_version')}`",
        f"- total_samples: `{report.get('total_samples')}`",
        f"- reviewed_samples: `{report.get('reviewed_samples')}`",
        "",
        "## Completeness",
        "",
        f"- samples_with_human_label: `{report.get('samples_with_human_label')}`",
        f"- samples_with_human_confidence: `{report.get('samples_with_human_confidence')}`",
        f"- samples_with_human_rationale_zh: `{report.get('samples_with_human_rationale_zh')}`",
        f"- samples_with_human_counterexample_zh: `{report.get('samples_with_human_counterexample_zh')}`",
        f"- samples_with_human_uncertainty_reason_zh: `{report.get('samples_with_human_uncertainty_reason_zh')}`",
        f"- samples_with_human_context_notes_zh: `{report.get('samples_with_human_context_notes_zh')}`",
        "",
        "## Quality Alerts",
        "",
        f"- samples_with_label_but_no_rationale: `{report.get('samples_with_label_but_no_rationale')}`",
        f"- samples_uncertain_but_missing_uncertainty_reason: `{report.get('samples_uncertain_but_missing_uncertainty_reason')}`",
        f"- samples_high_confidence_but_empty_rationale: `{report.get('samples_high_confidence_but_empty_rationale')}`",
        "",
        f"- reasons: `{report.get('reasons')}`",
    ]
    return "\n".join(lines) + "\n"
