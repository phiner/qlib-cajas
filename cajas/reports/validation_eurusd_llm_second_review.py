"""Offline LLM second-review protocol/output validation for EURUSD artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "eurusd_llm_second_review_v0"
SOURCE_ARTIFACT_VERSION = "eurusd_llm_review_sample_v0"
ALLOWED_VALIDITY = {"valid", "invalid", "uncertain"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
REQUIRED_KEYS = {
    "artifact_version",
    "source_artifact_version",
    "sample_id",
    "standard_version",
    "llm_reviewer_role",
    "llm_pattern_validity",
    "llm_confidence",
    "supporting_observations_zh",
    "counter_observations_zh",
    "uncertainty_reason_zh",
    "requires_human_review",
    "possible_standard_gap_zh",
    "forbidden_trade_output_present",
    "raw_model_name",
    "review_created_at_utc",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        rows.append(json.loads(text))
    return rows


def _is_english_key(value: str) -> bool:
    return bool(value) and value.isascii() and value.replace("_", "").isalnum() and value == value.lower()


def _validate_row_schema(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_KEYS - set(row.keys())
    if missing:
        errors.append(f"missing_keys:{sorted(missing)}")
    if row.get("artifact_version") != PROTOCOL_VERSION:
        errors.append("invalid_artifact_version")
    if row.get("source_artifact_version") != SOURCE_ARTIFACT_VERSION:
        errors.append("invalid_source_artifact_version")
    if row.get("llm_reviewer_role") != "second_reviewer":
        errors.append("invalid_llm_reviewer_role")
    if row.get("llm_pattern_validity") not in ALLOWED_VALIDITY:
        errors.append("invalid_llm_pattern_validity")
    if row.get("llm_confidence") not in ALLOWED_CONFIDENCE:
        errors.append("invalid_llm_confidence")
    if not isinstance(row.get("supporting_observations_zh"), list):
        errors.append("invalid_supporting_observations_zh")
    if not isinstance(row.get("counter_observations_zh"), list):
        errors.append("invalid_counter_observations_zh")
    if not isinstance(row.get("uncertainty_reason_zh"), str):
        errors.append("invalid_uncertainty_reason_zh")
    if not isinstance(row.get("possible_standard_gap_zh"), str):
        errors.append("invalid_possible_standard_gap_zh")
    if not isinstance(row.get("requires_human_review"), bool):
        errors.append("invalid_requires_human_review")
    if row.get("forbidden_trade_output_present") is not False:
        errors.append("forbidden_trade_output_present")
    for key in row.keys():
        if not _is_english_key(str(key)):
            errors.append(f"non_english_key:{key}")
    return errors


def build_llm_second_review_report(
    *,
    sample_artifacts_jsonl: Path,
    llm_outputs_jsonl: Path | None = None,
    min_output_coverage: float = 0.8,
    max_high_conf_disagreement_rate: float = 0.2,
) -> dict[str, Any]:
    if not sample_artifacts_jsonl.exists():
        return {
            "report_status": "blocked",
            "reason": "sample_artifacts_missing",
            "sample_artifacts_jsonl": str(sample_artifacts_jsonl),
        }

    source_rows = _read_jsonl(sample_artifacts_jsonl)
    source_sample_ids = [str(r.get("sample_id", "")) for r in source_rows]
    source_id_set = set(source_sample_ids)
    source_count = len(source_rows)

    if llm_outputs_jsonl is None or not llm_outputs_jsonl.exists():
        return {
            "report_status": "llm_second_review_protocol_ready",
            "protocol_version": PROTOCOL_VERSION,
            "source_artifact_row_count": source_count,
            "llm_review_row_count": 0,
            "missing_output_row_count": source_count,
            "duplicate_sample_id_count": 0,
            "invalid_schema_row_count": 0,
            "forbidden_output_violation_count": 0,
            "unknown_sample_id_count": 0,
            "agreement_count": 0,
            "disagreement_count": 0,
            "high_confidence_disagreement_count": 0,
            "requires_human_review_count": 0,
            "possible_standard_gap_count": 0,
            "automation_readiness_status": "not_evaluated",
            "output_coverage": 0.0,
            "high_confidence_disagreement_rate": 0.0,
        }

    output_rows = _read_jsonl(llm_outputs_jsonl)
    output_count = len(output_rows)
    output_ids = [str(r.get("sample_id", "")) for r in output_rows]
    duplicate_count = max(0, output_count - len(set(output_ids)))
    unknown_count = sum(1 for sid in output_ids if sid not in source_id_set)
    missing_output_count = max(0, len(source_id_set - set(output_ids)))

    invalid_schema_count = 0
    forbidden_count = 0
    requires_human_review_count = 0
    possible_standard_gap_count = 0
    agreement_count = 0
    disagreement_count = 0
    high_conf_disagreement_count = 0

    human_label_by_id = {
        str(r.get("sample_id", "")): str(((r.get("human_review") or {}).get("human_label", "not_reviewed")))
        for r in source_rows
    }

    for row in output_rows:
        errors = _validate_row_schema(row)
        if errors:
            invalid_schema_count += 1
        if row.get("forbidden_trade_output_present") is True or "forbidden_trade_output_present" in errors:
            forbidden_count += 1
        if bool(row.get("requires_human_review", False)):
            requires_human_review_count += 1
        if str(row.get("possible_standard_gap_zh", "")).strip():
            possible_standard_gap_count += 1
        sample_id = str(row.get("sample_id", ""))
        llm_validity = str(row.get("llm_pattern_validity", ""))
        human_label = human_label_by_id.get(sample_id, "not_reviewed")
        mapped_human = (
            "valid" if human_label == "valid_pattern" else
            "invalid" if human_label == "false_positive" else
            "uncertain" if human_label in {"weak_pattern", "unclear", "not_enough_context", "not_reviewed"} else
            "uncertain"
        )
        if sample_id in source_id_set:
            if llm_validity == mapped_human:
                agreement_count += 1
            else:
                disagreement_count += 1
                if str(row.get("llm_confidence", "")) == "high":
                    high_conf_disagreement_count += 1

    output_coverage = float(output_count / source_count) if source_count > 0 else 0.0
    disagreement_base = max(1, agreement_count + disagreement_count)
    high_conf_disagreement_rate = float(high_conf_disagreement_count / disagreement_base)

    if forbidden_count > 0 or invalid_schema_count > 0 or unknown_count > 0 or duplicate_count > 0:
        readiness = "not_ready"
    elif output_coverage < float(min_output_coverage):
        readiness = "watch"
    elif high_conf_disagreement_rate > float(max_high_conf_disagreement_rate):
        readiness = "watch"
    else:
        readiness = "ready_for_limited_trial"

    report_status = "llm_second_review_outputs_ready" if invalid_schema_count == 0 and forbidden_count == 0 else "blocked"
    return {
        "report_status": report_status,
        "protocol_version": PROTOCOL_VERSION,
        "source_artifact_row_count": source_count,
        "llm_review_row_count": output_count,
        "missing_output_row_count": missing_output_count,
        "duplicate_sample_id_count": duplicate_count,
        "invalid_schema_row_count": invalid_schema_count,
        "forbidden_output_violation_count": forbidden_count,
        "unknown_sample_id_count": unknown_count,
        "agreement_count": agreement_count,
        "disagreement_count": disagreement_count,
        "high_confidence_disagreement_count": high_conf_disagreement_count,
        "requires_human_review_count": requires_human_review_count,
        "possible_standard_gap_count": possible_standard_gap_count,
        "automation_readiness_status": readiness,
        "output_coverage": output_coverage,
        "high_confidence_disagreement_rate": high_conf_disagreement_rate,
    }


def render_llm_second_review_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EURUSD LLM Second Review Validation",
            "",
            f"**Status**: `{report.get('report_status')}`",
            "",
            f"- protocol_version: `{report.get('protocol_version')}`",
            f"- source_artifact_row_count: `{report.get('source_artifact_row_count')}`",
            f"- llm_review_row_count: `{report.get('llm_review_row_count')}`",
            f"- missing_output_row_count: `{report.get('missing_output_row_count')}`",
            f"- duplicate_sample_id_count: `{report.get('duplicate_sample_id_count')}`",
            f"- invalid_schema_row_count: `{report.get('invalid_schema_row_count')}`",
            f"- forbidden_output_violation_count: `{report.get('forbidden_output_violation_count')}`",
            f"- unknown_sample_id_count: `{report.get('unknown_sample_id_count')}`",
            f"- agreement_count: `{report.get('agreement_count')}`",
            f"- disagreement_count: `{report.get('disagreement_count')}`",
            f"- high_confidence_disagreement_count: `{report.get('high_confidence_disagreement_count')}`",
            f"- requires_human_review_count: `{report.get('requires_human_review_count')}`",
            f"- possible_standard_gap_count: `{report.get('possible_standard_gap_count')}`",
            f"- automation_readiness_status: `{report.get('automation_readiness_status')}`",
        ]
    )
