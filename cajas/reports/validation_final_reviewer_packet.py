"""Final reviewer packet report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_final_reviewer_packet(
    *,
    release_ready_closure: Path,
    alias_post_removal_closure: Path,
    runtime_variance_closure: Path,
    release_readiness_report: Path,
    milestone_packet: Path,
    review_bundle_manifest: Path,
    manifest_compatibility_report: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    data_source_audit_report: Path,
    maintenance_cadence: Path | None = None,
    maintenance_checklist: Path | None = None,
    optional_followups: Path | None = None,
    maintenance_governance_closure: Path | None = None,
    external_consumer_governance: Path | None = None,
    external_consumer_evidence_closure_report: Path | None = None,
    final_maintenance_archive_closure_report: Path | None = None,
    post_freeze_handoff_seal_report: Path | None = None,
    routine_release_cycle_stability_report: Path | None = None,
    routine_stability_watch_closure: Path | None = None,
    final_maintenance_handoff_report: Path | None = None,
) -> dict[str, Any]:
    final_closure = _load_json(release_ready_closure)
    alias_closure = _load_json(alias_post_removal_closure)
    variance_closure = _load_json(runtime_variance_closure)
    readiness = _load_json(release_readiness_report)
    milestone = _load_json(milestone_packet)
    manifest = _load_json(review_bundle_manifest)
    compat = _load_json(manifest_compatibility_report)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)
    audit = _load_json(data_source_audit_report)
    cadence = _load_json(maintenance_cadence) if maintenance_cadence and maintenance_cadence.exists() else {}
    checklist = _load_json(maintenance_checklist) if maintenance_checklist and maintenance_checklist.exists() else {}
    followups_queue = _load_json(optional_followups) if optional_followups and optional_followups.exists() else {}
    governance = _load_json(maintenance_governance_closure) if maintenance_governance_closure and maintenance_governance_closure.exists() else {}
    external_governance = _load_json(external_consumer_governance) if external_consumer_governance and external_consumer_governance.exists() else {}
    external_evidence_closure = _load_json(external_consumer_evidence_closure_report) if external_consumer_evidence_closure_report and external_consumer_evidence_closure_report.exists() else {}
    final_archive_closure = _load_json(final_maintenance_archive_closure_report) if final_maintenance_archive_closure_report and final_maintenance_archive_closure_report.exists() else {}
    post_freeze_handoff = _load_json(post_freeze_handoff_seal_report) if post_freeze_handoff_seal_report and post_freeze_handoff_seal_report.exists() else {}
    routine_stability = _load_json(routine_release_cycle_stability_report) if routine_release_cycle_stability_report and routine_release_cycle_stability_report.exists() else {}
    routine_watch_closure = _load_json(routine_stability_watch_closure) if routine_stability_watch_closure and routine_stability_watch_closure.exists() else {}
    final_handoff = _load_json(final_maintenance_handoff_report) if final_maintenance_handoff_report and final_maintenance_handoff_report.exists() else {}

    canonical_only = isinstance(manifest.get("history"), dict) and "history_update" not in manifest
    legacy_kept = readiness.get("legacy_read_normalization_kept") is True
    read_csv_count = (audit.get("summary") or {}).get("read_csv_count", audit.get("read_csv_count"))

    summary = {
        "canonical_only_manifest": canonical_only,
        "alias_post_removal_closure": alias_closure.get("status"),
        "legacy_read_normalization_kept": legacy_kept,
        "manifest_compatibility": compat.get("status"),
        "runtime_budget": budget.get("overall_status"),
        "runtime_edge": edge.get("status"),
        "runtime_variance_closure": variance_closure.get("status"),
        "data_source_audit_read_csv_count": read_csv_count,
    }

    blockers: list[str] = []
    followups: list[str] = []

    if final_closure.get("blocking") is True or final_closure.get("status") == "blocked":
        blockers.extend(final_closure.get("remaining_blockers", []))
    if compat.get("status") == "fail":
        blockers.append("manifest_compatibility_fail")
    if budget.get("overall_status") == "fail":
        blockers.append("runtime_budget_fail")
    if edge.get("status") == "fail":
        blockers.append("runtime_edge_fail")
    if not canonical_only:
        blockers.append("canonical_manifest_missing_or_alias_present")
    if not legacy_kept:
        blockers.append("legacy_read_normalization_not_kept")

    if variance_closure.get("status") == "monitoring_only":
        followups.append("monitor runtime variance next release cycle")
    followups.extend(final_closure.get("remaining_followups", []))
    followups = sorted(set(followups))

    routine_stability_status = routine_stability.get("status")
    routine_stability_blocking = routine_stability.get("blocking")
    routine_stability_review_state = routine_stability.get("review_state")
    if routine_stability_status == "blocked" or routine_stability_blocking is True or routine_stability_review_state == "blocked":
        blockers.append("routine_release_cycle_stability_blocked")
    closure_status = routine_watch_closure.get("status")
    closure_blocking = routine_watch_closure.get("blocking")
    if closure_status == "blocked" or closure_blocking is True:
        blockers.append("routine_stability_watch_closure_blocked")
    if final_handoff.get("status") == "blocked" or final_handoff.get("blocking") is True:
        blockers.append("final_maintenance_handoff_blocked")

    if blockers:
        status = "blocked"
    elif final_closure.get("ready_for_review") is True:
        status = "ready_for_review"
    else:
        status = "watch"

    return {
        "schema_version": "v1",
        "status": status,
        "summary": summary,
        "maintenance_cadence_status": cadence.get("status"),
        "maintenance_cadence_recommended": cadence.get("recommended_cadence"),
        "maintenance_cadence_routine_commands": cadence.get("routine_commands", []),
        "maintenance_cadence_watch_items": cadence.get("watch_items", []),
        "maintenance_checklist_status": checklist.get("status"),
        "maintenance_checklist_mode": checklist.get("mode"),
        "maintenance_checklist_canonical_artifacts": checklist.get("canonical_artifacts", []),
        "optional_followups_status": followups_queue.get("status"),
        "optional_followups_count": len(followups_queue.get("active_items", followups_queue.get("items", []))),
        "optional_followups_blocking": followups_queue.get("blocking", False),
        "maintenance_governance_closure_status": governance.get("status"),
        "maintenance_governance_closure_conclusion": governance.get("conclusion"),
        "external_consumer_governance_status": external_governance.get("status"),
        "external_consumer_governance_blocking": external_governance.get("blocking"),
        "external_consumer_governance_release_readiness_impact": external_governance.get("release_readiness_impact"),
        "external_consumer_evidence_closure_status": external_evidence_closure.get("status"),
        "external_consumer_evidence_closure_blocking": external_evidence_closure.get("blocking"),
        "final_maintenance_archive_closure_status": final_archive_closure.get("status"),
        "final_maintenance_archive_closure_blocking": final_archive_closure.get("blocking"),
        "post_freeze_handoff_seal_status": post_freeze_handoff.get("status"),
        "post_freeze_handoff_seal_blocking": post_freeze_handoff.get("blocking"),
        "routine_release_cycle_stability_status": routine_stability_status,
        "routine_release_cycle_stability_review_state": routine_stability_review_state,
        "routine_release_cycle_stability_blocking": routine_stability_blocking,
        "routine_stability_watch_closure_status": closure_status,
        "routine_stability_watch_closure_blocking": closure_blocking,
        "routine_stability_watch_closure_interpretation": routine_watch_closure.get("interpretation"),
        "routine_stability_watch_closure_next_action": routine_watch_closure.get("next_action"),
        "final_maintenance_handoff_status": final_handoff.get("status"),
        "final_maintenance_handoff_blocking": final_handoff.get("blocking"),
        "final_maintenance_handoff_manual_merge_required": final_handoff.get("manual_merge_required"),
        "final_maintenance_handoff_merge_method": final_handoff.get("merge_method"),
        "remaining_followups": followups,
        "primary_artifacts": [
            str(release_ready_closure),
            str(release_readiness_report),
            str(milestone_packet),
            str(review_bundle_manifest),
            str(manifest_compatibility_report),
        ],
        "rollback_readiness": "present" if alias_closure.get("status") == "closed" else "unknown",
        "non_goals": [
            "No trading execution",
            "No broker integration",
            "No live/paper execution",
        ],
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_final_reviewer_packet_markdown(payload: dict[str, Any]) -> str:
    s = payload.get("summary", {})
    return "\n".join(
        [
            "# Validation Final Reviewer Packet",
            "",
            f"- Status: `{payload.get('status')}`",
            f"- canonical_only_manifest: `{s.get('canonical_only_manifest')}`",
            f"- alias_post_removal_closure: `{s.get('alias_post_removal_closure')}`",
            f"- legacy_read_normalization_kept: `{s.get('legacy_read_normalization_kept')}`",
            f"- manifest_compatibility: `{s.get('manifest_compatibility')}`",
            f"- runtime_budget: `{s.get('runtime_budget')}`",
            f"- runtime_edge: `{s.get('runtime_edge')}`",
            f"- runtime_variance_closure: `{s.get('runtime_variance_closure')}`",
            f"- data_source_audit_read_csv_count: `{s.get('data_source_audit_read_csv_count')}`",
            "",
            "## Remaining Followups",
            "",
            *([f"- {x}" for x in payload.get("remaining_followups", [])] if payload.get("remaining_followups") else ["- none"]),
            "",
            "## Maintenance Cadence",
            "",
            f"- status: `{payload.get('maintenance_cadence_status', 'not_included')}`",
            f"- recommended_cadence: `{payload.get('maintenance_cadence_recommended', 'n/a')}`",
            f"- routine_command_count: `{len(payload.get('maintenance_cadence_routine_commands', []))}`",
            f"- watch_items: `{payload.get('maintenance_cadence_watch_items', [])}`",
            "",
            "## Maintenance Checklist",
            "",
            f"- status: `{payload.get('maintenance_checklist_status', 'not_included')}`",
            f"- mode: `{payload.get('maintenance_checklist_mode', 'n/a')}`",
            f"- canonical_artifact_count: `{len(payload.get('maintenance_checklist_canonical_artifacts', []))}`",
            "",
            "## Optional Followup Queue",
            "",
            f"- status: `{payload.get('optional_followups_status', 'not_included')}`",
            f"- count: `{payload.get('optional_followups_count', 0)}`",
            f"- blocking: `{payload.get('optional_followups_blocking', False)}`",
            "",
            "## Governance Closure",
            "",
            f"- status: `{payload.get('maintenance_governance_closure_status', 'not_included')}`",
            f"- conclusion: `{payload.get('maintenance_governance_closure_conclusion', 'n/a')}`",
            "",
            "## External Consumer Governance",
            "",
            f"- status: `{payload.get('external_consumer_governance_status', 'not_included')}`",
            f"- blocking: `{payload.get('external_consumer_governance_blocking', False)}`",
            f"- release_readiness_impact: `{payload.get('external_consumer_governance_release_readiness_impact', 'n/a')}`",
            "",
            "## External Consumer Evidence Closure",
            "",
            f"- status: `{payload.get('external_consumer_evidence_closure_status', 'not_included')}`",
            f"- blocking: `{payload.get('external_consumer_evidence_closure_blocking', False)}`",
            "",
            "## Final Maintenance Archive Closure",
            "",
            f"- status: `{payload.get('final_maintenance_archive_closure_status', 'not_included')}`",
            f"- blocking: `{payload.get('final_maintenance_archive_closure_blocking', False)}`",
            "",
            "## Post-Freeze Handoff Seal",
            "",
            f"- status: `{payload.get('post_freeze_handoff_seal_status', 'not_included')}`",
            f"- blocking: `{payload.get('post_freeze_handoff_seal_blocking', False)}`",
            "",
            "## Routine Release-Cycle Stability",
            "",
            f"- status: `{payload.get('routine_release_cycle_stability_status', 'not_included')}`",
            f"- review_state: `{payload.get('routine_release_cycle_stability_review_state', 'n/a')}`",
            f"- blocking: `{payload.get('routine_release_cycle_stability_blocking', False)}`",
            "",
            "## Routine Stability Watch Closure",
            "",
            f"- status: `{payload.get('routine_stability_watch_closure_status', 'not_included')}`",
            f"- blocking: `{payload.get('routine_stability_watch_closure_blocking', False)}`",
            f"- interpretation: `{payload.get('routine_stability_watch_closure_interpretation', 'n/a')}`",
            f"- next_action: `{payload.get('routine_stability_watch_closure_next_action', 'n/a')}`",
            "",
            "## Final Maintenance Handoff",
            "",
            f"- status: `{payload.get('final_maintenance_handoff_status', 'not_included')}`",
            f"- blocking: `{payload.get('final_maintenance_handoff_blocking', False)}`",
            f"- manual_merge_required: `{payload.get('final_maintenance_handoff_manual_merge_required', 'n/a')}`",
            f"- merge_method: `{payload.get('final_maintenance_handoff_merge_method', 'n/a')}`",
            "",
            "## Reviewer Handoff",
            "",
            f"- Status: `{'Ready for review' if payload.get('status') == 'ready_for_review' else payload.get('status')}`",
            "- Canonical manifest policy: `history-only`",
            f"- Alias migration: `{s.get('alias_post_removal_closure')}`",
            f"- Runtime: `budget={s.get('runtime_budget')}; edge={s.get('runtime_edge')}; variance_closure={s.get('runtime_variance_closure')}`",
            f"- Data-source audit: `stable at {s.get('data_source_audit_read_csv_count')} read_csv calls`",
            f"- Next routine action: `run maintenance cadence at {payload.get('maintenance_cadence_recommended', 'next release cycle')}`",
            "",
            "## Primary Artifacts",
            "",
            *[f"- `{x}`" for x in payload.get("primary_artifacts", [])],
            "",
            "## Non-goals",
            "",
            *[f"- {x}" for x in payload.get("non_goals", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
