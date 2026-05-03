"""External consumer evidence governance report for maintenance mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_external_consumer_governance(
    *,
    optional_followups: Path | None = None,
    maintenance_governance_closure: Path | None = None,
    alias_post_removal_closure: Path | None = None,
    consumer_owner_handoff: Path | None = None,
    consumer_evidence_closure: Path | None = None,
) -> dict[str, Any]:
    followups = _load_json(optional_followups) if optional_followups and optional_followups.exists() else {}
    closure = _load_json(maintenance_governance_closure) if maintenance_governance_closure and maintenance_governance_closure.exists() else {}
    alias = _load_json(alias_post_removal_closure) if alias_post_removal_closure and alias_post_removal_closure.exists() else {}
    handoff = _load_json(consumer_owner_handoff) if consumer_owner_handoff and consumer_owner_handoff.exists() else {}
    evidence = _load_json(consumer_evidence_closure) if consumer_evidence_closure and consumer_evidence_closure.exists() else {}

    items = followups.get("items", []) if isinstance(followups.get("items", []), list) else []
    reasons = [item.get("reason", "") for item in items if isinstance(item, dict)]
    has_external_governance = any("external" in r.lower() and "evidence" in r.lower() for r in reasons)

    remaining_items: list[str] = []
    if has_external_governance:
        remaining_items.append("external consumer ownership/evidence governance completion")
    if any("slow-test" in r.lower() or "runtime profile" in r.lower() for r in reasons):
        remaining_items.append("optional slow-test optimization if runtime variance/watch recurs")
    if not remaining_items:
        remaining_items.append("track external consumer governance evidence updates during routine maintenance")

    blocking = bool(followups.get("blocking") or closure.get("status") == "blocked")
    if blocking:
        status = "blocked"
        release_impact = "blocking"
    elif closure.get("status") == "ready":
        status = "routine"
        release_impact = "none"
    else:
        status = "tracked"
        release_impact = "none"

    return {
        "schema_version": "v1",
        "status": status,
        "blocking": blocking,
        "release_readiness_impact": release_impact,
        "alias_producer_behavior": "canonical_only",
        "legacy_read_normalization": "preserved" if alias.get("legacy_read_normalization_kept") is True else "unknown",
        "alias_post_removal_closure_status": alias.get("status"),
        "maintenance_governance_closure_status": closure.get("status"),
        "optional_followups_status": followups.get("status"),
        "optional_followups_count": len(items),
        "remaining_items": remaining_items,
        "consumer_owner_handoff_status": handoff.get("status"),
        "consumer_evidence_closure_status": evidence.get("status"),
        "next_maintenance_action": "track external consumer evidence updates and keep non-blocking classification unless artifacts report blocking",
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_external_consumer_governance_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation External Consumer Governance",
            "",
            f"- status: `{payload.get('status')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- release_readiness_impact: `{payload.get('release_readiness_impact')}`",
            f"- alias_producer_behavior: `{payload.get('alias_producer_behavior')}`",
            f"- legacy_read_normalization: `{payload.get('legacy_read_normalization')}`",
            f"- optional_followups_status: `{payload.get('optional_followups_status')}`",
            f"- optional_followups_count: `{payload.get('optional_followups_count')}`",
            "",
            "## Remaining Items",
            "",
            *[f"- {x}" for x in payload.get("remaining_items", [])],
            "",
            "## Next Maintenance Action",
            "",
            f"- {payload.get('next_maintenance_action', '')}",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
