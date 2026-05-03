"""Consumer evidence closure report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_consumer_evidence_closure_report(*, consumer_evidence: Path) -> dict[str, Any]:
    payload = _load_json(consumer_evidence)
    consumers = payload.get("consumers", [])

    owners_missing = 0
    requires_action_count = 0
    missing_fields_total = 0
    confirmed_clear_count = 0
    unresolved_count = 0
    requires_alias_count = 0
    items: list[dict[str, Any]] = []

    for c in consumers:
        status = c.get("status", "unknown")
        owner = c.get("owner")
        next_action = c.get("next_action", "identify_owner")
        missing_fields = []
        if not c.get("name"):
            missing_fields.append("name")
        if not owner:
            missing_fields.append("owner")
        if not c.get("evidence"):
            missing_fields.append("evidence")
        if status == "unknown" and not c.get("last_checked"):
            missing_fields.append("last_checked")

        if not owner or owner == "unknown":
            owners_missing += 1
        if status == "confirmed_clear":
            confirmed_clear_count += 1
        elif status == "requires_alias":
            requires_alias_count += 1
            requires_action_count += 1
        else:
            unresolved_count += 1
            requires_action_count += 1

        missing_fields_total += len(missing_fields)
        items.append(
            {
                "name": c.get("name"),
                "owner": owner,
                "status": status,
                "next_action": next_action,
                "due_phase": c.get("due_phase"),
                "missing_fields": missing_fields,
            }
        )

    if requires_alias_count > 0:
        status = "blocked"
    elif unresolved_count > 0 or missing_fields_total > 0:
        status = "incomplete"
    else:
        status = "complete"

    evidence_complete = status == "complete"
    completeness_ratio = 0.0
    if consumers:
        completeness_ratio = confirmed_clear_count / len(consumers)

    next_actions = sorted({item.get("next_action") for item in items if item.get("next_action") and item.get("next_action") != "none"})

    return {
        "schema_version": "v1",
        "status": status,
        "consumer_count": len(consumers),
        "confirmed_clear_count": confirmed_clear_count,
        "unresolved_count": unresolved_count,
        "requires_alias_count": requires_alias_count,
        "owners_missing_count": owners_missing,
        "consumers_requiring_action_count": requires_action_count,
        "missing_fields_total": missing_fields_total,
        "evidence_complete": evidence_complete,
        "evidence_completeness_ratio": completeness_ratio,
        "next_actions": next_actions,
        "consumers": items,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_consumer_evidence_closure_markdown(payload: dict[str, Any]) -> str:
    next_actions = payload.get("next_actions", [])
    return "\n".join(
        [
            "# History Alias Consumer Evidence Closure",
            "",
            f"- Status: `{payload.get('status', 'incomplete')}`",
            f"- consumer_count: `{payload.get('consumer_count', 0)}`",
            f"- confirmed_clear_count: `{payload.get('confirmed_clear_count', 0)}`",
            f"- unresolved_count: `{payload.get('unresolved_count', 0)}`",
            f"- requires_alias_count: `{payload.get('requires_alias_count', 0)}`",
            f"- owners_missing_count: `{payload.get('owners_missing_count', 0)}`",
            f"- evidence_complete: `{payload.get('evidence_complete', False)}`",
            "",
            "## Next Actions",
            "",
            *([f"- {a}" for a in next_actions] if next_actions else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
