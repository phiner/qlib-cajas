"""Alias sunset readiness review report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_alias_sunset_review(
    *,
    migration_readiness_report: Path,
    milestone_packet: Path,
    external_consumer_status: str,
) -> dict[str, Any]:
    migration = _load_json(migration_readiness_report)
    milestone = _load_json(milestone_packet)
    alias_fallback = migration.get("alias_fallback", {})

    canonical_default_confirmed = bool(alias_fallback.get("default_emits_alias") is False)
    fallback_flag_available = bool(alias_fallback.get("fallback_flag") == "--include-history-update-alias")
    fallback_alias_reported = "fallback_manifest_has_alias" in alias_fallback
    internal_consumers_clear = migration.get("status") == "pass"

    readiness_pass = migration.get("status") == "pass" and milestone.get("overall_status") == "pass"
    if external_consumer_status == "confirmed_clear" and readiness_pass:
        status = "ready"
        recommended_action = "schedule_removal"
    elif external_consumer_status == "requires_alias":
        status = "blocked"
        recommended_action = "keep_fallback"
    else:
        status = "watch"
        recommended_action = "keep_fallback"

    checks = [
        {"name": "canonical_default_confirmed", "status": "pass" if canonical_default_confirmed else "fail"},
        {"name": "fallback_flag_available", "status": "pass" if fallback_flag_available else "fail"},
        {"name": "fallback_alias_reported", "status": "pass" if fallback_alias_reported else "warn"},
        {"name": "internal_consumers_clear", "status": "pass" if internal_consumers_clear else "warn"},
    ]

    return {
        "schema_version": "v1",
        "status": status,
        "canonical_default_confirmed": canonical_default_confirmed,
        "fallback_flag_available": fallback_flag_available,
        "fallback_alias_reported": fallback_alias_reported,
        "internal_consumers_clear": internal_consumers_clear,
        "external_consumer_confirmation": external_consumer_status,
        "recommended_action": recommended_action,
        "checks": checks,
        "note": "Fallback alias is not removed in this phase.",
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_alias_sunset_review_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# History Alias Sunset Review",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- External consumer confirmation: `{payload.get('external_consumer_confirmation', 'unknown')}`",
            f"- Recommended action: `{payload.get('recommended_action', 'keep_fallback')}`",
            "",
            "## Checklist",
            "",
            "| Check | Status |",
            "|---|---|",
            *[f"| {c.get('name')} | {c.get('status')} |" for c in payload.get("checks", [])],
            "",
            "## Operating Notes",
            "",
            "- Default mode: canonical `history` only.",
            "- Fallback flag: `--include-history-update-alias`.",
            f"- {payload.get('note', '')}",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
