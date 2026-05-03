"""Alias fallback removal plan report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_future_removal_steps() -> list[str]:
    return [
        "remove --include-history-update-alias emission path",
        "remove history_update generation tests",
        "keep legacy read fallback for archived manifests until separate cleanup",
        "update docs and release notes",
    ]


def build_alias_removal_plan(
    *,
    alias_sunset_review: Path,
    migration_readiness_report: Path,
    release_readiness_report: Path | None = None,
) -> dict[str, Any]:
    sunset = _load_json(alias_sunset_review)
    migration = _load_json(migration_readiness_report)
    release = _load_json(release_readiness_report) if release_readiness_report and release_readiness_report.exists() else {}

    sunset_status = sunset.get("status", "watch")
    decision_gate = sunset.get("decision_gate") or {}
    migration_status = migration.get("status", "warn")
    release_status = release.get("status")

    removal_preconditions = [
        "alias_sunset_status=ready",
        "alias_decision_gate_required_evidence_complete=true",
        "migration_readiness_status=pass",
        "consumers_requiring_alias_count=0",
    ]

    remaining_blockers: list[str] = []
    if sunset_status != "ready":
        remaining_blockers.append(f"alias_sunset_status={sunset_status}")
    if not decision_gate.get("required_evidence_complete", False):
        remaining_blockers.append("required_evidence_complete=false")
    if migration_status != "pass":
        remaining_blockers.append(f"migration_readiness_status={migration_status}")
    if sunset.get("requires_alias_count", 0) > 0:
        remaining_blockers.append("consumers_requiring_alias_count>0")

    preconditions_met = len(remaining_blockers) == 0
    if sunset_status == "blocked":
        status = "blocked"
    elif preconditions_met:
        status = "ready_to_schedule"
    else:
        status = "not_ready"

    if status == "ready_to_schedule":
        recommendation = "schedule_removal_phase"
        do_not_remove_yet_reason = "Removal should happen in a dedicated follow-up phase with explicit change control."
    else:
        recommendation = "keep_fallback"
        do_not_remove_yet_reason = "; ".join(remaining_blockers) if remaining_blockers else "preconditions not met"

    return {
        "schema_version": "v1",
        "status": status,
        "sunset_status": sunset_status,
        "removal_preconditions": removal_preconditions,
        "preconditions_met": preconditions_met,
        "remaining_blockers": remaining_blockers,
        "future_removal_steps": _build_future_removal_steps(),
        "do_not_remove_yet_reason": do_not_remove_yet_reason,
        "recommendation": recommendation,
        "release_readiness_status": release_status,
        "scope_note": "Offline Qlib validation automation only; this phase does not remove fallback.",
    }


def render_alias_removal_plan_markdown(payload: dict[str, Any]) -> str:
    remaining_blockers = payload.get("remaining_blockers", [])
    return "\n".join(
        [
            "# History Alias Removal Plan",
            "",
            f"- Status: `{payload.get('status', 'not_ready')}`",
            f"- Sunset status: `{payload.get('sunset_status', 'watch')}`",
            f"- Preconditions met: `{payload.get('preconditions_met', False)}`",
            f"- Recommendation: `{payload.get('recommendation', 'keep_fallback')}`",
            f"- Do not remove yet reason: `{payload.get('do_not_remove_yet_reason', '')}`",
            "",
            "## Remaining Blockers",
            "",
            *([f"- {item}" for item in remaining_blockers] if remaining_blockers else ["- none"]),
            "",
            "## Future Removal Steps",
            "",
            *[f"- {item}" for item in payload.get("future_removal_steps", [])],
            "",
            "## Non-Goal",
            "",
            "- This phase prepares removal planning only and does not remove alias fallback.",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
