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
) -> dict[str, Any]:
    milestone = _load_json(milestone_packet)
    alias = _load_json(alias_sunset_review)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    runtime_variance = _load_json(runtime_variance_report)
    runtime_edge = _load_json(runtime_edge_report)
    runtime_budget = _load_json(runtime_budget_report)

    alias_status = alias.get("status", "watch")
    alias_gate_status = (alias.get("decision_gate") or {}).get("status", alias_status)
    runtime_cycle_status = runtime_cycle.get("status", "watch")
    runtime_variance_status = runtime_variance.get("status", "watch")
    runtime_edge_status = runtime_edge.get("status", "watch")
    runtime_budget_status = runtime_budget.get("overall_status", "warn")
    timing_consistency_status = (runtime_budget.get("timing_consistency") or {}).get("status", "warn")
    milestone_status = milestone.get("overall_status", "watch")
    migration_status = (milestone.get("alias_migration_summary") or {}).get("status", "warn")

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
