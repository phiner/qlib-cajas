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
    external_consumer_status: str | None = None,
    consumer_evidence: Path | None = None,
) -> dict[str, Any]:
    migration = _load_json(migration_readiness_report)
    milestone = _load_json(milestone_packet)
    alias_fallback = migration.get("alias_fallback", {})

    canonical_default_confirmed = bool(alias_fallback.get("default_emits_alias") is False)
    fallback_flag_available = bool(alias_fallback.get("fallback_flag") == "--include-history-update-alias")
    fallback_alias_reported = "fallback_manifest_has_alias" in alias_fallback
    internal_consumers_clear = migration.get("status") == "pass"

    evidence_payload: dict[str, Any] = {}
    evidence_source = "none"
    consumers: list[dict[str, Any]] = []
    evidence_status = "unknown"
    if consumer_evidence and consumer_evidence.exists():
        evidence_payload = _load_json(consumer_evidence)
        evidence_source = str(consumer_evidence)
        consumers = evidence_payload.get("consumers", [])
        if isinstance(evidence_payload.get("external_status"), str):
            evidence_status = evidence_payload["external_status"]

    # Precedence rule: explicit CLI status overrides evidence file status.
    effective_external_status = external_consumer_status or evidence_status

    requires_alias_count = 0
    confirmed_clear_count = 0
    unresolved_count = 0
    for c in consumers:
        if c.get("requires_history_update") is True:
            requires_alias_count += 1
        st = c.get("status")
        if st == "confirmed_clear":
            confirmed_clear_count += 1
        elif st != "requires_alias":
            unresolved_count += 1

    if requires_alias_count > 0:
        effective_external_status = "requires_alias"
    elif consumers and unresolved_count == 0 and effective_external_status == "unknown":
        # If all listed consumers are resolved but no external status set, default to confirmed_clear.
        effective_external_status = "confirmed_clear"

    migration_status = migration.get("status", "warn")
    milestone_status = milestone.get("overall_status", "warn")
    readiness_pass = migration_status == "pass" and milestone_status != "fail"
    if effective_external_status == "confirmed_clear" and readiness_pass and requires_alias_count == 0 and unresolved_count == 0:
        status = "ready"
        recommended_action = "schedule_removal"
    elif effective_external_status == "requires_alias":
        status = "blocked"
        recommended_action = "migrate_consumers"
    else:
        status = "watch"
        recommended_action = "collect_consumer_evidence"

    if migration_status == "fail" or milestone_status == "fail":
        status = "blocked"
        recommended_action = "keep_fallback"

    unresolved_consumers = [
        c
        for c in consumers
        if c.get("status") not in {"confirmed_clear", "requires_alias"}
    ]
    consumers_requiring_alias = [
        c
        for c in consumers
        if c.get("status") == "requires_alias" or c.get("requires_history_update") is True
    ]
    required_evidence_complete = (
        bool(consumers)
        and unresolved_count == 0
        and all(
            bool(c.get("name")) and bool(c.get("owner")) and bool(c.get("evidence"))
            for c in consumers
        )
    )
    ready_conditions = [
        "migration_readiness_status=pass",
        "milestone_packet_status!=fail",
        "external_status=confirmed_clear",
        "unresolved_count=0",
        "requires_alias_count=0",
    ]
    blocking_conditions: list[str] = []
    if migration_status == "fail":
        blocking_conditions.append("migration_readiness_status=fail")
    if milestone_status == "fail":
        blocking_conditions.append("milestone_packet_status=fail")
    if requires_alias_count > 0:
        blocking_conditions.append("consumers_requiring_alias>0")
    if effective_external_status == "requires_alias":
        blocking_conditions.append("external_status=requires_alias")
    next_actions: list[str] = []
    if status == "blocked":
        if requires_alias_count > 0:
            next_actions.append("migrate_consumers")
        next_actions.append("keep_fallback")
    elif status == "watch":
        next_actions.extend(["collect_consumer_evidence", "keep_fallback"])
    else:
        next_actions.append("schedule_removal")

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
        "external_consumer_confirmation": effective_external_status,
        "evidence_source": evidence_source,
        "evidence_consumer_count": len(consumers),
        "requires_alias_count": requires_alias_count,
        "confirmed_clear_count": confirmed_clear_count,
        "unresolved_count": unresolved_count,
        "consumers": consumers,
        "recommended_action": recommended_action,
        "decision_gate": {
            "status": status,
            "required_evidence_complete": required_evidence_complete,
            "unresolved_consumers": unresolved_consumers,
            "consumers_requiring_alias": consumers_requiring_alias,
            "ready_conditions": ready_conditions,
            "blocking_conditions": blocking_conditions,
            "next_actions": next_actions,
        },
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
            f"- Evidence source: `{payload.get('evidence_source', 'none')}`",
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
            f"- requires_alias_count: `{payload.get('requires_alias_count', 0)}`",
            f"- confirmed_clear_count: `{payload.get('confirmed_clear_count', 0)}`",
            f"- unresolved_count: `{payload.get('unresolved_count', 0)}`",
            f"- {payload.get('note', '')}",
            "",
            "## Decision Gate",
            "",
            f"- status: `{(payload.get('decision_gate') or {}).get('status', 'watch')}`",
            f"- required_evidence_complete: `{(payload.get('decision_gate') or {}).get('required_evidence_complete', False)}`",
            f"- next_actions: `{(payload.get('decision_gate') or {}).get('next_actions', [])}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
