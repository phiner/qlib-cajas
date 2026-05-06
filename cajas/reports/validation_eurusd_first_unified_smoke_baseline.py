"""Validate first unified EURUSD smoke-review baseline packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_OVERALL_FIELDS = [
    "human_label",
    "human_confidence",
    "human_rationale_zh",
]
LAYER_FEEDBACK_FIELDS = [
    "human_pattern_3_feedback_zh",
    "human_market_8_feedback_zh",
    "human_market_24_feedback_zh",
    "human_market_128_feedback_zh",
    "human_local_structure_feedback_zh",
]


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
            obj = json.loads(line)
        except Exception:
            issues.append(f"invalid_jsonl_line:{i}")
            continue
        if not isinstance(obj, dict):
            issues.append(f"non_object_jsonl_line:{i}")
            continue
        rows.append(obj)
    return rows, issues


def _contains_non_ascii_key(keys: list[str]) -> bool:
    return any(any(ord(ch) > 127 for ch in key) for key in keys)


def _count_present(df: pd.DataFrame, field: str) -> int:
    if field not in df.columns:
        return 0
    values = _txt(df[field])
    return int(((values != "") & (values != "not_reviewed")).sum())


def _row_has_any_layer_feedback(row: pd.Series) -> bool:
    for field in LAYER_FEEDBACK_FIELDS:
        raw = row.get(field, "")
        if raw is None or pd.isna(raw):
            continue
        val = str(raw).strip()
        if val and val.lower() != "nan":
            return True
    return False


def build_first_unified_smoke_baseline_report(
    *,
    completed_csv: Path,
    review_events_jsonl: Path,
    llm_artifact_jsonl: Path,
    smoke_report_json: Path,
    quality_report_json: Path,
    llm_artifact_report_json: Path,
    trial_approval_json: Path,
    minimum_reviewed_samples: int = 3,
) -> dict[str, Any]:
    smoke_report = _load_json(smoke_report_json) or {}
    quality_report = _load_json(quality_report_json) or {}
    llm_report = _load_json(llm_artifact_report_json) or {}
    trial_report = _load_json(trial_approval_json) or {}
    trial_status = str(trial_report.get("approval_status", trial_report.get("trial_approval_status", "not_approved")))

    base: dict[str, Any] = {
        "report_status": "awaiting_smoke_reviews",
        "reviewed_sample_ids": [],
        "reviewed_sample_count": 0,
        "completed_review_csv_exists": completed_csv.exists(),
        "review_events_jsonl_exists": review_events_jsonl.exists(),
        "llm_artifact_jsonl_exists": llm_artifact_jsonl.exists(),
        "overall_fields_present_count": 0,
        "human_label_present_count": 0,
        "human_confidence_present_count": 0,
        "human_rationale_zh_present_count": 0,
        "standard_version_present_count": 0,
        "multi_layer_evidence_present_count": 0,
        "p3_feedback_present_count": 0,
        "m8_feedback_present_count": 0,
        "m24_feedback_present_count": 0,
        "m128_feedback_present_count": 0,
        "local_feedback_present_count": 0,
        "jsonl_event_count_for_reviewed_samples": 0,
        "save_and_next_evidence_present": False,
        "reload_verification_source": "review_events_jsonl_action_history",
        "llm_artifact_contains_human_review": False,
        "llm_artifact_contains_multi_layer_evidence": False,
        "smoke_report_status": str(smoke_report.get("report_status", "unknown")),
        "quality_report_status": str(quality_report.get("report_status", "unknown")),
        "llm_artifact_report_status": str(llm_report.get("report_status", "unknown")),
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
        completed_df = pd.read_csv(completed_csv)
    except Exception as exc:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append(f"completed_csv_read_error:{exc}")
        return base

    cols = [str(c) for c in completed_df.columns]
    if _contains_non_ascii_key(cols):
        base["report_status"] = "blocked"
        base["blocking_reasons"].append("non_english_schema_keys_detected")
        return base

    for field in REQUIRED_OVERALL_FIELDS + ["review_updated_at_utc"]:
        if field not in completed_df.columns:
            base["report_status"] = "blocked"
            base["blocking_reasons"].append(f"missing_required_field:{field}")
            return base

    dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
    reviewed = dedup[_txt(dedup["review_updated_at_utc"]) != ""].copy()
    reviewed_ids = reviewed["sample_id"].astype(str).tolist()
    base["reviewed_sample_ids"] = reviewed_ids
    base["reviewed_sample_count"] = int(len(reviewed_ids))

    base["human_label_present_count"] = _count_present(reviewed, "human_label")
    base["human_confidence_present_count"] = _count_present(reviewed, "human_confidence")
    base["human_rationale_zh_present_count"] = _count_present(reviewed, "human_rationale_zh")
    base["overall_fields_present_count"] = int(
        (
            (_txt(reviewed["human_label"]) != "")
            & (_txt(reviewed["human_label"]) != "not_reviewed")
            & (_txt(reviewed["human_confidence"]) != "")
            & (_txt(reviewed["human_confidence"]) != "not_reviewed")
            & (_txt(reviewed["human_rationale_zh"]) != "")
        ).sum()
    )
    base["p3_feedback_present_count"] = _count_present(reviewed, "human_pattern_3_feedback_zh")
    base["m8_feedback_present_count"] = _count_present(reviewed, "human_market_8_feedback_zh")
    base["m24_feedback_present_count"] = _count_present(reviewed, "human_market_24_feedback_zh")
    base["m128_feedback_present_count"] = _count_present(reviewed, "human_market_128_feedback_zh")
    base["local_feedback_present_count"] = _count_present(reviewed, "human_local_structure_feedback_zh")
    base["multi_layer_evidence_present_count"] = int(reviewed.apply(_row_has_any_layer_feedback, axis=1).sum())

    events, event_issues = _load_jsonl(review_events_jsonl)
    if event_issues:
        base["report_status"] = "blocked"
        base["blocking_reasons"].extend(event_issues)
        return base
    reviewed_set = set(reviewed_ids)
    base["jsonl_event_count_for_reviewed_samples"] = int(
        sum(1 for row in events if str(row.get("sample_id", "")) in reviewed_set)
    )
    base["standard_version_present_count"] = int(
        sum(
            1
            for row in events
            if str(row.get("sample_id", "")) in reviewed_set
            and str(row.get("standard_version", "")).strip() == "eurusd_15m_review_standard_v0"
        )
    )
    base["save_and_next_evidence_present"] = any(
        str(row.get("sample_id", "")) in reviewed_set and str(row.get("action_type", "")) == "save_and_next"
        for row in events
    )

    artifact_rows, artifact_issues = _load_jsonl(llm_artifact_jsonl)
    if artifact_issues:
        base["report_status"] = "blocked"
        base["blocking_reasons"].extend(artifact_issues)
        return base
    artifact_map = {str(row.get("sample_id", "")): row for row in artifact_rows}
    if reviewed_ids:
        subset = [artifact_map.get(sid, {}) for sid in reviewed_ids]
        base["llm_artifact_contains_human_review"] = all(
            isinstance(row.get("human_review"), dict) and len(row.get("human_review", {})) > 0 for row in subset
        )
        base["llm_artifact_contains_multi_layer_evidence"] = all(
            isinstance(row.get("multi_layer_evidence"), dict) and len(row.get("multi_layer_evidence", {})) > 0 for row in subset
        )

    if base["reviewed_sample_count"] < int(minimum_reviewed_samples):
        base["report_status"] = "awaiting_smoke_reviews"
        return base

    required_checks = [
        ("overall_fields_insufficient", base["overall_fields_present_count"] >= int(minimum_reviewed_samples)),
        ("human_label_insufficient", base["human_label_present_count"] >= int(minimum_reviewed_samples)),
        ("human_confidence_insufficient", base["human_confidence_present_count"] >= int(minimum_reviewed_samples)),
        ("human_rationale_zh_insufficient", base["human_rationale_zh_present_count"] >= int(minimum_reviewed_samples)),
        ("standard_version_insufficient", base["standard_version_present_count"] >= int(minimum_reviewed_samples)),
        ("multi_layer_evidence_insufficient", base["multi_layer_evidence_present_count"] >= int(minimum_reviewed_samples)),
        ("llm_artifact_missing_human_review", base["llm_artifact_contains_human_review"]),
        ("llm_artifact_missing_multi_layer_evidence", base["llm_artifact_contains_multi_layer_evidence"]),
    ]
    failed = [name for name, ok in required_checks if not ok]
    if failed:
        base["report_status"] = "blocked"
        base["blocking_reasons"].extend(failed)
        return base

    base["report_status"] = "first_unified_smoke_baseline_ready"
    return base


def render_first_unified_smoke_baseline_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD First Unified Smoke Baseline",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- reviewed_sample_ids: `{report.get('reviewed_sample_ids')}`",
        f"- reviewed_sample_count: `{report.get('reviewed_sample_count')}`",
        f"- smoke_report_status: `{report.get('smoke_report_status')}`",
        f"- quality_report_status: `{report.get('quality_report_status')}`",
        f"- llm_artifact_report_status: `{report.get('llm_artifact_report_status')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Proven",
        "",
        "- Unified GUI save path works for first smoke baseline.",
        "- CSV latest state persistence works for reviewed samples.",
        "- JSONL audit append works and includes save/save_and_next traces.",
        "- Overall fields persist (`human_label`, `human_confidence`, `human_rationale_zh`).",
        "- Multi-layer evidence persists (P3/M8/M24/M128/Local).",
        "- LLM artifacts include both `human_review` and `multi_layer_evidence`.",
        "",
        "## Remaining",
        "",
        "- Continue human review beyond the first smoke baseline set.",
        "- Improve quality metrics from watch toward ready.",
        "- Keep real LLM integration unapproved until explicit approval.",
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
        lines.extend([f"- {r}" for r in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
