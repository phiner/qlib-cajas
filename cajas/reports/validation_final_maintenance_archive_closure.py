"""Final maintenance freeze/archive closure report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any



def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))



def _safe(path: Path | None) -> dict[str, Any]:
    if path and path.exists():
        return _load_json(path)
    return {}



def build_validation_final_maintenance_archive_closure(
    *,
    maintenance_checklist_report: Path | None = None,
    maintenance_governance_closure_report: Path | None = None,
    external_consumer_evidence_closure_report: Path | None = None,
    optional_followups_report: Path | None = None,
    release_readiness_report: Path | None = None,
    final_reviewer_packet_report: Path | None = None,
    milestone_packet_report: Path | None = None,
    alias_post_removal_closure_report: Path | None = None,
    runtime_release_cycle_report: Path | None = None,
    runtime_budget_report: Path | None = None,
    runtime_variance_closure_report: Path | None = None,
) -> dict[str, Any]:
    checklist = _safe(maintenance_checklist_report)
    governance = _safe(maintenance_governance_closure_report)
    external = _safe(external_consumer_evidence_closure_report)
    followups = _safe(optional_followups_report)
    readiness = _safe(release_readiness_report)
    reviewer = _safe(final_reviewer_packet_report)
    milestone = _safe(milestone_packet_report)
    alias = _safe(alias_post_removal_closure_report)
    runtime_cycle = _safe(runtime_release_cycle_report)
    runtime_budget = _safe(runtime_budget_report)
    runtime_variance = _safe(runtime_variance_closure_report)

    active_followups = []
    for item in followups.get("items", []):
        if isinstance(item, dict) and item.get("status") in {"open", "optional", "watch"}:
            active_followups.append(item.get("id", "unknown"))

    blocking = False
    blocking_reasons: list[str] = []
    if readiness.get("status") == "blocked":
        blocking = True
        blocking_reasons.append("release_readiness_blocked")
    if reviewer.get("status") == "blocked":
        blocking = True
        blocking_reasons.append("final_reviewer_blocked")
    if milestone.get("blocking") is True:
        blocking = True
        blocking_reasons.append("milestone_blocking")
    if external.get("blocking") is True or external.get("status") == "fail":
        blocking = True
        blocking_reasons.append("external_consumer_evidence_blocking")

    canonical_only_confirmed = alias.get("status") == "closed"
    legacy_kept = alias.get("legacy_read_normalization_kept") is True or readiness.get("legacy_read_normalization_kept") is True
    alias_work_remaining = False

    if blocking:
        status = "fail"
    elif readiness.get("status") == "ready" and canonical_only_confirmed and not alias_work_remaining:
        status = "ready"
    else:
        status = "watch"

    canonical_artifacts = checklist.get("canonical_artifacts", [])
    if not isinstance(canonical_artifacts, list):
        canonical_artifacts = []

    superseded_historical_gates = []
    if readiness.get("superseded_watch_items"):
        superseded_historical_gates = list(readiness.get("superseded_watch_items"))

    routine_commands = [
        "python cajas/scripts/run_fast_validation.py",
        "python cajas/scripts/audit_data_sources.py",
        "python cajas/scripts/audit_validation_runtime.py",
        "python cajas/scripts/check_path_hygiene.py",
    ]

    return {
        "schema_version": "v1",
        "status": status,
        "review_state": "ready_for_review" if not blocking else "blocked",
        "blocking": blocking,
        "maintenance_mode": "frozen_routine",
        "archive_closure": "closed" if status in {"ready", "watch"} else "watch",
        "release_ready": readiness.get("status") == "ready" and not blocking,
        "canonical_only_confirmed": canonical_only_confirmed,
        "legacy_read_normalization_kept": legacy_kept,
        "alias_migration_active_work_remaining": alias_work_remaining,
        "runtime_monitoring_cadence": "next_release_cycle",
        "canonical_review_surface": {
            "artifact_count": len(canonical_artifacts),
            "artifacts": canonical_artifacts,
        },
        "superseded_historical_gates": sorted(set(superseded_historical_gates)),
        "active_followups": active_followups,
        "routine_maintenance_commands": routine_commands,
        "scope_boundary": {
            "offline_validation_only": True,
            "qlib_core_modified": False,
            "trading_execution_added": False,
        },
        "runtime_summary": {
            "runtime_release_cycle_status": runtime_cycle.get("status"),
            "runtime_budget_status": runtime_budget.get("overall_status"),
            "runtime_variance_closure_status": runtime_variance.get("status"),
        },
        "blocking_reasons": blocking_reasons,
    }



def render_validation_final_maintenance_archive_closure_markdown(payload: dict[str, Any]) -> str:
    surface = payload.get("canonical_review_surface", {})
    scope = payload.get("scope_boundary", {})
    return "\n".join(
        [
            "# Validation Final Maintenance Archive Closure",
            "",
            f"- status: `{payload.get('status')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- maintenance_mode: `{payload.get('maintenance_mode')}`",
            f"- archive_closure: `{payload.get('archive_closure')}`",
            f"- release_ready: `{payload.get('release_ready')}`",
            f"- canonical_only_confirmed: `{payload.get('canonical_only_confirmed')}`",
            f"- legacy_read_normalization_kept: `{payload.get('legacy_read_normalization_kept')}`",
            f"- alias_migration_active_work_remaining: `{payload.get('alias_migration_active_work_remaining')}`",
            "",
            "## Canonical Review Surface",
            "",
            f"- artifact_count: `{surface.get('artifact_count', 0)}`",
            *[f"- `{item}`" for item in surface.get("artifacts", [])],
            "",
            "## Active Followups",
            "",
            *([f"- {item}" for item in payload.get("active_followups", [])] if payload.get("active_followups") else ["- none"]),
            "",
            "## Routine Maintenance Commands",
            "",
            *[f"- `{cmd}`" for cmd in payload.get("routine_maintenance_commands", [])],
            "",
            "## Scope Boundary",
            "",
            f"- offline_validation_only: `{scope.get('offline_validation_only')}`",
            f"- qlib_core_modified: `{scope.get('qlib_core_modified')}`",
            f"- trading_execution_added: `{scope.get('trading_execution_added')}`",
            "",
        ]
    )
