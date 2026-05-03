"""Routine stability watch closure and interpretation report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return _load_json(path)


def _infer_followup_type(items: list[Any]) -> str:
    text = json.dumps(items, ensure_ascii=True).lower()
    if "slow" in text and "test" in text:
        return "slow_test_optimization"
    if "runtime" in text and "variance" in text:
        return "runtime_variance_monitoring"
    return "unspecified_maintenance_followup"


def build_validation_routine_stability_watch_closure(
    *,
    routine_release_cycle_stability_report: Path,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    milestone_packet: Path,
    optional_followups_report: Path | None = None,
) -> dict[str, Any]:
    stability = _load_json(routine_release_cycle_stability_report)
    readiness = _load_json(release_readiness_report)
    reviewer = _load_json(final_reviewer_packet)
    milestone = _load_json(milestone_packet)
    followups = _optional_json(optional_followups_report)

    stability_status = stability.get("status")
    readiness_status = readiness.get("status")
    reviewer_status = reviewer.get("status")
    milestone_review_state = milestone.get("review_state")
    milestone_blocking = bool(milestone.get("blocking", False))
    followup_items = followups.get("active_items", followups.get("items", []))
    followup_count = len(followup_items) if isinstance(followup_items, list) else 0
    followup_blocking = bool(followups.get("blocking", False))
    remaining_followup_type = _infer_followup_type(followup_items) if followup_count else "none"

    reasons: list[str] = []
    if readiness_status != "ready":
        reasons.append("release_readiness_not_ready")
    if reviewer_status != "ready_for_review":
        reasons.append("final_reviewer_packet_not_ready_for_review")
    if milestone_review_state != "ready_for_review":
        reasons.append("milestone_review_state_not_ready_for_review")
    if milestone_blocking:
        reasons.append("milestone_blocking_true")
    if followup_blocking:
        reasons.append("optional_followups_blocking_true")
    if stability.get("blocking") is True or stability_status == "blocked":
        reasons.append("routine_stability_blocked")

    if not reasons and stability_status == "watch":
        status = "closed_non_blocking"
        review_state = "ready_for_review"
        blocking = False
        reason_code = "routine_optional_followup_only"
        interpretation = "Routine stability watch is a non-blocking maintenance signal, not a release blocker."
        next_action = "monitor_next_release_cycle"
    elif reasons:
        status = "blocked"
        review_state = "blocked"
        blocking = True
        reason_code = "closure_blocked_by_required_gate"
        interpretation = "Routine stability watch closure cannot be treated as non-blocking until required readiness gates are healthy."
        next_action = "resolve_blocking_gates"
    else:
        status = "watch"
        review_state = "watch"
        blocking = bool(followup_blocking)
        reason_code = "watch_semantics_pending_confirmation"
        interpretation = "Routine stability requires continued watch monitoring before closure can be marked non-blocking."
        next_action = "monitor_next_release_cycle"

    if not followups:
        reasons.append("optional_followups_report_missing")

    return {
        "schema_version": 1,
        "status": status,
        "review_state": review_state,
        "blocking": blocking,
        "reason_code": reason_code,
        "reason_details": sorted(set(reasons)),
        "stability_status": stability_status,
        "release_readiness_status": readiness_status,
        "final_reviewer_packet_status": reviewer_status,
        "milestone_review_state": milestone_review_state,
        "milestone_blocking": milestone_blocking,
        "optional_followup_count": followup_count,
        "optional_followups_blocking": followup_blocking,
        "remaining_followup_type": remaining_followup_type,
        "interpretation": interpretation,
        "next_action": next_action,
        "scope_boundary": {
            "qlib_core_changes": False,
            "trading_execution": False,
            "broker_routing": False,
            "training_workflow_execution": False,
        },
    }


def render_validation_routine_stability_watch_closure_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Routine Stability Watch Closure",
            "",
            f"- status: `{payload.get('status')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- reason_code: `{payload.get('reason_code')}`",
            f"- stability_status: `{payload.get('stability_status')}`",
            f"- release_readiness_status: `{payload.get('release_readiness_status')}`",
            f"- final_reviewer_packet_status: `{payload.get('final_reviewer_packet_status')}`",
            f"- milestone_review_state: `{payload.get('milestone_review_state')}`",
            f"- optional_followup_count: `{payload.get('optional_followup_count')}`",
            f"- optional_followups_blocking: `{payload.get('optional_followups_blocking')}`",
            f"- remaining_followup_type: `{payload.get('remaining_followup_type')}`",
            "",
            "## Interpretation",
            "",
            f"- {payload.get('interpretation', '')}",
            "",
            "## Next Action",
            "",
            f"- `{payload.get('next_action')}`",
            "",
            "## Reason Details",
            "",
            *([f"- {item}" for item in payload.get("reason_details", [])] if payload.get("reason_details") else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- `{payload.get('scope_boundary', {})}`",
            "",
        ]
    )
