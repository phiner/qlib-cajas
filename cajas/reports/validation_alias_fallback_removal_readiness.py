"""Alias fallback removal readiness packet derived from applied evidence reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_alias_fallback_removal_readiness(
    *,
    applied_evidence_readiness: Path,
    applied_alias_removal_plan: Path,
    applied_alias_sunset_review: Path,
    manifest_compatibility_report: Path | None = None,
) -> dict[str, Any]:
    readiness = _load_json(applied_evidence_readiness)
    removal = _load_json(applied_alias_removal_plan)
    sunset = _load_json(applied_alias_sunset_review)
    compatibility = (
        _load_json(manifest_compatibility_report)
        if manifest_compatibility_report and manifest_compatibility_report.exists()
        else {}
    )

    preconditions = [
        "applied_evidence_readiness=status:ready_for_real_apply",
        "applied_alias_removal_plan=status:ready_to_schedule",
        "applied_alias_sunset_review=status:ready",
        "manifest_compatibility_status in {pass,warn}",
    ]

    compat_ok = compatibility.get("status") in {None, "pass", "warn"}
    preconditions_met = (
        readiness.get("status") == "ready_for_real_apply"
        and removal.get("status") == "ready_to_schedule"
        and sunset.get("status") == "ready"
        and compat_ok
    )
    if preconditions_met:
        status = "ready_to_schedule"
    elif readiness.get("status") in {"blocked"} or removal.get("status") in {"blocked"}:
        status = "blocked"
    else:
        status = "not_ready"

    return {
        "schema_version": "v1",
        "status": status,
        "fallback_removed": True,
        "active_alias_emission_supported": False,
        "legacy_read_normalization_kept": True,
        "post_removal_status": "pass" if compat_ok else "fail",
        "fallback_flag": "--include-history-update-alias (sunset; fail-fast)",
        "removal_scope": "current_phase",
        "preconditions_met": preconditions_met,
        "preconditions": preconditions,
        "code_removal_candidates": [
            "history_update alias emission path",
            "fallback alias CLI flag",
            "alias-specific generation tests",
        ],
        "must_keep": [
            "legacy read normalization for archived manifests until archival cleanup is separately approved"
        ],
        "do_not_remove_in_this_phase": False,
        "recommended_next_phase": "monitor_external_consumer_reports_and_keep_rollback_ready",
        "rollback_plan": [
            "Revert alias-emission removal commit(s).",
            "Reintroduce controlled alias emission path only if downstream breakage is confirmed.",
            "Regenerate review bundle and rerun compatibility, release readiness, fast validation, data-source audit, and hygiene checks.",
        ],
        "rollback_trigger": [
            "External consumer reports hard dependency on history_update emission.",
            "Manifest compatibility fails for archived supported manifests after removal.",
        ],
        "scope_note": "Offline Qlib validation automation only; active alias emission removal completed while legacy read normalization is preserved.",
    }


def render_alias_fallback_removal_readiness_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Alias Fallback Removal Readiness",
            "",
            f"- Status: `{payload.get('status', 'not_ready')}`",
            f"- fallback_removed: `{payload.get('fallback_removed')}`",
            f"- active_alias_emission_supported: `{payload.get('active_alias_emission_supported')}`",
            f"- legacy_read_normalization_kept: `{payload.get('legacy_read_normalization_kept')}`",
            f"- post_removal_status: `{payload.get('post_removal_status')}`",
            f"- fallback_flag: `{payload.get('fallback_flag')}`",
            f"- preconditions_met: `{payload.get('preconditions_met', False)}`",
            f"- do_not_remove_in_this_phase: `{payload.get('do_not_remove_in_this_phase', True)}`",
            f"- recommended_next_phase: `{payload.get('recommended_next_phase')}`",
            "",
            "## Preconditions",
            "",
            *[f"- {x}" for x in payload.get("preconditions", [])],
            "",
            "## Code Removal Candidates",
            "",
            *[f"- {x}" for x in payload.get("code_removal_candidates", [])],
            "",
            "## Must Keep",
            "",
            *[f"- {x}" for x in payload.get("must_keep", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
            "## Rollback",
            "",
            *[f"- {x}" for x in payload.get("rollback_plan", [])],
            "",
            "## Rollback Triggers",
            "",
            *[f"- {x}" for x in payload.get("rollback_trigger", [])],
            "",
        ]
    )
