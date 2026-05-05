"""Validation for explicit approval record and minimal real LLM trial boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_ALLOWED_SAMPLES = 10


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_llm_trial_approval_report(*, readiness_json: Path, approval_json: Path) -> dict[str, Any]:
    readiness = _load_json(readiness_json)
    approval = _load_json(approval_json)
    if readiness is None:
        return {"status": "blocked", "reason": "missing_readiness_report", "readiness_json": str(readiness_json)}
    if approval is None:
        return {"status": "blocked", "reason": "missing_approval_artifact", "approval_json": str(approval_json)}

    readiness_status = readiness.get("status")
    required_fields = [
        "approval_status",
        "approved_scope",
        "allowed_input_artifact",
        "allowed_output_artifact",
        "max_samples",
        "provider",
        "model",
        "live_api_calls_allowed",
        "human_audit_required",
        "overwrite_human_labels_allowed",
        "trading_outputs_allowed",
        "rollback_plan_required",
    ]
    missing_fields = [f for f in required_fields if f not in approval]
    blocking_reasons: list[str] = []

    if missing_fields:
        blocking_reasons.append(f"missing_fields:{','.join(missing_fields)}")
    if readiness_status != "ready_for_explicit_approval":
        blocking_reasons.append(f"readiness_not_ready_for_explicit_approval:{readiness_status}")

    approval_status = approval.get("approval_status", "not_approved")
    max_samples = int(approval.get("max_samples", 0) or 0)
    live_api_calls_allowed = bool(approval.get("live_api_calls_allowed", False))
    human_audit_required = bool(approval.get("human_audit_required", False))
    overwrite_human_labels_allowed = bool(approval.get("overwrite_human_labels_allowed", False))
    trading_outputs_allowed = bool(approval.get("trading_outputs_allowed", False))
    rollback_plan_required = bool(approval.get("rollback_plan_required", False))
    provider = str(approval.get("provider", "") or "").strip()
    model = str(approval.get("model", "") or "").strip()
    output_artifact = str(approval.get("allowed_output_artifact", "") or "").strip()

    if trading_outputs_allowed:
        blocking_reasons.append("trading_outputs_must_be_false")
    if overwrite_human_labels_allowed:
        blocking_reasons.append("overwrite_human_labels_must_be_false")
    if not human_audit_required:
        blocking_reasons.append("human_audit_required_must_be_true")
    if not rollback_plan_required:
        blocking_reasons.append("rollback_plan_required_must_be_true")
    if max_samples <= 0:
        blocking_reasons.append("max_samples_must_be_positive")
    if max_samples > MAX_ALLOWED_SAMPLES:
        blocking_reasons.append(f"max_samples_exceeds_limit:{MAX_ALLOWED_SAMPLES}")

    if approval_status == "approved":
        if not live_api_calls_allowed:
            blocking_reasons.append("approved_but_live_api_calls_not_allowed")
        if provider == "" or model == "":
            blocking_reasons.append("approved_requires_provider_and_model")
        if output_artifact == "":
            blocking_reasons.append("approved_requires_output_artifact")

    if blocking_reasons:
        status = "blocked"
    elif approval_status != "approved":
        status = "not_approved"
    else:
        status = "approved_for_limited_trial"

    return {
        "status": status,
        "readiness_status": readiness_status,
        "approval_status": approval_status,
        "approved_scope": approval.get("approved_scope"),
        "max_samples": max_samples,
        "max_allowed_samples": MAX_ALLOWED_SAMPLES,
        "live_api_calls_allowed": live_api_calls_allowed,
        "human_audit_required": human_audit_required,
        "overwrite_human_labels_allowed": overwrite_human_labels_allowed,
        "trading_outputs_allowed": trading_outputs_allowed,
        "rollback_plan_required": rollback_plan_required,
        "provider": provider,
        "model": model,
        "allowed_input_artifact": approval.get("allowed_input_artifact"),
        "allowed_output_artifact": output_artifact,
        "blocking_reasons": blocking_reasons,
        "notes": approval.get("notes", ""),
    }


def render_llm_trial_approval_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD LLM Trial Approval Validation",
        "",
        f"**Status**: `{report.get('status')}`",
        "",
        f"- readiness_status: `{report.get('readiness_status')}`",
        f"- approval_status: `{report.get('approval_status')}`",
        f"- approved_scope: `{report.get('approved_scope')}`",
        f"- max_samples: `{report.get('max_samples')}` / `{report.get('max_allowed_samples')}`",
        f"- live_api_calls_allowed: `{report.get('live_api_calls_allowed')}`",
        f"- human_audit_required: `{report.get('human_audit_required')}`",
        f"- overwrite_human_labels_allowed: `{report.get('overwrite_human_labels_allowed')}`",
        f"- trading_outputs_allowed: `{report.get('trading_outputs_allowed')}`",
        f"- rollback_plan_required: `{report.get('rollback_plan_required')}`",
        "",
        "## Blocking Reasons",
        "",
    ]
    reasons = report.get("blocking_reasons", [])
    if reasons:
        lines.extend([f"- {item}" for item in reasons])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- readiness is not approval",
            "- limited trial approval does not permit trading actions",
            "- no human label overwrite is allowed",
        ]
    )
    return "\n".join(lines)
