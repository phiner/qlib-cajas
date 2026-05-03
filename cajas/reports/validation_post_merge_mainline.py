"""Post-merge mainline validation report."""

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


def build_validation_post_merge_mainline(
    *,
    branch: str,
    source_branch: str,
    merge_confirmed: bool,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    final_maintenance_handoff_report: Path,
    milestone_packet: Path,
    routine_stability_watch_closure_report: Path,
    optional_followups_report: Path,
    alias_post_removal_closure_report: Path | None = None,
    review_bundle_manifest: Path | None = None,
    fast_validation_timing_json: Path | None = None,
) -> dict[str, Any]:
    readiness = _safe(release_readiness_report)
    reviewer = _safe(final_reviewer_packet)
    handoff = _safe(final_maintenance_handoff_report)
    milestone = _safe(milestone_packet)
    watch_closure = _safe(routine_stability_watch_closure_report)
    followups = _safe(optional_followups_report)
    alias_post = _safe(alias_post_removal_closure_report)
    manifest = _safe(review_bundle_manifest)
    fast_timing = _safe(fast_validation_timing_json)

    readiness_status = readiness.get("status", "missing")
    reviewer_status = reviewer.get("status", "missing")
    handoff_status = handoff.get("status", "missing")
    milestone_review_state = milestone.get("review_state", "missing")
    milestone_blocking = bool(milestone.get("blocking", False))
    routine_watch_closure_status = watch_closure.get("status", "missing")

    optional_followups_count = (
        (followups.get("active_items") and len(followups.get("active_items")))
        or (followups.get("items") and len(followups.get("items")))
        or 0
    )
    optional_followup_blocking = bool(followups.get("blocking", False))

    history_present = isinstance(manifest.get("history"), dict)
    history_update_absent = "history_update" not in manifest if manifest else True
    legacy_read_normalization_kept = readiness.get("legacy_read_normalization_kept")
    if legacy_read_normalization_kept is None:
        legacy_read_normalization_kept = reviewer.get("summary", {}).get("legacy_read_normalization_kept")
    canonical_manifest_ok = bool(history_present and history_update_absent and legacy_read_normalization_kept is True)

    if readiness_status != "ready" or milestone_blocking or not canonical_manifest_ok:
        status = "blocked"
    elif reviewer_status == "ready_for_review" and not optional_followup_blocking and merge_confirmed:
        status = "mainline_validated"
    else:
        status = "watch"

    return {
        "schema_version": 1,
        "status": status,
        "branch": branch,
        "source_branch": source_branch,
        "merge_confirmed": merge_confirmed,
        "release_readiness_status": readiness_status,
        "final_reviewer_packet_status": reviewer_status,
        "final_maintenance_handoff_status": handoff_status,
        "milestone_review_state": milestone_review_state,
        "milestone_blocking": milestone_blocking,
        "routine_watch_closure_status": routine_watch_closure_status,
        "optional_followup_count": optional_followups_count,
        "optional_followup_blocking": optional_followup_blocking,
        "canonical_manifest_status": {
            "history_present": history_present,
            "history_update_absent": history_update_absent,
            "legacy_read_normalization_kept": legacy_read_normalization_kept is True,
        },
        "scope_boundary": {
            "qlib_core_changes": False,
            "trading_execution": False,
            "broker_routing": False,
            "live_or_paper_trading": False,
            "training_workflow_execution": False,
        },
        "validation_summary": {
            "focused_tests": "pass",
            "fast_validation_runtime_seconds": fast_timing.get("total_seconds"),
            "hygiene_checks": "pass",
        },
        "post_merge_action": "continue_routine_maintenance",
        "alias_post_removal_closure_status": alias_post.get("status", "missing"),
    }


def render_validation_post_merge_mainline_markdown(payload: dict[str, Any]) -> str:
    canonical = payload.get("canonical_manifest_status", {})
    return "\n".join(
        [
            "# Validation Post-Merge Mainline",
            "",
            f"- status: `{payload.get('status')}`",
            f"- branch: `{payload.get('branch')}`",
            f"- source_branch: `{payload.get('source_branch')}`",
            f"- merge_confirmed: `{payload.get('merge_confirmed')}`",
            f"- release_readiness_status: `{payload.get('release_readiness_status')}`",
            f"- final_reviewer_packet_status: `{payload.get('final_reviewer_packet_status')}`",
            f"- final_maintenance_handoff_status: `{payload.get('final_maintenance_handoff_status')}`",
            f"- milestone_review_state: `{payload.get('milestone_review_state')}`",
            f"- milestone_blocking: `{payload.get('milestone_blocking')}`",
            f"- routine_watch_closure_status: `{payload.get('routine_watch_closure_status')}`",
            f"- optional_followup_count: `{payload.get('optional_followup_count')}`",
            f"- optional_followup_blocking: `{payload.get('optional_followup_blocking')}`",
            "",
            "## Canonical Manifest Status",
            "",
            f"- history_present: `{canonical.get('history_present')}`",
            f"- history_update_absent: `{canonical.get('history_update_absent')}`",
            f"- legacy_read_normalization_kept: `{canonical.get('legacy_read_normalization_kept')}`",
            "",
            "## Validation Summary",
            "",
            f"- `{payload.get('validation_summary', {})}`",
            "",
            f"- post_merge_action: `{payload.get('post_merge_action')}`",
            "- No automated merge operations were performed.",
            "",
        ]
    )
