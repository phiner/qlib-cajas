"""Aggregate readiness gate for real EURUSD LLM integration approval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _scan_live_llm_markers(paths: list[Path]) -> dict[str, Any]:
    markers = [
        "openai",
        "anthropic",
        "gemini",
        "cohere",
        "api_key",
        "client.chat.completions",
        "responses.create",
    ]
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for marker in markers:
            if marker in lower:
                hits.append({"path": str(path), "marker": marker})
    return {"detected": len(hits) > 0, "hits": hits}


def build_real_llm_integration_readiness_report(
    *,
    language_boundary_json: Path,
    zh_rationale_json: Path,
    llm_artifacts_json: Path,
    llm_second_review_json: Path,
    standard_v0_json: Path,
    fixture_drill_json: Path | None,
    docs_to_check: list[Path],
    files_to_scan_for_live_llm: list[Path],
) -> dict[str, Any]:
    required = {
        "language_boundary": ("status", "language_boundary_ready", _load_json(language_boundary_json)),
        "zh_rationale_fields": ("status", "zh_rationale_fields_ready", _load_json(zh_rationale_json)),
        "llm_review_artifacts": ("report_status", "llm_review_artifacts_ready", _load_json(llm_artifacts_json)),
        "llm_second_review_protocol": ("report_status", "llm_second_review_protocol_ready", _load_json(llm_second_review_json)),
        "review_standard_v0": ("status", "review_standard_v0_ready", _load_json(standard_v0_json)),
    }
    checks: dict[str, dict[str, Any]] = {}
    missing_required_reports: list[str] = []
    blocked_prereqs: list[str] = []
    pending_prereqs: list[str] = []
    for name, (field, expected, payload) in required.items():
        if payload is None:
            checks[name] = {"present": False, "expected_status": expected, "actual_status": None}
            missing_required_reports.append(name)
            continue
        actual = payload.get(field)
        checks[name] = {"present": True, "expected_status": expected, "actual_status": actual}
        if actual == "blocked":
            blocked_prereqs.append(name)
        elif actual != expected:
            pending_prereqs.append(name)

    fixture_payload = _load_json(fixture_drill_json) if fixture_drill_json is not None else None
    fixture_state = {
        "present": fixture_payload is not None,
        "report_status": fixture_payload.get("report_status") if fixture_payload else None,
        "automation_readiness_status": fixture_payload.get("automation_readiness_status") if fixture_payload else None,
        "drill_only_expected": True,
    }

    docs_text = "\n".join([p.read_text(encoding="utf-8") for p in docs_to_check if p.exists()])
    docs_lower = docs_text.lower()
    forbidden_outputs_present = all(k in docs_lower for k in ["trade_signal", "entry", "exit", "position_size"])
    human_audit_gate_documented = ("human audit" in docs_lower) or ("人工" in docs_text and "审核" in docs_text)
    explicit_approval_documented = ("explicit approval" in docs_lower) or ("明确批准" in docs_text)
    offline_only_documented = ("no live llm api calls" in docs_lower) or ("offline" in docs_lower and "no live llm" in docs_lower)

    live_scan = _scan_live_llm_markers(files_to_scan_for_live_llm)

    if live_scan["detected"] or not forbidden_outputs_present or not human_audit_gate_documented:
        status = "blocked"
    elif blocked_prereqs:
        status = "blocked"
    elif missing_required_reports or pending_prereqs:
        status = "not_ready"
    else:
        status = "ready_for_explicit_approval"

    remaining_work: list[str] = []
    if missing_required_reports:
        remaining_work.append(f"missing_required_reports:{','.join(missing_required_reports)}")
    if pending_prereqs:
        remaining_work.append(f"pending_prereqs:{','.join(pending_prereqs)}")
    if not forbidden_outputs_present:
        remaining_work.append("missing_forbidden_output_boundary_docs")
    if not human_audit_gate_documented:
        remaining_work.append("missing_human_audit_gate_docs")
    if not explicit_approval_documented:
        remaining_work.append("missing_explicit_approval_gate_docs")
    if live_scan["detected"]:
        remaining_work.append("live_llm_integration_detected_before_approval")

    return {
        "status": status,
        "prerequisites": checks,
        "fixture_drill": fixture_state,
        "forbidden_output_boundary_present": forbidden_outputs_present,
        "human_audit_gate_documented": human_audit_gate_documented,
        "explicit_approval_documented": explicit_approval_documented,
        "offline_only_documented": offline_only_documented,
        "live_llm_integration_scan": live_scan,
        "remaining_work_before_real_llm_integration": remaining_work,
        "non_goals": [
            "readiness_is_not_approval",
            "readiness_is_not_automation_permission",
            "no_trading_actions",
            "no_model_training",
        ],
    }


def render_real_llm_integration_readiness_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Real LLM Integration Readiness",
        "",
        f"**Status**: `{report['status']}`",
        "",
        "## Prerequisites",
        "",
    ]
    for name, payload in report.get("prerequisites", {}).items():
        lines.append(
            f"- {name}: present={payload.get('present')} expected={payload.get('expected_status')} actual={payload.get('actual_status')}"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            f"- forbidden_output_boundary_present: `{report.get('forbidden_output_boundary_present')}`",
            f"- human_audit_gate_documented: `{report.get('human_audit_gate_documented')}`",
            f"- explicit_approval_documented: `{report.get('explicit_approval_documented')}`",
            f"- offline_only_documented: `{report.get('offline_only_documented')}`",
            f"- live_llm_integration_detected: `{report.get('live_llm_integration_scan', {}).get('detected')}`",
            "",
            "## Remaining Work",
            "",
        ]
    )
    for item in report.get("remaining_work_before_real_llm_integration", []):
        lines.append(f"- {item}")
    if not report.get("remaining_work_before_real_llm_integration"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- readiness is not approval",
            "- explicit user approval is still required before any real provider integration",
        ]
    )
    return "\n".join(lines)
