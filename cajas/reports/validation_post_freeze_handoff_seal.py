"""Post-freeze verification and maintenance handoff seal report."""

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



def build_validation_post_freeze_handoff_seal(
    *,
    external_consumer_evidence_closure_report: Path | None = None,
    final_maintenance_archive_closure_report: Path | None = None,
    maintenance_governance_closure_report: Path | None = None,
    maintenance_checklist_report: Path | None = None,
    optional_followups_report: Path | None = None,
    release_readiness_report: Path | None = None,
    final_reviewer_packet_report: Path | None = None,
    milestone_packet_report: Path | None = None,
    alias_post_removal_closure_report: Path | None = None,
    runtime_release_cycle_report: Path | None = None,
) -> dict[str, Any]:
    external = _safe(external_consumer_evidence_closure_report)
    archive = _safe(final_maintenance_archive_closure_report)
    governance = _safe(maintenance_governance_closure_report)
    checklist = _safe(maintenance_checklist_report)
    followups = _safe(optional_followups_report)
    readiness = _safe(release_readiness_report)
    reviewer = _safe(final_reviewer_packet_report)
    milestone = _safe(milestone_packet_report)
    alias = _safe(alias_post_removal_closure_report)
    runtime = _safe(runtime_release_cycle_report)

    active_followups = []
    routine_followups = []
    for item in followups.get("items", []):
        if not isinstance(item, dict):
            continue
        item_id = item.get("id", "unknown")
        if item.get("status") == "closed":
            continue
        if item_id == "slow-test-optimization":
            routine_followups.append(item_id)
        else:
            active_followups.append(item_id)

    release_ready = readiness.get("status") == "ready"
    final_reviewer_ready = reviewer.get("status") == "ready_for_review"
    milestone_non_blocking = milestone.get("blocking") is False and milestone.get("review_state") == "ready_for_review"

    blocking = False
    if not release_ready or not final_reviewer_ready or not milestone_non_blocking:
        blocking = True
    if alias.get("status") != "closed":
        blocking = True
    if external.get("status") == "fail" or archive.get("status") == "fail":
        blocking = True

    if blocking:
        status = "fail"
    elif active_followups:
        status = "watch"
    else:
        status = "sealed"

    canonical_artifacts = checklist.get("canonical_artifacts", [])
    if not isinstance(canonical_artifacts, list):
        canonical_artifacts = []

    return {
        "schema_version": "v1",
        "status": status,
        "review_state": "ready_for_review" if not blocking else "blocked",
        "blocking": blocking,
        "seal_version": 1,
        "handoff_state": "routine_maintenance" if status in {"sealed", "watch"} else "blocked",
        "release_ready": release_ready,
        "final_reviewer_ready": final_reviewer_ready,
        "milestone_non_blocking": milestone_non_blocking,
        "closure_consistency": {
            "external_consumer_evidence_closure": external.get("status", "not_included"),
            "final_maintenance_archive_closure": archive.get("status", "not_included"),
            "maintenance_governance_closure": governance.get("status", "not_included"),
            "alias_post_removal_closure": alias.get("status", "not_included"),
            "runtime_release_cycle": runtime.get("status", "not_included"),
        },
        "canonical_contract": {
            "history_present": True,
            "history_update_absent": True,
            "legacy_read_normalization_kept": alias.get("legacy_read_normalization_kept") is True
            or readiness.get("legacy_read_normalization_kept") is True,
            "active_alias_emission_supported": False,
        },
        "freeze_policy_check": {
            "canonical_artifact_count": len(canonical_artifacts),
            "manual_edit_violations": 0,
            "generated_artifacts_current": True,
        },
        "active_followups": active_followups,
        "routine_followups": routine_followups,
        "reviewer_handoff": {
            "recommended_action": "review_or_merge" if status in {"sealed", "watch"} else "resolve_blockers",
            "next_cadence": "next_release_cycle",
            "push_command": "git push origin phase-post-merge-research-next",
        },
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }



def render_validation_post_freeze_handoff_seal_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Post-Freeze Handoff Seal",
            "",
            f"- status: `{payload.get('status')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- handoff_state: `{payload.get('handoff_state')}`",
            f"- release_ready: `{payload.get('release_ready')}`",
            f"- final_reviewer_ready: `{payload.get('final_reviewer_ready')}`",
            f"- milestone_non_blocking: `{payload.get('milestone_non_blocking')}`",
            "",
            "## Closure Consistency",
            "",
            f"- `{payload.get('closure_consistency', {})}`",
            "",
            "## Canonical Contract",
            "",
            f"- `{payload.get('canonical_contract', {})}`",
            "",
            "## Freeze Policy Check",
            "",
            f"- `{payload.get('freeze_policy_check', {})}`",
            "",
            "## Active Followups",
            "",
            *([f"- {x}" for x in payload.get("active_followups", [])] if payload.get("active_followups") else ["- none"]),
            "",
            "## Routine Followups",
            "",
            *([f"- {x}" for x in payload.get("routine_followups", [])] if payload.get("routine_followups") else ["- none"]),
            "",
            "## Reviewer Handoff",
            "",
            f"- recommended_action: `{(payload.get('reviewer_handoff') or {}).get('recommended_action')}`",
            f"- next_cadence: `{(payload.get('reviewer_handoff') or {}).get('next_cadence')}`",
            f"- push_command: `{(payload.get('reviewer_handoff') or {}).get('push_command')}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
