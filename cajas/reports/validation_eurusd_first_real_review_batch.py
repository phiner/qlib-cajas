"""Validate first real EURUSD unified review batch status and coverage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

SMOKE_SAMPLE_IDS = {
    "eurusd15m_000028",
    "eurusd15m_000068",
    "eurusd15m_000124",
}
REQUIRED_FIELDS = [
    "sample_id",
    "review_updated_at_utc",
    "human_label",
    "human_confidence",
    "human_rationale_zh",
]
LAYER_FIELDS = [
    "human_pattern_3_feedback_zh",
    "human_market_8_feedback_zh",
    "human_market_24_feedback_zh",
    "human_market_128_feedback_zh",
    "human_local_structure_feedback_zh",
]
LIVE_LLM_MARKERS = ["openai", "anthropic", "gemini", "cohere", "api_key", "responses.create"]


def _txt(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    if not path.exists():
        return rows, issues
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            issues.append(f"invalid_jsonl_line:{i}")
            continue
        if not isinstance(row, dict):
            issues.append(f"non_object_jsonl_line:{i}")
            continue
        rows.append(row)
    return rows, issues


def _contains_non_ascii_key(cols: list[str]) -> bool:
    return any(any(ord(ch) > 127 for ch in c) for c in cols)


def _has_live_llm_markers(cols: list[str]) -> bool:
    joined = " ".join(cols).lower()
    return any(marker in joined for marker in LIVE_LLM_MARKERS)


def _dist(series: pd.Series) -> dict[str, int]:
    if series.empty:
        return {}
    return {str(k): int(v) for k, v in _txt(series).value_counts().items() if str(k) != ""}


def _coverage(non_empty: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return float(non_empty) / float(total)


def _count_non_empty(df: pd.DataFrame, field: str) -> int:
    if field not in df.columns:
        return 0
    values = _txt(df[field])
    return int(((values != "") & (values != "not_reviewed")).sum())


def _has_any_layer_feedback(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series([False] * len(df), index=df.index)
    for field in LAYER_FIELDS:
        if field in df.columns:
            values = _txt(df[field])
            mask = mask | ((values != "") & (values != "not_reviewed") & (values != "nan"))
    return mask


def build_first_real_review_batch_report(
    *,
    completed_csv: Path,
    review_events_jsonl: Path,
    llm_artifact_jsonl: Path,
    human_review_quality_json: Path,
    llm_artifact_report_json: Path,
    trial_approval_json: Path,
    minimum_total_reviewed: int = 10,
    minimum_new_since_smoke: int = 7,
    minimum_layer_feedback_ratio: float = 0.8,
) -> dict[str, Any]:
    quality = _load_json(human_review_quality_json) or {}
    artifact_report = _load_json(llm_artifact_report_json) or {}
    trial = _load_json(trial_approval_json) or {}
    trial_status = str(trial.get("approval_status", trial.get("trial_approval_status", "not_approved")))

    base: dict[str, Any] = {
        "report_status": "awaiting_real_review_batch",
        "reviewed_sample_count": 0,
        "new_reviewed_sample_count_since_smoke": 0,
        "reviewed_sample_ids": [],
        "candidate_type_distribution": {},
        "human_label_distribution": {},
        "human_confidence_distribution": {},
        "overall_rationale_coverage": 0.0,
        "uncertainty_reason_coverage": 0.0,
        "counterexample_coverage": 0.0,
        "context_notes_coverage": 0.0,
        "p3_feedback_coverage": 0.0,
        "m8_feedback_coverage": 0.0,
        "m24_feedback_coverage": 0.0,
        "m128_feedback_coverage": 0.0,
        "local_feedback_coverage": 0.0,
        "samples_with_overall_but_no_layer_evidence": 0,
        "samples_with_layer_evidence_but_no_overall_label": 0,
        "standard_version_coverage": 0.0,
        "jsonl_event_count": 0,
        "llm_artifact_contains_multi_layer_evidence": False,
        "human_review_quality_status": str(quality.get("report_status", "unknown")),
        "llm_artifact_status": str(artifact_report.get("report_status", "unknown")),
        "trial_approval_status": trial_status,
        "real_llm_integration_approved": False,
        "blocking_reasons": [],
    }

    if trial_status != "not_approved":
        base["report_status"] = "blocked"
        base["real_llm_integration_approved"] = True
        base["blocking_reasons"].append(f"trial_approval_must_be_not_approved:{trial_status}")
        return base

    if not completed_csv.exists():
        return base

    try:
        completed = pd.read_csv(completed_csv)
    except Exception as exc:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append(f"completed_csv_read_error:{exc}")
        return base

    cols = [str(c) for c in completed.columns]
    if _contains_non_ascii_key(cols):
        base["report_status"] = "blocked"
        base["blocking_reasons"].append("non_english_schema_keys_detected")
        return base
    if _has_live_llm_markers(cols):
        base["report_status"] = "blocked"
        base["blocking_reasons"].append("live_llm_provider_markers_detected")
        return base

    missing = [f for f in REQUIRED_FIELDS if f not in completed.columns]
    if missing:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append(f"missing_required_fields:{','.join(missing)}")
        return base

    reviewed = completed.drop_duplicates(subset=["sample_id"], keep="last").copy()
    reviewed = reviewed[_txt(reviewed["review_updated_at_utc"]) != ""].copy()
    reviewed_ids = reviewed["sample_id"].astype(str).tolist()
    base["reviewed_sample_ids"] = reviewed_ids
    base["reviewed_sample_count"] = int(len(reviewed_ids))
    base["new_reviewed_sample_count_since_smoke"] = int(sum(1 for sid in reviewed_ids if sid not in SMOKE_SAMPLE_IDS))

    base["candidate_type_distribution"] = _dist(reviewed.get("candidate_type", pd.Series(dtype=str)))
    base["human_label_distribution"] = _dist(reviewed["human_label"])
    base["human_confidence_distribution"] = _dist(reviewed["human_confidence"])

    total = max(1, len(reviewed))
    base["overall_rationale_coverage"] = _coverage(_count_non_empty(reviewed, "human_rationale_zh"), len(reviewed))
    base["counterexample_coverage"] = _coverage(_count_non_empty(reviewed, "human_counterexample_zh"), len(reviewed))
    base["context_notes_coverage"] = _coverage(_count_non_empty(reviewed, "human_context_notes_zh"), len(reviewed))
    base["p3_feedback_coverage"] = _coverage(_count_non_empty(reviewed, "human_pattern_3_feedback_zh"), len(reviewed))
    base["m8_feedback_coverage"] = _coverage(_count_non_empty(reviewed, "human_market_8_feedback_zh"), len(reviewed))
    base["m24_feedback_coverage"] = _coverage(_count_non_empty(reviewed, "human_market_24_feedback_zh"), len(reviewed))
    base["m128_feedback_coverage"] = _coverage(_count_non_empty(reviewed, "human_market_128_feedback_zh"), len(reviewed))
    base["local_feedback_coverage"] = _coverage(_count_non_empty(reviewed, "human_local_structure_feedback_zh"), len(reviewed))
    if "human_label" in reviewed.columns and "human_uncertainty_reason_zh" in reviewed.columns:
        labels = _txt(reviewed["human_label"])
        uncertain_mask = labels == "unclear"
        uncertain_count = int(uncertain_mask.sum())
        if uncertain_count > 0:
            reasons = _txt(reviewed["human_uncertainty_reason_zh"])
            filled = int((reasons[uncertain_mask] != "").sum())
            base["uncertainty_reason_coverage"] = _coverage(filled, uncertain_count)
        else:
            base["uncertainty_reason_coverage"] = 1.0


    overall_ok = (
        (_txt(reviewed["human_label"]) != "")
        & (_txt(reviewed["human_label"]) != "not_reviewed")
        & (_txt(reviewed["human_confidence"]) != "")
        & (_txt(reviewed["human_confidence"]) != "not_reviewed")
        & (_txt(reviewed["human_rationale_zh"]) != "")
    )
    layer_ok = _has_any_layer_feedback(reviewed)
    base["samples_with_overall_but_no_layer_evidence"] = int((overall_ok & (~layer_ok)).sum())
    base["samples_with_layer_evidence_but_no_overall_label"] = int(
        (layer_ok & ~((_txt(reviewed["human_label"]) != "") & (_txt(reviewed["human_label"]) != "not_reviewed"))).sum()
    )

    events, event_issues = _load_jsonl(review_events_jsonl)
    if event_issues:
        base["report_status"] = "blocked"
        base["blocking_reasons"].extend(event_issues)
        return base
    base["jsonl_event_count"] = int(len(events))
    reviewed_set = set(reviewed_ids)
    std_count = int(
        sum(
            1
            for row in events
            if str(row.get("sample_id", "")) in reviewed_set
            and str(row.get("standard_version", "")).strip() == "eurusd_15m_review_standard_v0"
        )
    )
    base["standard_version_coverage"] = _coverage(std_count, len(reviewed))

    artifacts, artifact_issues = _load_jsonl(llm_artifact_jsonl)
    if artifact_issues:
        base["report_status"] = "blocked"
        base["blocking_reasons"].extend(artifact_issues)
        return base
    art_map = {str(row.get("sample_id", "")): row for row in artifacts}
    if reviewed_ids:
        base["llm_artifact_contains_multi_layer_evidence"] = all(
            isinstance((art_map.get(sid, {}) or {}).get("multi_layer_evidence"), dict)
            and len(((art_map.get(sid, {}) or {}).get("multi_layer_evidence") or {})) > 0
            for sid in reviewed_ids
        )

    if base["reviewed_sample_count"] < int(minimum_total_reviewed):
        base["report_status"] = "awaiting_real_review_batch"
        return base

    required_all = [
        ("insufficient_new_samples_since_smoke", base["new_reviewed_sample_count_since_smoke"] >= int(minimum_new_since_smoke)),
        ("missing_overall_fields", int(overall_ok.sum()) == int(len(reviewed))),
        ("standard_version_coverage_insufficient", base["standard_version_coverage"] >= 1.0),
        ("llm_artifact_missing_multi_layer_evidence", base["llm_artifact_contains_multi_layer_evidence"]),
    ]
    blocked = [name for name, ok in required_all if not ok]
    if blocked:
        base["report_status"] = "blocked"
        base["blocking_reasons"].extend(blocked)
        return base

    layer_ratio = _coverage(int(layer_ok.sum()), len(reviewed))
    if layer_ratio < float(minimum_layer_feedback_ratio):
        base["report_status"] = "first_real_review_batch_watch"
        return base

    base["report_status"] = "first_real_review_batch_ready"
    return base


def render_first_real_review_batch_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD First Real Review Batch",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- reviewed_sample_count: `{report.get('reviewed_sample_count')}`",
        f"- new_reviewed_sample_count_since_smoke: `{report.get('new_reviewed_sample_count_since_smoke')}`",
        f"- human_review_quality_status: `{report.get('human_review_quality_status')}`",
        f"- llm_artifact_status: `{report.get('llm_artifact_status')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Distribution",
        "",
        f"- candidate_type_distribution: `{report.get('candidate_type_distribution')}`",
        f"- human_label_distribution: `{report.get('human_label_distribution')}`",
        f"- human_confidence_distribution: `{report.get('human_confidence_distribution')}`",
        "",
        "## Coverage",
        "",
        f"- overall_rationale_coverage: `{report.get('overall_rationale_coverage')}`",
        f"- uncertainty_reason_coverage: `{report.get('uncertainty_reason_coverage')}`",
        f"- p3_feedback_coverage: `{report.get('p3_feedback_coverage')}`",
        f"- m8_feedback_coverage: `{report.get('m8_feedback_coverage')}`",
        f"- m24_feedback_coverage: `{report.get('m24_feedback_coverage')}`",
        f"- m128_feedback_coverage: `{report.get('m128_feedback_coverage')}`",
        f"- local_feedback_coverage: `{report.get('local_feedback_coverage')}`",
        "",
        "## Next Operator Command",
        "",
        "```bash",
        "./scripts/run_eurusd_review_gui.sh",
        "```",
        "",
        "## Blocking Reasons",
        "",
    ]
    reasons = report.get("blocking_reasons") or []
    if reasons:
        lines.extend([f"- {x}" for x in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
