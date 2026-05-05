"""EURUSD human review quality completeness report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_ZH_FIELDS = [
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]
REQUIRED_COMPLETED_ENGLISH_KEYS = [
    "sample_id",
    "human_label",
    "human_confidence",
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]
LIVE_LLM_MARKERS = ["openai", "anthropic", "gemini", "cohere", "api_key", "responses.create"]


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


def _coverage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _has_non_ascii_key(columns: list[str]) -> bool:
    return any(any(ord(ch) > 127 for ch in col) for col in columns)


def _approval_status_from_template(path: Path) -> str:
    if not path.exists():
        return "not_approved"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return str(payload.get("approval_status", "not_approved"))
    except Exception:
        return "not_approved"


def _contains_live_llm_markers(columns: list[str]) -> bool:
    hay = " ".join(columns).lower()
    return any(marker in hay for marker in LIVE_LLM_MARKERS)


def build_human_review_quality_report(
    *,
    batch_csv: Path,
    completed_csv: Path,
    approval_json: Path = Path("cajas/data_examples/eurusd_real_llm_integration_approval.template.json"),
) -> dict[str, Any]:
    trial_approval_status = _approval_status_from_template(approval_json)
    real_llm_integration_approved = trial_approval_status == "approved"

    if not batch_csv.exists():
        return {
            "report_status": "blocked",
            "status_reason": "batch_csv_missing",
            "completed_review_csv_exists": completed_csv.exists(),
            "has_active_batch_or_template": False,
            "real_llm_integration_approved": real_llm_integration_approved,
            "trial_approval_status": trial_approval_status,
        }

    batch_df = pd.read_csv(batch_csv)
    has_active_batch_or_template = int(len(batch_df)) > 0

    if not completed_csv.exists():
        return {
            "report_status": "awaiting_review_input",
            "status_reason": "completed_csv_missing_review_input_awaited",
            "completed_review_csv_exists": False,
            "has_active_batch_or_template": has_active_batch_or_template,
            "total_samples": int(len(batch_df)),
            "reviewed_samples": 0,
            "label_coverage": 0.0,
            "confidence_coverage": 0.0,
            "rationale_coverage": 0.0,
            "counterexample_coverage": 0.0,
            "uncertainty_reason_coverage": 0.0,
            "context_notes_coverage": 0.0,
            "label_without_rationale_count": 0,
            "uncertain_without_uncertainty_reason_count": 0,
            "high_confidence_without_rationale_count": 0,
            "missing_standard_version_count": 0,
            "real_llm_integration_approved": real_llm_integration_approved,
            "trial_approval_status": trial_approval_status,
        }

    try:
        completed_df = pd.read_csv(completed_csv)
    except Exception as exc:
        return {
            "report_status": "blocked",
            "status_reason": f"completed_csv_read_error:{exc}",
            "completed_review_csv_exists": True,
            "has_active_batch_or_template": has_active_batch_or_template,
            "real_llm_integration_approved": real_llm_integration_approved,
            "trial_approval_status": trial_approval_status,
        }

    columns = [str(x) for x in completed_df.columns.tolist()]
    missing_keys = [k for k in REQUIRED_COMPLETED_ENGLISH_KEYS if k not in columns]
    if missing_keys:
        return {
            "report_status": "blocked",
            "status_reason": f"missing_required_english_keys:{','.join(missing_keys)}",
            "completed_review_csv_exists": True,
            "has_active_batch_or_template": has_active_batch_or_template,
            "real_llm_integration_approved": real_llm_integration_approved,
            "trial_approval_status": trial_approval_status,
        }
    if _has_non_ascii_key(columns):
        return {
            "report_status": "blocked",
            "status_reason": "non_english_schema_keys_detected",
            "completed_review_csv_exists": True,
            "has_active_batch_or_template": has_active_batch_or_template,
            "real_llm_integration_approved": real_llm_integration_approved,
            "trial_approval_status": trial_approval_status,
        }
    if _contains_live_llm_markers(columns):
        return {
            "report_status": "blocked",
            "status_reason": "live_llm_provider_markers_detected",
            "completed_review_csv_exists": True,
            "has_active_batch_or_template": has_active_batch_or_template,
            "real_llm_integration_approved": real_llm_integration_approved,
            "trial_approval_status": trial_approval_status,
        }

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

    if "standard_version" in reviewed.columns:
        missing_standard_version_count = int((_as_text(reviewed["standard_version"]) == "").sum())
    else:
        missing_standard_version_count = reviewed_samples

    report_status = "human_review_quality_ready"
    reasons: list[str] = []
    if reviewed_samples == 0:
        report_status = "awaiting_review_input"
        reasons.append("no_reviewed_samples_yet")
    elif (
        label_no_rationale > 0
        or uncertain_missing_reason > 0
        or high_confidence_empty_rationale > 0
        or missing_standard_version_count > 0
    ):
        report_status = "human_review_quality_watch"
        if label_no_rationale > 0:
            reasons.append("label_without_rationale_detected")
        if uncertain_missing_reason > 0:
            reasons.append("uncertain_missing_uncertainty_reason_detected")
        if high_confidence_empty_rationale > 0:
            reasons.append("high_confidence_without_rationale_detected")
        if missing_standard_version_count > 0:
            reasons.append("missing_standard_version_detected")

    return {
        "report_status": report_status,
        "status_reason": ";".join(reasons) if reasons else "quality_thresholds_passed",
        "completed_review_csv_exists": True,
        "has_active_batch_or_template": has_active_batch_or_template,
        "total_samples": total_samples,
        "reviewed_samples": reviewed_samples,
        "label_coverage": _coverage(human_label_count, reviewed_samples),
        "confidence_coverage": _coverage(human_confidence_count, reviewed_samples),
        "rationale_coverage": _coverage(rationale_count, reviewed_samples),
        "counterexample_coverage": _coverage(counterexample_count, reviewed_samples),
        "uncertainty_reason_coverage": _coverage(uncertainty_reason_count, reviewed_samples),
        "context_notes_coverage": _coverage(context_notes_count, reviewed_samples),
        "label_without_rationale_count": label_no_rationale,
        "uncertain_without_uncertainty_reason_count": uncertain_missing_reason,
        "high_confidence_without_rationale_count": high_confidence_empty_rationale,
        "missing_standard_version_count": missing_standard_version_count,
        "standard_version": "eurusd_15m_review_standard_v0",
        "real_llm_integration_approved": real_llm_integration_approved,
        "trial_approval_status": trial_approval_status,
        "per_candidate_type_completeness": {
            "human_label": _count_per_candidate(reviewed, "human_label"),
            "human_confidence": _count_per_candidate(reviewed, "human_confidence"),
            "human_rationale_zh": _count_per_candidate(reviewed, "human_rationale_zh"),
            "human_counterexample_zh": _count_per_candidate(reviewed, "human_counterexample_zh"),
            "human_uncertainty_reason_zh": _count_per_candidate(reviewed, "human_uncertainty_reason_zh"),
            "human_context_notes_zh": _count_per_candidate(reviewed, "human_context_notes_zh"),
        },
        "missing_required_zh_fields": [f for f in REQUIRED_ZH_FIELDS if f not in columns],
    }


def render_human_review_quality_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Human Review Quality",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- status_reason: `{report.get('status_reason')}`",
        f"- completed_review_csv_exists: `{report.get('completed_review_csv_exists')}`",
        f"- has_active_batch_or_template: `{report.get('has_active_batch_or_template')}`",
        f"- real_llm_integration_approved: `{report.get('real_llm_integration_approved')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        f"- total_samples: `{report.get('total_samples')}`",
        f"- reviewed_samples: `{report.get('reviewed_samples')}`",
        "",
        "## Completeness",
        "",
        f"- label_coverage: `{report.get('label_coverage')}`",
        f"- confidence_coverage: `{report.get('confidence_coverage')}`",
        f"- rationale_coverage: `{report.get('rationale_coverage')}`",
        f"- counterexample_coverage: `{report.get('counterexample_coverage')}`",
        f"- uncertainty_reason_coverage: `{report.get('uncertainty_reason_coverage')}`",
        f"- context_notes_coverage: `{report.get('context_notes_coverage')}`",
        "",
        "## Quality Alerts",
        "",
        f"- label_without_rationale_count: `{report.get('label_without_rationale_count')}`",
        f"- uncertain_without_uncertainty_reason_count: `{report.get('uncertain_without_uncertainty_reason_count')}`",
        f"- high_confidence_without_rationale_count: `{report.get('high_confidence_without_rationale_count')}`",
        f"- missing_standard_version_count: `{report.get('missing_standard_version_count')}`",
        "",
        "## Notes",
        "",
        "- Missing completed review CSV is not a blocker; it indicates review input is still awaited.",
        "- Real LLM integration remains unapproved in the current phase.",
        "- Trial approval remains `not_approved` unless explicit approval artifact changes.",
    ]
    return "\n".join(lines) + "\n"
