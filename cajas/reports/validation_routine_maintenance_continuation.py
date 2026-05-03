"""Routine maintenance continuation report."""

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


def build_validation_routine_maintenance_continuation(
    *,
    post_merge_mainline_report: Path,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    milestone_packet: Path,
    optional_followups_report: Path | None = None,
    review_bundle_manifest: Path | None = None,
) -> dict[str, Any]:
    mainline = _safe(post_merge_mainline_report)
    readiness = _safe(release_readiness_report)
    reviewer = _safe(final_reviewer_packet)
    milestone = _safe(milestone_packet)
    followups = _safe(optional_followups_report)
    manifest = _safe(review_bundle_manifest)

    release_readiness_status = readiness.get("status", "missing")
    final_reviewer_status = reviewer.get("status", "missing")
    milestone_review_state = milestone.get("review_state", "missing")
    milestone_blocking = bool(milestone.get("blocking", False))
    mainline_status = mainline.get("status", "missing")

    items = followups.get("active_items", followups.get("items", []))
    if not isinstance(items, list):
        items = []
    remaining = []
    for item in items:
        if isinstance(item, dict):
            remaining.append(str(item.get("id") or item.get("reason") or "unnamed_followup"))
        else:
            remaining.append(str(item))
    optional_count = len(items)
    optional_blocking = bool(followups.get("blocking", False))

    history_present = isinstance(manifest.get("history"), dict)
    history_update_absent = "history_update" not in manifest if manifest else True
    legacy_kept = readiness.get("legacy_read_normalization_kept")
    if legacy_kept is None:
        legacy_kept = reviewer.get("summary", {}).get("legacy_read_normalization_kept")
    canonical_ok = bool(history_present and history_update_absent and legacy_kept is True)

    if release_readiness_status != "ready" or milestone_blocking or not canonical_ok:
        status = "blocked"
        review_state = "blocked"
        blocking = True
    elif final_reviewer_status == "ready_for_review" and not optional_blocking:
        status = "routine_continues"
        review_state = "ready_for_review"
        blocking = False
    else:
        status = "watch"
        review_state = "watch"
        blocking = False

    return {
        "schema_version": 1,
        "status": status,
        "review_state": review_state,
        "blocking": blocking,
        "repo_posture": {
            "fork_relationship": "kept",
            "upstream_sync_planned": False,
            "repo_migration_planned": False,
            "manual_merge_policy": "github_only",
        },
        "mainline_validation_status": mainline_status,
        "release_readiness_status": release_readiness_status,
        "final_reviewer_packet_status": final_reviewer_status,
        "milestone_review_state": milestone_review_state,
        "milestone_blocking": milestone_blocking,
        "optional_followup_count": optional_count,
        "optional_followup_blocking": optional_blocking,
        "remaining_optional_followups": remaining,
        "canonical_manifest_status": {
            "history_present": history_present,
            "history_update_absent": history_update_absent,
            "legacy_read_normalization_kept": legacy_kept is True,
        },
        "scope_boundary": {
            "qlib_core_changes": False,
            "trading_execution": False,
            "broker_routing": False,
            "live_or_paper_trading": False,
            "training_workflow_execution": False,
            "upstream_sync_in_this_phase": False,
            "repo_migration_in_this_phase": False,
        },
        "next_cadence": "routine_next_release_cycle",
        "recommended_next_actions": [
            "monitor routine validation runtime",
            "keep optional slow-test optimization non-blocking",
            "evaluate upstream sync only in a dedicated future audit branch when explicitly requested",
        ],
    }


def render_validation_routine_maintenance_continuation_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Routine Maintenance Continuation",
            "",
            f"- status: `{payload.get('status')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- mainline_validation_status: `{payload.get('mainline_validation_status')}`",
            f"- release_readiness_status: `{payload.get('release_readiness_status')}`",
            f"- final_reviewer_packet_status: `{payload.get('final_reviewer_packet_status')}`",
            f"- milestone_review_state: `{payload.get('milestone_review_state')}`",
            f"- milestone_blocking: `{payload.get('milestone_blocking')}`",
            f"- optional_followup_count: `{payload.get('optional_followup_count')}`",
            f"- optional_followup_blocking: `{payload.get('optional_followup_blocking')}`",
            "",
            "## Repo Posture",
            "",
            f"- `{payload.get('repo_posture', {})}`",
            "",
            "## Canonical Manifest Status",
            "",
            f"- `{payload.get('canonical_manifest_status', {})}`",
            "",
            "## Next Cadence",
            "",
            f"- `{payload.get('next_cadence')}`",
            "",
            "## Recommended Next Actions",
            "",
            *[f"- {x}" for x in payload.get("recommended_next_actions", [])],
            "",
            "## Policy",
            "",
            "- Routine maintenance continues; fork relationship is kept.",
            "- No upstream sync is planned in this phase.",
            "- No automated merge operations were performed.",
            "",
        ]
    )
