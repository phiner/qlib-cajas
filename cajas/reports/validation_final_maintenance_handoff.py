"""Final maintenance handoff and manual GitHub merge readiness report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return _load_json(path)


def _state(payload: dict[str, Any], key: str, default: str = "missing") -> str:
    value = payload.get(key, default)
    return value if isinstance(value, str) else default


def build_validation_final_maintenance_handoff(
    *,
    branch: str,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    milestone_packet: Path,
    routine_stability_watch_closure: Path | None = None,
    post_freeze_handoff_seal_report: Path | None = None,
    final_maintenance_archive_closure_report: Path | None = None,
    external_consumer_evidence_closure_report: Path | None = None,
    alias_post_removal_closure_report: Path | None = None,
    optional_followups_report: Path | None = None,
) -> dict[str, Any]:
    readiness = _safe(release_readiness_report)
    reviewer = _safe(final_reviewer_packet)
    milestone = _safe(milestone_packet)
    watch_closure = _safe(routine_stability_watch_closure)
    handoff_seal = _safe(post_freeze_handoff_seal_report)
    archive = _safe(final_maintenance_archive_closure_report)
    external = _safe(external_consumer_evidence_closure_report)
    alias_post = _safe(alias_post_removal_closure_report)
    followups = _safe(optional_followups_report)

    readiness_status = _state(readiness, "status")
    reviewer_status = _state(reviewer, "status")
    milestone_review_state = _state(milestone, "review_state")
    milestone_blocking = bool(milestone.get("blocking", False))
    routine_watch_closure_status = _state(watch_closure, "status")
    handoff_seal_status = _state(handoff_seal, "status")
    archive_status = _state(archive, "status")
    external_status = _state(external, "status")
    alias_post_status = _state(alias_post, "status")

    followup_items = followups.get("active_items", followups.get("items", []))
    if not isinstance(followup_items, list):
        followup_items = []
    followup_names: list[str] = []
    for item in followup_items:
        if isinstance(item, dict):
            followup_names.append(str(item.get("id") or item.get("reason") or "unnamed_followup"))
        else:
            followup_names.append(str(item))
    optional_followup_count = len(followup_items)
    optional_followups_blocking = bool(followups.get("blocking", False))

    missing_required = readiness_status == "missing" or reviewer_status == "missing" or milestone_review_state == "missing"

    blocked = (
        missing_required
        or readiness_status != "ready"
        or reviewer_status != "ready_for_review"
        or milestone_blocking
        or optional_followups_blocking
    )
    ready_for_manual = (
        not blocked
        and alias_post_status == "closed"
        and routine_watch_closure_status in {"closed_non_blocking", "missing"}
        and handoff_seal_status in {"sealed", "missing"}
    )

    if blocked:
        status = "blocked"
        review_state = "blocked"
    elif ready_for_manual:
        status = "ready_for_manual_github_merge"
        review_state = "ready_for_review"
    else:
        status = "watch"
        review_state = "watch"

    human_actions = [
        "Review branch and artifacts on GitHub.",
        "Verify final validation artifacts and non-blocking followup context.",
        "Merge manually on GitHub if acceptable.",
        "Codex/local scripts must not perform automated merge operations.",
    ]

    return {
        "schema_version": 1,
        "status": status,
        "review_state": review_state,
        "blocking": status == "blocked",
        "manual_merge_required": True,
        "merge_method": "manual_github",
        "branch": branch,
        "release_readiness_status": readiness_status,
        "final_reviewer_packet_status": reviewer_status,
        "milestone_review_state": milestone_review_state,
        "milestone_blocking": milestone_blocking,
        "routine_watch_closure_status": routine_watch_closure_status,
        "post_freeze_handoff_seal_status": handoff_seal_status,
        "final_archive_closure_status": archive_status,
        "external_consumer_evidence_closure_status": external_status,
        "alias_post_removal_closure_status": alias_post_status,
        "optional_followup_summary": {
            "count": optional_followup_count,
            "blocking": optional_followups_blocking,
            "active_items": followup_names,
        },
        "scope_boundary": {
            "qlib_core_changes": False,
            "trading_execution": False,
            "broker_routing": False,
            "live_or_paper_trading": False,
            "training_workflow_execution": False,
        },
        "human_actions": human_actions,
    }


def render_validation_final_maintenance_handoff_markdown(payload: dict[str, Any]) -> str:
    followups = payload.get("optional_followup_summary", {})
    return "\n".join(
        [
            "# Validation Final Maintenance Handoff",
            "",
            f"- status: `{payload.get('status')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- manual_merge_required: `{payload.get('manual_merge_required')}`",
            f"- merge_method: `{payload.get('merge_method')}`",
            f"- branch: `{payload.get('branch')}`",
            f"- release_readiness_status: `{payload.get('release_readiness_status')}`",
            f"- final_reviewer_packet_status: `{payload.get('final_reviewer_packet_status')}`",
            f"- milestone_review_state: `{payload.get('milestone_review_state')}`",
            f"- milestone_blocking: `{payload.get('milestone_blocking')}`",
            f"- routine_watch_closure_status: `{payload.get('routine_watch_closure_status')}`",
            f"- post_freeze_handoff_seal_status: `{payload.get('post_freeze_handoff_seal_status')}`",
            f"- final_archive_closure_status: `{payload.get('final_archive_closure_status')}`",
            f"- external_consumer_evidence_closure_status: `{payload.get('external_consumer_evidence_closure_status')}`",
            f"- alias_post_removal_closure_status: `{payload.get('alias_post_removal_closure_status')}`",
            "",
            "## Optional Followups",
            "",
            f"- count: `{followups.get('count')}`",
            f"- blocking: `{followups.get('blocking')}`",
            f"- active_items: `{followups.get('active_items', [])}`",
            "",
            "## Manual GitHub Merge Instruction",
            "",
            "- Merge must be performed manually by a human reviewer on GitHub.",
            "- Do not run automated merge operations from Codex or local scripts.",
            "",
            "## Human Actions",
            "",
            *[f"- {x}" for x in payload.get("human_actions", [])],
            "",
            "## Scope Boundary",
            "",
            f"- `{payload.get('scope_boundary', {})}`",
            "",
        ]
    )
