"""Release readiness dashboard report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_release_readiness_report(
    *,
    milestone_packet: Path,
    alias_sunset_review: Path,
    runtime_release_cycle_report: Path,
    runtime_variance_report: Path,
    runtime_edge_report: Path,
    runtime_budget_report: Path,
    alias_removal_plan: Path | None = None,
    consumer_evidence_closure_report: Path | None = None,
    consumer_owner_handoff: Path | None = None,
    runtime_watch_triage_report: Path | None = None,
    pytest_runtime_profile: Path | None = None,
) -> dict[str, Any]:
    milestone = _load_json(milestone_packet)
    alias = _load_json(alias_sunset_review)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    runtime_variance = _load_json(runtime_variance_report)
    runtime_edge = _load_json(runtime_edge_report)
    runtime_budget = _load_json(runtime_budget_report)
    removal_plan = _load_json(alias_removal_plan) if alias_removal_plan and alias_removal_plan.exists() else {}
    evidence_closure = (
        _load_json(consumer_evidence_closure_report)
        if consumer_evidence_closure_report and consumer_evidence_closure_report.exists()
        else {}
    )
    owner_handoff = _load_json(consumer_owner_handoff) if consumer_owner_handoff and consumer_owner_handoff.exists() else {}
    runtime_watch_triage = (
        _load_json(runtime_watch_triage_report)
        if runtime_watch_triage_report and runtime_watch_triage_report.exists()
        else {}
    )
    runtime_profile = _load_json(pytest_runtime_profile) if pytest_runtime_profile and pytest_runtime_profile.exists() else {}

    alias_status = alias.get("status", "watch")
    alias_gate_status = (alias.get("decision_gate") or {}).get("status", alias_status)
    runtime_cycle_status = runtime_cycle.get("status", "watch")
    runtime_variance_status = runtime_variance.get("status", "watch")
    runtime_edge_status = runtime_edge.get("status", "watch")
    runtime_budget_status = runtime_budget.get("overall_status", "warn")
    timing_consistency_status = (runtime_budget.get("timing_consistency") or {}).get("status", "warn")
    milestone_status = milestone.get("overall_status", "watch")
    migration_status = (milestone.get("alias_migration_summary") or {}).get("status", "warn")
    removal_plan_status = removal_plan.get("status")
    evidence_closure_status = evidence_closure.get("status")
    runtime_watch_triage_status = runtime_watch_triage.get("status")
    owner_handoff_status = owner_handoff.get("status")

    required_gates = [
        {"name": "runtime_budget", "status": runtime_budget_status},
        {"name": "timing_consistency", "status": timing_consistency_status},
        {"name": "runtime_edge", "status": runtime_edge_status},
        {"name": "runtime_release_cycle", "status": runtime_cycle_status},
        {"name": "runtime_variance", "status": runtime_variance_status},
        {"name": "alias_migration_readiness", "status": migration_status},
        {"name": "alias_sunset_decision_gate", "status": alias_gate_status},
    ]

    blocking_items: list[str] = []
    watch_items: list[str] = []
    next_actions: list[str] = []

    if runtime_budget_status == "fail":
        blocking_items.append("runtime_budget_status=fail")
    if timing_consistency_status == "fail":
        blocking_items.append("timing_consistency_status=fail")
    if runtime_edge_status == "fail":
        blocking_items.append("runtime_edge_status=fail")
    if runtime_cycle_status == "fail":
        blocking_items.append("runtime_release_cycle_status=fail")
    if runtime_variance_status == "fail":
        blocking_items.append("runtime_variance_status=fail")
    if migration_status == "fail":
        blocking_items.append("alias_migration_readiness_status=fail")
    if alias_gate_status == "blocked":
        blocking_items.append("alias_sunset_decision_gate=blocked")

    if alias_gate_status == "watch":
        watch_items.append("alias_sunset_decision_gate=watch")
    if runtime_cycle_status == "watch":
        watch_items.append("runtime_release_cycle_status=watch")
    if runtime_variance_status == "watch":
        watch_items.append("runtime_variance_status=watch")
    if runtime_edge_status == "watch":
        watch_items.append("runtime_edge_status=watch")
    if runtime_budget_status == "warn":
        watch_items.append("runtime_budget_status=warn")
    if timing_consistency_status == "warn":
        watch_items.append("timing_consistency_status=warn")
    if migration_status == "warn":
        watch_items.append("alias_migration_readiness_status=warn")
    if removal_plan_status in {"not_ready", "blocked"}:
        watch_items.append(f"alias_removal_plan_status={removal_plan_status}")
    if evidence_closure_status in {"incomplete", "blocked"}:
        watch_items.append(f"consumer_evidence_closure_status={evidence_closure_status}")
    if owner_handoff_status in {"open", "blocked"}:
        watch_items.append(f"consumer_owner_handoff_status={owner_handoff_status}")
    if runtime_watch_triage_status in {"watch", "warn", "fail"}:
        watch_items.append(f"runtime_watch_triage_status={runtime_watch_triage_status}")

    if blocking_items:
        status = "blocked"
        release_readiness_reason = "; ".join(blocking_items)
        next_actions.extend(["resolve_blocking_gates", "keep_fallback"])
    elif watch_items or milestone_status == "watch":
        status = "watch"
        release_readiness_reason = "; ".join(watch_items or ["milestone_status=watch"])
        next_actions.extend((alias.get("decision_gate") or {}).get("next_actions", []))
        if not next_actions:
            next_actions.extend(["collect_consumer_evidence", "keep_fallback"])
    else:
        status = "ready"
        release_readiness_reason = "all required gates pass and alias sunset decision gate is ready"
        next_actions.append("proceed_release_cycle_review")

    primary_artifacts = [
        str(milestone_packet),
        str(alias_sunset_review),
        str(runtime_release_cycle_report),
        str(runtime_variance_report),
        str(runtime_edge_report),
        str(runtime_budget_report),
    ]

    return {
        "schema_version": "v1",
        "status": status,
        "release_readiness_reason": release_readiness_reason,
        "alias_sunset_status": alias_status,
        "alias_sunset_decision_gate_status": alias_gate_status,
        "runtime_release_cycle_status": runtime_cycle_status,
        "runtime_variance_status": runtime_variance_status,
        "runtime_edge_status": runtime_edge_status,
        "runtime_budget_status": runtime_budget_status,
        "timing_consistency_status": timing_consistency_status,
        "milestone_status": milestone_status,
        "alias_removal_plan_status": removal_plan_status,
        "alias_removal_plan_recommendation": removal_plan.get("recommendation"),
        "alias_removal_plan_remaining_blockers": removal_plan.get("remaining_blockers", []),
        "consumer_evidence_closure_status": evidence_closure_status,
        "consumer_evidence_closure_next_actions": evidence_closure.get("next_actions", []),
        "consumer_evidence_action_plan": evidence_closure.get("action_plan", []),
        "consumer_owner_handoff_status": owner_handoff_status,
        "consumer_owner_handoff_blocking_consumer_count": owner_handoff.get("blocking_consumer_count"),
        "consumer_owner_handoff_items": owner_handoff.get("handoff_items", []),
        "consumer_owner_handoff_message": owner_handoff.get("recommended_message"),
        "runtime_watch_triage_status": runtime_watch_triage_status,
        "runtime_watch_triage_recommendation": runtime_watch_triage.get("recommendation"),
        "runtime_watch_triage_test_count": runtime_watch_triage.get("test_count"),
        "runtime_watch_triage_seconds_per_test": runtime_watch_triage.get("seconds_per_test"),
        "pytest_runtime_profile_status": runtime_profile.get("status"),
        "pytest_runtime_profile_recommendation": runtime_profile.get("recommendation"),
        "pytest_runtime_profile_test_summary": runtime_profile.get("test_summary"),
        "pytest_runtime_profile_slowest_tests": runtime_profile.get("slowest_tests", []),
        "pytest_runtime_profile_slowest_files": runtime_profile.get("slowest_files", []),
        "required_gates": required_gates,
        "watch_items": watch_items,
        "blocking_items": blocking_items,
        "next_actions": sorted(set(next_actions)),
        "primary_artifacts": primary_artifacts,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_release_readiness_markdown(payload: dict[str, Any]) -> str:
    watch_items = payload.get("watch_items", [])
    blocking_items = payload.get("blocking_items", [])
    return "\n".join(
        [
            "# Validation Release Readiness Dashboard",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- Reason: `{payload.get('release_readiness_reason', '')}`",
            f"- Alias sunset: `{payload.get('alias_sunset_status', 'watch')}`",
            f"- Alias decision gate: `{payload.get('alias_sunset_decision_gate_status', 'watch')}`",
            f"- Runtime release-cycle: `{payload.get('runtime_release_cycle_status', 'watch')}`",
            f"- Runtime variance: `{payload.get('runtime_variance_status', 'watch')}`",
            f"- Milestone status: `{payload.get('milestone_status', 'watch')}`",
            f"- Alias removal plan: `{payload.get('alias_removal_plan_status', 'not_included')}`",
            f"- Consumer evidence closure: `{payload.get('consumer_evidence_closure_status', 'not_included')}`",
            f"- Consumer owner handoff: `{payload.get('consumer_owner_handoff_status', 'not_included')}`",
            f"- Runtime watch triage: `{payload.get('runtime_watch_triage_status', 'not_included')}`",
            f"- Runtime watch triage test_count: `{payload.get('runtime_watch_triage_test_count', 'n/a')}`",
            f"- Pytest runtime profile: `{payload.get('pytest_runtime_profile_status', 'not_included')}`",
            "",
            "## Watch Items",
            "",
            *([f"- {item}" for item in watch_items] if watch_items else ["- none"]),
            "",
            "## Blocking Items",
            "",
            *([f"- {item}" for item in blocking_items] if blocking_items else ["- none"]),
            "",
            "## Next Actions",
            "",
            *[f"- {item}" for item in payload.get("next_actions", [])],
            *[
                f"- removal_plan_blocker: {item}"
                for item in payload.get("alias_removal_plan_remaining_blockers", [])
            ],
            "",
            "## Primary Artifacts",
            "",
            *[f"- `{item}`" for item in payload.get("primary_artifacts", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
