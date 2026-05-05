"""Deterministic EURUSD human review quality feedback report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _txt(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _dist(series: pd.Series) -> dict[str, int]:
    if series.empty:
        return {}
    vc = series.fillna("<NA>").astype(str).value_counts()
    return {str(k): int(v) for k, v in vc.items()}


def build_human_review_feedback_report(*, completed_csv: Path) -> dict[str, Any]:
    if not completed_csv.exists():
        return {
            "report_status": "awaiting_review_data",
            "reason": "completed_csv_missing",
            "completed_csv_path": str(completed_csv),
        }
    try:
        df = pd.read_csv(completed_csv)
    except Exception as exc:
        return {
            "report_status": "blocked",
            "reason": f"completed_csv_unreadable:{exc}",
            "completed_csv_path": str(completed_csv),
        }

    required = [
        "sample_id",
        "candidate_type",
        "human_label",
        "human_confidence",
        "human_rationale_zh",
        "human_uncertainty_reason_zh",
        "review_updated_at_utc",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {
            "report_status": "blocked",
            "reason": f"missing_required_fields:{','.join(missing)}",
            "completed_csv_path": str(completed_csv),
        }

    dedup = df.drop_duplicates(subset=["sample_id"], keep="last").copy()
    reviewed = dedup[_txt(dedup["review_updated_at_utc"]) != ""].copy()
    if reviewed.empty:
        return {
            "report_status": "awaiting_review_data",
            "reason": "no_reviewed_rows",
            "completed_csv_path": str(completed_csv),
            "reviewed_sample_count": 0,
        }

    label = _txt(reviewed["human_label"])
    conf = _txt(reviewed["human_confidence"])
    rationale = _txt(reviewed["human_rationale_zh"])
    uncertainty = _txt(reviewed.get("human_uncertainty_reason_zh", pd.Series([""] * len(reviewed), index=reviewed.index)))

    missing_rationale_count = int((rationale == "").sum())
    uncertain_missing_reason_count = int(((label == "unclear") & (uncertainty == "")).sum())
    high_conf_missing_rationale_count = int(((conf == "high") & (rationale == "")).sum())

    suitable_for_standard = reviewed[(rationale != "") & conf.isin(["high", "medium"])].copy()
    follow_up = reviewed[(label == "unclear") | (conf == "low") | (rationale == "")].copy()

    recurring: list[str] = []
    if missing_rationale_count > 0:
        recurring.append("missing_rationale")
    if uncertain_missing_reason_count > 0:
        recurring.append("uncertain_without_uncertainty_reason")
    if high_conf_missing_rationale_count > 0:
        recurring.append("high_confidence_without_rationale")

    focus = []
    if uncertain_missing_reason_count > 0:
        focus.append("Fill uncertainty reasons for unclear labels")
    if high_conf_missing_rationale_count > 0:
        focus.append("Add concrete rationale for high-confidence decisions")
    if not focus:
        focus.append("Continue 10-20 sample batches and expand candidate-type coverage")

    return {
        "report_status": "feedback_ready",
        "completed_csv_path": str(completed_csv),
        "reviewed_sample_count": int(len(reviewed)),
        "label_distribution": _dist(label),
        "confidence_distribution": _dist(conf),
        "candidate_type_distribution": _dist(_txt(reviewed["candidate_type"])),
        "missing_rationale_count": missing_rationale_count,
        "uncertain_without_uncertainty_reason_count": uncertain_missing_reason_count,
        "high_confidence_without_rationale_count": high_conf_missing_rationale_count,
        "samples_suitable_for_standard_examples": int(len(suitable_for_standard)),
        "samples_needing_follow_up_review": int(len(follow_up)),
        "recurring_review_quality_issues": recurring,
        "next_recommended_manual_review_focus": focus,
    }


def render_human_review_feedback_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Human Review Feedback",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- reviewed_sample_count: `{report.get('reviewed_sample_count')}`",
        f"- samples_suitable_for_standard_examples: `{report.get('samples_suitable_for_standard_examples')}`",
        f"- samples_needing_follow_up_review: `{report.get('samples_needing_follow_up_review')}`",
        "",
        "## Distributions",
        "",
        f"- label_distribution: `{report.get('label_distribution')}`",
        f"- confidence_distribution: `{report.get('confidence_distribution')}`",
        f"- candidate_type_distribution: `{report.get('candidate_type_distribution')}`",
        "",
        "## Quality Gaps",
        "",
        f"- missing_rationale_count: `{report.get('missing_rationale_count')}`",
        f"- uncertain_without_uncertainty_reason_count: `{report.get('uncertain_without_uncertainty_reason_count')}`",
        f"- high_confidence_without_rationale_count: `{report.get('high_confidence_without_rationale_count')}`",
        f"- recurring_review_quality_issues: `{report.get('recurring_review_quality_issues')}`",
        "",
        "## Next Focus",
        "",
    ]
    for item in report.get("next_recommended_manual_review_focus", []) or []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
