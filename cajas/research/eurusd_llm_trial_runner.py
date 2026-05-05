"""Fail-closed EURUSD LLM trial runner skeleton without provider calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_APPROVAL_STATUS = "approved"
REQUIRED_READINESS_STATUS = "ready_for_explicit_approval"
MAX_ALLOWED_SAMPLES = 10


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "":
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _render_reason(*, status: str, reasons: list[str]) -> str:
    if reasons:
        return ";".join(reasons)
    if status == "not_approved":
        return "approval_status_not_approved"
    if status == "ready_but_no_provider_adapter":
        return "provider_adapter_not_implemented"
    return "blocked"


def build_eurusd_llm_trial_run_report(
    *,
    readiness_json: Path,
    approval_json: Path,
    sample_artifacts_jsonl: Path,
    output_jsonl: Path,
) -> dict[str, Any]:
    readiness = _load_json(readiness_json)
    approval = _load_json(approval_json)
    if readiness is None:
        return {
            "run_status": "blocked",
            "approval_status": None,
            "readiness_status": None,
            "provider": "",
            "model": "",
            "max_samples": 0,
            "selected_sample_count": 0,
            "provider_adapter_available": False,
            "live_api_calls_attempted": False,
            "output_jsonl_written": False,
            "human_labels_mutated": False,
            "trading_outputs_allowed": False,
            "overwrite_human_labels_allowed": False,
            "human_audit_required": False,
            "reason": "missing_readiness_report",
            "blocking_reasons": ["missing_readiness_report"],
            "readiness_json": str(readiness_json),
        }
    if approval is None:
        return {
            "run_status": "blocked",
            "approval_status": None,
            "readiness_status": readiness.get("status"),
            "provider": "",
            "model": "",
            "max_samples": 0,
            "selected_sample_count": 0,
            "provider_adapter_available": False,
            "live_api_calls_attempted": False,
            "output_jsonl_written": False,
            "human_labels_mutated": False,
            "trading_outputs_allowed": False,
            "overwrite_human_labels_allowed": False,
            "human_audit_required": False,
            "reason": "missing_approval_artifact",
            "blocking_reasons": ["missing_approval_artifact"],
            "approval_json": str(approval_json),
        }

    readiness_status = str(readiness.get("status", ""))
    approval_status = str(approval.get("approval_status", "not_approved"))
    provider = str(approval.get("provider", "") or "").strip()
    model = str(approval.get("model", "") or "").strip()

    max_samples = int(approval.get("max_samples", 0) or 0)
    live_api_calls_allowed = bool(approval.get("live_api_calls_allowed", False))
    trading_outputs_allowed = bool(approval.get("trading_outputs_allowed", False))
    overwrite_human_labels_allowed = bool(approval.get("overwrite_human_labels_allowed", False))
    human_audit_required = bool(approval.get("human_audit_required", False))

    blocking_reasons: list[str] = []
    if readiness_status != REQUIRED_READINESS_STATUS:
        blocking_reasons.append(f"readiness_not_{REQUIRED_READINESS_STATUS}:{readiness_status}")
    if trading_outputs_allowed:
        blocking_reasons.append("trading_outputs_must_be_false")
    if overwrite_human_labels_allowed:
        blocking_reasons.append("overwrite_human_labels_must_be_false")
    if not human_audit_required:
        blocking_reasons.append("human_audit_required_must_be_true")
    if max_samples <= 0:
        blocking_reasons.append("max_samples_must_be_positive")
    if max_samples > MAX_ALLOWED_SAMPLES:
        blocking_reasons.append(f"max_samples_exceeds_limit:{MAX_ALLOWED_SAMPLES}")

    if approval_status == REQUIRED_APPROVAL_STATUS:
        if not live_api_calls_allowed:
            blocking_reasons.append("approved_but_live_api_calls_not_allowed")
        if provider == "":
            blocking_reasons.append("approved_requires_provider")
        if model == "":
            blocking_reasons.append("approved_requires_model")

    samples = _load_jsonl(sample_artifacts_jsonl)
    if samples is None:
        blocking_reasons.append("missing_sample_artifacts")
        samples = []

    selected_sample_count = min(len(samples), max(0, min(max_samples, MAX_ALLOWED_SAMPLES)))

    if blocking_reasons:
        status = "blocked"
    elif approval_status != REQUIRED_APPROVAL_STATUS:
        status = "not_approved"
    else:
        # No provider adapter exists in this task by design.
        status = "ready_but_no_provider_adapter"

    should_write_output_jsonl = status == "ready_but_no_provider_adapter" and selected_sample_count == 0
    if should_write_output_jsonl:
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        output_jsonl.write_text("", encoding="utf-8")

    return {
        "run_status": status,
        "approval_status": approval_status,
        "readiness_status": readiness_status,
        "provider": provider,
        "model": model,
        "max_samples": max_samples,
        "selected_sample_count": selected_sample_count,
        "provider_adapter_available": False,
        "live_api_calls_attempted": False,
        "output_jsonl_written": should_write_output_jsonl,
        "human_labels_mutated": False,
        "trading_outputs_allowed": trading_outputs_allowed,
        "overwrite_human_labels_allowed": overwrite_human_labels_allowed,
        "human_audit_required": human_audit_required,
        "reason": _render_reason(status=status, reasons=blocking_reasons),
        "blocking_reasons": blocking_reasons,
        "sample_artifacts_jsonl": str(sample_artifacts_jsonl),
        "output_jsonl": str(output_jsonl),
    }


def render_eurusd_llm_trial_run_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD LLM Second-Review Trial Runner",
        "",
        f"**Run Status**: `{report.get('run_status')}`",
        "",
        f"- approval_status: `{report.get('approval_status')}`",
        f"- readiness_status: `{report.get('readiness_status')}`",
        f"- provider: `{report.get('provider')}`",
        f"- model: `{report.get('model')}`",
        f"- max_samples: `{report.get('max_samples')}`",
        f"- selected_sample_count: `{report.get('selected_sample_count')}`",
        f"- provider_adapter_available: `{report.get('provider_adapter_available')}`",
        f"- live_api_calls_attempted: `{report.get('live_api_calls_attempted')}`",
        f"- output_jsonl_written: `{report.get('output_jsonl_written')}`",
        f"- human_labels_mutated: `{report.get('human_labels_mutated')}`",
        f"- trading_outputs_allowed: `{report.get('trading_outputs_allowed')}`",
        f"- overwrite_human_labels_allowed: `{report.get('overwrite_human_labels_allowed')}`",
        f"- human_audit_required: `{report.get('human_audit_required')}`",
        f"- reason: `{report.get('reason')}`",
        "",
        "## Blocking Reasons",
        "",
    ]
    reasons = report.get("blocking_reasons") or []
    if reasons:
        lines.extend([f"- {item}" for item in reasons])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- no provider adapter in this task",
            "- no live API calls",
            "- no human label overwrite",
            "- no trading outputs",
        ]
    )
    return "\n".join(lines)
