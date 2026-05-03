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
    action_plan: list[dict[str, Any]] = []
    owner_missing_count = 0
    blocking_consumer_count = 0

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

        if not owner or owner in {"unknown", "unassigned", "external-review-needed"}:
            owners_missing += 1
            owner_missing_count += 1
        if status == "confirmed_clear":
            confirmed_clear_count += 1
        elif status == "requires_alias":
            requires_alias_count += 1
            requires_action_count += 1
        else:
            unresolved_count += 1
            requires_action_count += 1

        missing_fields_total += len(missing_fields)
        blocking_alias_sunset = bool(c.get("blocking_alias_sunset", status != "confirmed_clear"))
        if blocking_alias_sunset:
            blocking_consumer_count += 1
        items.append(
            {
                "name": c.get("name"),
                "owner": owner,
                "status": status,
                "next_action": next_action,
                "due_phase": c.get("due_phase"),
                "blocking_alias_sunset": blocking_alias_sunset,
                "missing_fields": missing_fields,
            }
        )
        if next_action and next_action != "none":
            action_plan.append(
                {
                    "consumer": c.get("name"),
                    "owner": owner,
                    "next_action": next_action,
                    "due_phase": c.get("due_phase"),
                    "blocking_alias_sunset": blocking_alias_sunset,
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
        "owner_missing_count": owner_missing_count,
        "blocking_consumer_count": blocking_consumer_count,
        "consumers_requiring_action_count": requires_action_count,
        "missing_fields_total": missing_fields_total,
        "evidence_complete": evidence_complete,
        "evidence_completeness_ratio": completeness_ratio,
        "next_actions": next_actions,
        "action_plan": action_plan,
        "closure_checklist": [
            "Identify owner for unresolved external consumer",
            "Confirm whether consumer reads manifest.history",
            "If consumer requires alias, keep fallback and create migration item",
            "If confirmed clear, update evidence file with owner, last_checked, evidence, and status",
        ],
        "consumers": items,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_consumer_evidence_closure_markdown(payload: dict[str, Any]) -> str:
    next_actions = payload.get("next_actions", [])
    action_plan = payload.get("action_plan", [])
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
            f"- blocking_consumer_count: `{payload.get('blocking_consumer_count', 0)}`",
            f"- evidence_complete: `{payload.get('evidence_complete', False)}`",
            "",
            "## Action Plan",
            "",
            "| Consumer | Owner | Status | Next action | Blocking |",
            "|---|---|---|---|---|",
            *[
                f"| {item.get('consumer')} | {item.get('owner')} | "
                f"{next((c.get('status') for c in payload.get('consumers', []) if c.get('name') == item.get('consumer')), 'unknown')} | "
                f"{item.get('next_action')} | {item.get('blocking_alias_sunset')} |"
                for item in action_plan
            ],
            "",
            "## Next Actions",
            "",
            *([f"- {a}" for a in next_actions] if next_actions else ["- none"]),
            "",
            "## Closure Checklist",
            "",
            *[f"- {item}" for item in payload.get("closure_checklist", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
