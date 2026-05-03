"""Release-cycle runtime monitor report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_runtime_release_cycle_report(
    *,
    runtime_edge_report: Path,
    runtime_budget_report: Path,
    fast_timing_json: Path,
    runtime_variance_report: Path | None = None,
    runtime_watch_triage_report: Path | None = None,
    pytest_runtime_profile: Path | None = None,
) -> dict[str, Any]:
    edge = _load_json(runtime_edge_report)
    budget = _load_json(runtime_budget_report)
    timing = _load_json(fast_timing_json)
    variance = _load_json(runtime_variance_report) if runtime_variance_report and runtime_variance_report.exists() else {}
    triage = _load_json(runtime_watch_triage_report) if runtime_watch_triage_report and runtime_watch_triage_report.exists() else {}
    profile = _load_json(pytest_runtime_profile) if pytest_runtime_profile and pytest_runtime_profile.exists() else {}

    edge_status = edge.get("status", "watch")
    budget_status = budget.get("overall_status", "warn")
    timing_consistency_status = (budget.get("timing_consistency") or {}).get("status", "warn")
    variance_status = variance.get("status")
    triage_status = triage.get("status")
    profile_status = profile.get("status")

    blocking_runtime_gates: list[str] = []
    watch_runtime_gates: list[str] = []
    non_blocking_notes: list[str] = []

    if budget_status == "fail":
        blocking_runtime_gates.append("runtime_budget_status=fail")
    elif budget_status == "warn":
        watch_runtime_gates.append("runtime_budget_status=warn")

    if timing_consistency_status == "fail":
        blocking_runtime_gates.append("timing_consistency_status=fail")
    elif timing_consistency_status == "warn":
        watch_runtime_gates.append("timing_consistency_status=warn")

    if edge_status == "fail":
        blocking_runtime_gates.append("runtime_edge_status=fail")
    elif edge_status in {"warn", "watch"}:
        watch_runtime_gates.append(f"runtime_edge_status={edge_status}")

    if variance_status == "fail":
        blocking_runtime_gates.append("runtime_variance_status=fail")
    elif variance_status in {"warn", "watch"}:
        watch_runtime_gates.append(f"runtime_variance_status={variance_status}")

    if triage_status == "fail":
        blocking_runtime_gates.append("runtime_watch_triage_status=fail")
    elif triage_status in {"warn", "watch"}:
        watch_runtime_gates.append(f"runtime_watch_triage_status={triage_status}")

    if profile_status in {"warn", "watch"}:
        non_blocking_notes.append(f"pytest_runtime_profile_status={profile_status}")

    if blocking_runtime_gates:
        status = "fail"
        reason_code = "runtime_gate_fail"
        recommendation = "optimize_before_release"
        next_action = "resolve_runtime_blockers"
    elif watch_runtime_gates:
        if any("runtime_edge_status=warn" in x for x in watch_runtime_gates):
            reason_code = "runtime_edge_warn"
        elif any("runtime_budget_status=warn" in x for x in watch_runtime_gates):
            reason_code = "runtime_budget_warn"
        elif any("runtime_variance_status" in x for x in watch_runtime_gates):
            reason_code = "runtime_variance_watch"
        elif any("runtime_watch_triage_status" in x for x in watch_runtime_gates):
            reason_code = "runtime_watch_triage_watch"
        else:
            reason_code = "runtime_watch_gate"

        if any("=warn" in x for x in watch_runtime_gates):
            status = "warn"
            recommendation = "optimize_before_release"
            next_action = "profile_slow_tests"
        else:
            status = "watch"
            recommendation = "monitor"
            next_action = "watch_next_cycle"
    else:
        status = "pass"
        reason_code = "runtime_healthy"
        recommendation = "ok"
        next_action = "manual_next_release"

    return {
        "schema_version": "v1",
        "status": status,
        "reason_code": reason_code,
        "current_runtime_edge_status": edge_status,
        "current_fast_total_seconds": timing.get("total_seconds"),
        "remaining_budget_seconds": edge.get("remaining_budget_seconds"),
        "remaining_budget_ratio": edge.get("remaining_budget_ratio"),
        "runtime_budget_status": budget_status,
        "timing_consistency_status": timing_consistency_status,
        "runtime_variance_status": variance_status,
        "runtime_watch_triage_status": triage_status,
        "pytest_runtime_profile_status": profile_status,
        "blocking_runtime_gates": blocking_runtime_gates,
        "watch_runtime_gates": watch_runtime_gates,
        "non_blocking_notes": non_blocking_notes,
        "release_cycle_recommendation": recommendation,
        "next_review_trigger": next_action,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_runtime_release_cycle_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Runtime Release-Cycle Monitor",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- Reason code: `{payload.get('reason_code')}`",
            f"- Current runtime edge: `{payload.get('current_runtime_edge_status')}`",
            f"- Current fast total seconds: `{payload.get('current_fast_total_seconds')}`",
            f"- Remaining budget seconds: `{payload.get('remaining_budget_seconds')}`",
            f"- Remaining budget ratio: `{payload.get('remaining_budget_ratio')}`",
            f"- Runtime budget status: `{payload.get('runtime_budget_status')}`",
            f"- Timing consistency status: `{payload.get('timing_consistency_status')}`",
            f"- Runtime variance status: `{payload.get('runtime_variance_status')}`",
            f"- Runtime watch triage status: `{payload.get('runtime_watch_triage_status')}`",
            f"- Recommendation: `{payload.get('release_cycle_recommendation')}`",
            f"- Next review trigger: `{payload.get('next_review_trigger')}`",
            "",
            "## Blocking Runtime Gates",
            "",
            *([f"- {x}" for x in payload.get("blocking_runtime_gates", [])] if payload.get("blocking_runtime_gates") else ["- none"]),
            "",
            "## Watch Runtime Gates",
            "",
            *([f"- {x}" for x in payload.get("watch_runtime_gates", [])] if payload.get("watch_runtime_gates") else ["- none"]),
            "",
            "## Non-blocking Notes",
            "",
            *([f"- {x}" for x in payload.get("non_blocking_notes", [])] if payload.get("non_blocking_notes") else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
