"""Alias sunset scheduling packet built from approval and readiness signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_alias_sunset_schedule(
    *,
    evidence_candidate_approval_report: Path,
    alias_removal_plan: Path,
    release_readiness_report: Path,
    milestone_packet: Path,
) -> dict[str, Any]:
    approval = _load_json(evidence_candidate_approval_report)
    removal = _load_json(alias_removal_plan)
    release = _load_json(release_readiness_report)
    milestone = _load_json(milestone_packet)

    approval_status = approval.get("status")
    removal_status = removal.get("status")

    if approval_status in {"invalid", "blocked"}:
        status = "blocked"
        reason = f"approval_status={approval_status}"
    elif approval_status != "approved_candidate":
        status = "not_scheduled"
        reason = "manual_approval_required"
    elif removal_status == "ready_to_schedule":
        status = "ready_to_schedule"
        reason = "approved_candidate_and_removal_plan_ready"
    else:
        status = "blocked"
        reason = f"alias_removal_plan_status={removal_status}"

    preconditions = [
        "evidence_candidate_approval_status=approved_candidate",
        "alias_removal_plan_status=ready_to_schedule",
        "release_readiness_status=ready",
        "milestone_overall_status in {pass,watch}",
    ]

    return {
        "schema_version": "v1",
        "status": status,
        "reason": reason,
        "preconditions": preconditions,
        "schedule_steps": [
            "Apply approved evidence candidate to canonical evidence file in a dedicated phase.",
            "Regenerate alias sunset review and release readiness.",
            "If ready, schedule removal of --include-history-update-alias in a later phase.",
            "Keep legacy read fallback for archived manifests until separate archival cleanup.",
        ],
        "earliest_safe_phase": "future_after_manual_approval",
        "do_not_remove_in_this_phase": True,
        "approval_status": approval_status,
        "alias_removal_plan_status": removal_status,
        "release_readiness_status": release.get("status"),
        "milestone_overall_status": milestone.get("overall_status"),
        "scope_note": "Offline Qlib validation automation only; this phase does not remove fallback.",
    }


def render_alias_sunset_schedule_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Alias Sunset Scheduling Packet",
            "",
            f"- Status: `{payload.get('status', 'not_scheduled')}`",
            f"- Reason: `{payload.get('reason', '')}`",
            f"- earliest_safe_phase: `{payload.get('earliest_safe_phase')}`",
            f"- do_not_remove_in_this_phase: `{payload.get('do_not_remove_in_this_phase', True)}`",
            "",
            "## Preconditions",
            "",
            *[f"- {item}" for item in payload.get("preconditions", [])],
            "",
            "## Schedule Steps",
            "",
            *[f"- {item}" for item in payload.get("schedule_steps", [])],
            "",
            "## Non-Goal",
            "",
            "- Do not remove fallback in this phase.",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
