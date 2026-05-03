"""Maintenance governance closure summary for routine release-cycle posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_maintenance_governance_closure(
    *,
    maintenance_checklist: Path,
    optional_followups: Path,
    release_readiness_report: Path,
    milestone_packet: Path,
    final_reviewer_packet: Path,
    alias_post_removal_closure: Path,
    runtime_release_cycle_report: Path | None = None,
    runtime_variance_closure_report: Path | None = None,
) -> dict[str, Any]:
    checklist = _load_json(maintenance_checklist)
    followups = _load_json(optional_followups)
    readiness = _load_json(release_readiness_report)
    milestone = _load_json(milestone_packet)
    reviewer = _load_json(final_reviewer_packet)
    alias_closure = _load_json(alias_post_removal_closure)
    runtime_cycle = _load_json(runtime_release_cycle_report) if runtime_release_cycle_report and runtime_release_cycle_report.exists() else {}
    runtime_variance_closure = _load_json(runtime_variance_closure_report) if runtime_variance_closure_report and runtime_variance_closure_report.exists() else {}

    blocking_reasons: list[str] = []
    if checklist.get("status") == "blocked":
        blocking_reasons.append("maintenance_checklist_status=blocked")
    if readiness.get("status") == "blocked":
        blocking_reasons.append("release_readiness_status=blocked")
    if milestone.get("blocking") is True:
        blocking_reasons.append("milestone_blocking=true")
    if reviewer.get("status") == "blocked":
        blocking_reasons.append("final_reviewer_packet_status=blocked")
    if alias_closure.get("status") == "blocked":
        blocking_reasons.append("alias_post_removal_closure_status=blocked")
    if followups.get("blocking") is True:
        blocking_reasons.append("optional_followups_blocking=true")
    if runtime_cycle.get("status") == "fail":
        blocking_reasons.append("runtime_release_cycle_status=fail")
    if runtime_variance_closure.get("status") == "blocked":
        blocking_reasons.append("runtime_variance_closure_status=blocked")

    if blocking_reasons:
        conclusion = "blocked"
    elif (
        checklist.get("status") == "ready"
        and readiness.get("status") == "ready"
        and reviewer.get("status") == "ready_for_review"
        and milestone.get("review_state") == "ready_for_review"
        and milestone.get("blocking") is False
        and alias_closure.get("status") == "closed"
    ):
        conclusion = "routine"
    elif followups.get("status") == "open" and followups.get("blocking") is False:
        conclusion = "watch_non_blocking"
    else:
        conclusion = "ready_for_review"

    status = "blocked" if conclusion == "blocked" else "ready"
    if conclusion == "watch_non_blocking":
        status = "watch"

    return {
        "schema_version": "v1",
        "status": status,
        "conclusion": conclusion,
        "maintenance_checklist_status": checklist.get("status"),
        "optional_followups_status": followups.get("status"),
        "optional_followups_count": len(followups.get("items", [])),
        "optional_followups_blocking": followups.get("blocking", False),
        "release_readiness_status": readiness.get("status"),
        "milestone_overall_status": milestone.get("overall_status"),
        "milestone_review_state": milestone.get("review_state"),
        "milestone_blocking": milestone.get("blocking"),
        "final_reviewer_packet_status": reviewer.get("status"),
        "alias_post_removal_closure_status": alias_closure.get("status"),
        "runtime_release_cycle_status": runtime_cycle.get("status"),
        "runtime_variance_closure_status": runtime_variance_closure.get("status"),
        "blocking_reasons": blocking_reasons,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_maintenance_governance_closure_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Maintenance Governance Closure",
            "",
            f"- status: `{payload.get('status')}`",
            f"- conclusion: `{payload.get('conclusion')}`",
            f"- maintenance_checklist_status: `{payload.get('maintenance_checklist_status')}`",
            f"- optional_followups_status: `{payload.get('optional_followups_status')}`",
            f"- optional_followups_count: `{payload.get('optional_followups_count')}`",
            f"- optional_followups_blocking: `{payload.get('optional_followups_blocking')}`",
            f"- release_readiness_status: `{payload.get('release_readiness_status')}`",
            f"- milestone_review_state: `{payload.get('milestone_review_state')}`",
            f"- milestone_blocking: `{payload.get('milestone_blocking')}`",
            f"- final_reviewer_packet_status: `{payload.get('final_reviewer_packet_status')}`",
            f"- alias_post_removal_closure_status: `{payload.get('alias_post_removal_closure_status')}`",
            "",
            "## Blocking Reasons",
            "",
            *([f"- {x}" for x in payload.get("blocking_reasons", [])] if payload.get("blocking_reasons") else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
