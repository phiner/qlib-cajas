"""Consumer owner handoff packet for unresolved alias evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_consumer_owner_handoff(
    *,
    consumer_evidence: Path,
    consumer_evidence_closure_report: Path | None = None,
    alias_sunset_review: Path | None = None,
) -> dict[str, Any]:
    evidence = _load_json(consumer_evidence)
    closure = (
        _load_json(consumer_evidence_closure_report)
        if consumer_evidence_closure_report and consumer_evidence_closure_report.exists()
        else {}
    )
    sunset = _load_json(alias_sunset_review) if alias_sunset_review and alias_sunset_review.exists() else {}

    consumers = evidence.get("consumers", [])
    handoff_items: list[dict[str, Any]] = []
    blocking_consumer_count = 0

    for c in consumers:
        status = c.get("status", "unknown")
        requires_alias = status == "requires_alias" or c.get("requires_history_update") is True
        unresolved = status != "confirmed_clear"
        blocks_alias_sunset = bool(c.get("blocking_alias_sunset", unresolved))
        if blocks_alias_sunset:
            blocking_consumer_count += 1
        if not unresolved:
            continue
        handoff_items.append(
            {
                "consumer": c.get("name"),
                "owner": c.get("owner", "external-review-needed"),
                "next_action": c.get("next_action", "identify_owner"),
                "required_evidence": [
                    "owner/team",
                    "whether consumer reads manifest.history",
                    "whether history_update is still required",
                    "last_checked date",
                    "evidence note/link",
                ],
                "blocks_alias_sunset": blocks_alias_sunset,
                "status": status,
                "requires_alias": requires_alias,
            }
        )

    if any(item.get("requires_alias") for item in handoff_items):
        status = "blocked"
    elif handoff_items:
        status = "open"
    else:
        status = "ready"

    recommended_message = (
        "Please identify the owner for each unresolved external consumer and confirm whether it reads "
        "`manifest.history` or still depends on `history_update`. Keep alias fallback until confirmed clear evidence is recorded."
    )

    return {
        "schema_version": "v1",
        "status": status,
        "blocking_consumer_count": blocking_consumer_count,
        "consumer_evidence_closure_status": closure.get("status"),
        "alias_sunset_review_status": sunset.get("status"),
        "handoff_items": handoff_items,
        "recommended_message": recommended_message,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_consumer_owner_handoff_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# History Alias Consumer Owner Handoff",
        "",
        f"- Status: `{payload.get('status', 'open')}`",
        f"- blocking_consumer_count: `{payload.get('blocking_consumer_count', 0)}`",
        f"- consumer_evidence_closure_status: `{payload.get('consumer_evidence_closure_status', 'unknown')}`",
        f"- alias_sunset_review_status: `{payload.get('alias_sunset_review_status', 'unknown')}`",
        "",
        "## Handoff Items",
        "",
        "| Consumer | Owner | Status | Next action | Blocks alias sunset |",
        "|---|---|---|---|---|",
    ]
    items = payload.get("handoff_items", [])
    if items:
        lines.extend(
            [
                f"| {x.get('consumer')} | {x.get('owner')} | {x.get('status')} | "
                f"{x.get('next_action')} | {x.get('blocks_alias_sunset')} |"
                for x in items
            ]
        )
    else:
        lines.append("| none | n/a | n/a | n/a | n/a |")
    lines.extend(
        [
            "",
            "## Copyable Owner Message",
            "",
            payload.get("recommended_message", ""),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
    return "\n".join(lines)
