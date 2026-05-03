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
    consumer_owner_response_validation: Path | None = None,
    consumer_evidence_candidate_report: Path | None = None,
    evidence_candidate_approval_report: Path | None = None,
    alias_sunset_schedule: Path | None = None,
    canonical_evidence_update_plan: Path | None = None,
    canonical_evidence_apply_report: Path | None = None,
    applied_evidence_readiness: Path | None = None,
    alias_fallback_removal_readiness: Path | None = None,
    runtime_watch_triage_report: Path | None = None,
    pytest_runtime_profile: Path | None = None,
    alias_post_removal_closure: Path | None = None,
    release_ready_closure: Path | None = None,
    final_reviewer_packet: Path | None = None,
    maintenance_cadence: Path | None = None,
    maintenance_checklist: Path | None = None,
    optional_followups: Path | None = None,
) -> dict[str, Any]:
    milestone = _load_json(milestone_packet)
    alias = _load_json(alias_sunset_review)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    runtime_variance = _load_json(runtime_variance_report)
    runtime_edge = _load_json(runtime_edge_report)
    runtime_budget = _load_json(runtime_budget_report)
    removal_plan = _load_json(alias_removal_plan) if alias_removal_plan and alias_removal_plan.exists() else {}
    evidence_closure = _load_json(consumer_evidence_closure_report) if consumer_evidence_closure_report and consumer_evidence_closure_report.exists() else {}
    owner_handoff = _load_json(consumer_owner_handoff) if consumer_owner_handoff and consumer_owner_handoff.exists() else {}
    owner_response_validation = _load_json(consumer_owner_response_validation) if consumer_owner_response_validation and consumer_owner_response_validation.exists() else {}
    evidence_candidate = _load_json(consumer_evidence_candidate_report) if consumer_evidence_candidate_report and consumer_evidence_candidate_report.exists() else {}
    candidate_approval = _load_json(evidence_candidate_approval_report) if evidence_candidate_approval_report and evidence_candidate_approval_report.exists() else {}
    sunset_schedule = _load_json(alias_sunset_schedule) if alias_sunset_schedule and alias_sunset_schedule.exists() else {}
    update_plan = _load_json(canonical_evidence_update_plan) if canonical_evidence_update_plan and canonical_evidence_update_plan.exists() else {}
    apply_report = _load_json(canonical_evidence_apply_report) if canonical_evidence_apply_report and canonical_evidence_apply_report.exists() else {}
    applied_readiness = _load_json(applied_evidence_readiness) if applied_evidence_readiness and applied_evidence_readiness.exists() else {}
    fallback_removal_readiness = _load_json(alias_fallback_removal_readiness) if alias_fallback_removal_readiness and alias_fallback_removal_readiness.exists() else {}
    runtime_watch_triage = _load_json(runtime_watch_triage_report) if runtime_watch_triage_report and runtime_watch_triage_report.exists() else {}
    runtime_profile = _load_json(pytest_runtime_profile) if pytest_runtime_profile and pytest_runtime_profile.exists() else {}
    post_removal_closure = _load_json(alias_post_removal_closure) if alias_post_removal_closure and alias_post_removal_closure.exists() else {}
    final_release_closure = _load_json(release_ready_closure) if release_ready_closure and release_ready_closure.exists() else {}
    reviewer_packet = _load_json(final_reviewer_packet) if final_reviewer_packet and final_reviewer_packet.exists() else {}
    cadence_packet = _load_json(maintenance_cadence) if maintenance_cadence and maintenance_cadence.exists() else {}
    checklist_packet = _load_json(maintenance_checklist) if maintenance_checklist and maintenance_checklist.exists() else {}
    followups_packet = _load_json(optional_followups) if optional_followups and optional_followups.exists() else {}

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
    owner_response_status = owner_response_validation.get("status")
    evidence_candidate_status = evidence_candidate.get("status")
    candidate_approval_status = candidate_approval.get("status")
    sunset_schedule_status = sunset_schedule.get("status")
    update_plan_status = update_plan.get("status")
    apply_report_status = apply_report.get("status")
    applied_readiness_status = applied_readiness.get("status")

    fallback_removal_status = fallback_removal_readiness.get("status")
    fallback_removed = fallback_removal_readiness.get("fallback_removed")
    active_alias_emission_supported = fallback_removal_readiness.get("active_alias_emission_supported")
    legacy_read_normalization_kept = fallback_removal_readiness.get("legacy_read_normalization_kept")
    fallback_post_removal_status = fallback_removal_readiness.get("post_removal_status")

    closure_status = post_removal_closure.get("status")
    closure_release_readiness_status = post_removal_closure.get("release_readiness_status")
    final_release_closure_status = final_release_closure.get("status")

    post_removal_mode = (
        fallback_removed is True
        and fallback_post_removal_status == "pass"
        and legacy_read_normalization_kept is True
    )

    supersedable_watch_items = {
        "alias_sunset_decision_gate=watch",
        "alias_removal_plan_status=not_ready",
        "consumer_evidence_closure_status=incomplete",
        "consumer_owner_handoff_status=open",
        "consumer_owner_response_status=incomplete",
        "evidence_candidate_approval_status=approval_required",
        "alias_sunset_schedule_status=not_scheduled",
        "canonical_evidence_update_plan_status=not_ready",
    }

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
    if fallback_post_removal_status == "fail":
        blocking_items.append("alias_fallback_post_removal_status=fail")
    if post_removal_mode and closure_status == "blocked":
        blocking_items.append("alias_post_removal_closure_status=blocked")

    if alias_gate_status == "watch":
        watch_items.append("alias_sunset_decision_gate=watch")
    if runtime_cycle_status in {"watch", "warn"}:
        watch_items.append(f"runtime_release_cycle_status={runtime_cycle_status}")
    if runtime_variance_status in {"watch", "warn"}:
        watch_items.append(f"runtime_variance_status={runtime_variance_status}")
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
    if owner_response_status in {"incomplete", "invalid", "valid_requires_alias"}:
        watch_items.append(f"consumer_owner_response_status={owner_response_status}")
    if runtime_watch_triage_status in {"watch", "warn", "fail"}:
        watch_items.append(f"runtime_watch_triage_status={runtime_watch_triage_status}")
    if candidate_approval_status in {"approval_required", "blocked", "invalid"}:
        watch_items.append(f"evidence_candidate_approval_status={candidate_approval_status}")
    if sunset_schedule_status in {"not_scheduled", "blocked"}:
        watch_items.append(f"alias_sunset_schedule_status={sunset_schedule_status}")
    if update_plan_status in {"not_ready", "blocked"}:
        watch_items.append(f"canonical_evidence_update_plan_status={update_plan_status}")
    if apply_report_status in {"blocked", "invalid"}:
        watch_items.append(f"canonical_evidence_apply_report_status={apply_report_status}")
    if applied_readiness_status in {"watch", "blocked"}:
        watch_items.append(f"applied_evidence_readiness_status={applied_readiness_status}")
    if fallback_removal_status in {"not_ready", "blocked"}:
        watch_items.append(f"alias_fallback_removal_readiness_status={fallback_removal_status}")

    superseded_watch_items: list[str] = []
    if post_removal_mode:
        superseded_watch_items = [x for x in watch_items if x in supersedable_watch_items]
        watch_items = [x for x in watch_items if x not in supersedable_watch_items]

    remaining_watch_items = list(watch_items)

    if blocking_items:
        status = "blocked"
        release_readiness_reason = "; ".join(blocking_items)
        next_actions.extend(["resolve_blocking_gates", "keep_fallback"])
    elif watch_items:
        status = "watch"
        release_readiness_reason = "; ".join(watch_items)
        next_actions.extend((alias.get("decision_gate") or {}).get("next_actions", []))
        if not next_actions:
            next_actions.extend(["collect_consumer_evidence", "keep_fallback"])
    elif post_removal_mode and closure_release_readiness_status == "ready":
        status = "ready"
        release_readiness_reason = "post-removal closure indicates release ready; pre-removal watch items superseded"
        next_actions.append("proceed_release_cycle_review")
    elif milestone_status == "watch" and post_removal_mode:
        status = "ready"
        release_readiness_reason = "post-removal mode active with no remaining watch/blocking gates"
        next_actions.append("proceed_release_cycle_review")
    elif milestone_status == "watch":
        status = "watch"
        release_readiness_reason = "milestone_status=watch"
        next_actions.extend(["collect_consumer_evidence", "keep_fallback"])
    else:
        status = "ready"
        release_readiness_reason = "all required gates pass and alias sunset decision gate is ready"
        next_actions.append("proceed_release_cycle_review")

    if final_release_closure_status == "blocked" and status != "blocked":
        status = "blocked"
        release_readiness_reason = "release_ready_closure_status=blocked"
        next_actions = ["resolve_blocking_gates"]

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
        "consumer_owner_response_status": owner_response_status,
        "consumer_owner_response_safe_to_update": owner_response_validation.get("safe_to_update_evidence"),
        "consumer_owner_response_issues": owner_response_validation.get("issues", []),
        "consumer_evidence_candidate_status": evidence_candidate_status,
        "consumer_evidence_candidate_projected_release_status": evidence_candidate.get("release_readiness_projected_status"),
        "consumer_evidence_candidate_manual_approval_required": evidence_candidate.get("manual_approval_required"),
        "consumer_evidence_candidate_next_action": evidence_candidate.get("next_action"),
        "evidence_candidate_approval_status": candidate_approval_status,
        "evidence_candidate_approval_next_action": candidate_approval.get("next_action"),
        "alias_sunset_schedule_status": sunset_schedule_status,
        "alias_sunset_schedule_reason": sunset_schedule.get("reason"),
        "alias_sunset_schedule_next_steps": sunset_schedule.get("schedule_steps", []),
        "canonical_evidence_update_plan_status": update_plan_status,
        "canonical_evidence_update_plan_recommendation": update_plan.get("recommendation"),
        "canonical_evidence_update_plan_manual_update_required": update_plan.get("manual_update_required"),
        "canonical_evidence_apply_report_status": apply_report_status,
        "canonical_evidence_apply_report_next_action": apply_report.get("next_action"),
        "canonical_evidence_apply_report_alias_fallback_removal_allowed": apply_report.get("alias_fallback_removal_allowed"),
        "applied_evidence_readiness_status": applied_readiness_status,
        "applied_evidence_readiness_next_action": applied_readiness.get("next_action"),
        "alias_fallback_removal_readiness_status": fallback_removal_status,
        "fallback_removed": fallback_removed,
        "active_alias_emission_supported": active_alias_emission_supported,
        "legacy_read_normalization_kept": legacy_read_normalization_kept,
        "alias_fallback_post_removal_status": fallback_post_removal_status,
        "post_removal_mode": post_removal_mode,
        "superseded_watch_items": superseded_watch_items,
        "remaining_watch_items": remaining_watch_items,
        "release_ready_after_post_removal": bool(post_removal_mode and status == "ready" and not blocking_items),
        "alias_post_removal_closure_status": closure_status,
        "release_ready_closure_status": final_release_closure_status,
        "release_ready_closure_recommendation": final_release_closure.get("recommendation"),
        "release_ready_closure_remaining_blockers": final_release_closure.get("remaining_blockers", []),
        "release_ready_closure_remaining_followups": final_release_closure.get("remaining_followups", []),
        "final_reviewer_packet_status": reviewer_packet.get("status"),
        "final_reviewer_packet_primary_artifacts": reviewer_packet.get("primary_artifacts", []),
        "final_reviewer_packet_remaining_followups": reviewer_packet.get("remaining_followups", []),
        "maintenance_cadence_status": cadence_packet.get("status"),
        "maintenance_cadence_recommended_cadence": cadence_packet.get("recommended_cadence"),
        "maintenance_cadence_routine_commands": cadence_packet.get("routine_commands", []),
        "maintenance_cadence_watch_items": cadence_packet.get("watch_items", []),
        "maintenance_checklist_status": checklist_packet.get("status"),
        "maintenance_checklist_mode": checklist_packet.get("mode"),
        "maintenance_checklist_optional_followup_count": checklist_packet.get("optional_followup_count"),
        "optional_followups_status": followups_packet.get("status"),
        "optional_followups_count": len(followups_packet.get("items", [])),
        "optional_followups_blocking": followups_packet.get("blocking", False),
        "alias_fallback_removal_readiness_preconditions_met": fallback_removal_readiness.get("preconditions_met"),
        "alias_fallback_removal_readiness_do_not_remove_in_this_phase": fallback_removal_readiness.get("do_not_remove_in_this_phase"),
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
            f"- Alias sunset decision gate: `{payload.get('alias_sunset_decision_gate_status', 'watch')}`",
            f"- Runtime release-cycle: `{payload.get('runtime_release_cycle_status', 'watch')}`",
            f"- Runtime variance: `{payload.get('runtime_variance_status', 'watch')}`",
            f"- Post-removal mode: `{payload.get('post_removal_mode')}`",
            f"- Alias post-removal closure status: `{payload.get('alias_post_removal_closure_status')}`",
            f"- Final release-ready closure status: `{payload.get('release_ready_closure_status')}`",
            f"- Final reviewer packet status: `{payload.get('final_reviewer_packet_status')}`",
            f"- Maintenance cadence status: `{payload.get('maintenance_cadence_status', 'not_included')}`",
            f"- Maintenance cadence recommended: `{payload.get('maintenance_cadence_recommended_cadence', 'n/a')}`",
            f"- Maintenance checklist status: `{payload.get('maintenance_checklist_status', 'not_included')}`",
            f"- Optional followups count: `{payload.get('optional_followups_count', 0)}`",
            f"- Release ready after post-removal: `{payload.get('release_ready_after_post_removal')}`",
            "",
            "## Watch Items",
            "",
            *([f"- {item}" for item in watch_items] if watch_items else ["- none"]),
            "",
            "## Superseded Watch Items",
            "",
            *([f"- {item}" for item in payload.get("superseded_watch_items", [])] if payload.get("superseded_watch_items") else ["- none"]),
            "",
            "## Remaining Watch Items",
            "",
            *([f"- {item}" for item in payload.get("remaining_watch_items", [])] if payload.get("remaining_watch_items") else ["- none"]),
            "",
            "## Blocking Items",
            "",
            *([f"- {item}" for item in blocking_items] if blocking_items else ["- none"]),
            "",
            "## Next Actions",
            "",
            *[f"- {item}" for item in payload.get("next_actions", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
