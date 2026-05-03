"""Optional follow-up queue report for maintenance mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_optional_followups(
    *,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    maintenance_cadence: Path,
    external_consumer_evidence_closure_report: Path | None = None,
) -> dict[str, Any]:
    readiness = _load_json(release_readiness_report)
    reviewer = _load_json(final_reviewer_packet)
    cadence = _load_json(maintenance_cadence)

    external_closure = (
        _load_json(external_consumer_evidence_closure_report)
        if external_consumer_evidence_closure_report and external_consumer_evidence_closure_report.exists()
        else {}
    )

    items = [
        {
            "id": "external-consumer-evidence-governance",
            "status": "open",
            "blocking_release": False,
            "recommended_timing": "when external owner evidence is available",
            "reason": "Alias sunset governance trail still has unresolved external-owner evidence.",
        },
        {
            "id": "slow-test-optimization",
            "status": "optional",
            "blocking_release": False,
            "recommended_timing": "if runtime variance recurs",
            "reason": "Pytest runtime profile may keep warn-level hotspots without blocking release readiness.",
        },
    ]
    if external_closure.get("status") in {"closed_confirmed", "closed_unresolved_external"} and external_closure.get(
        "blocking"
    ) is not True:
        items[0]["status"] = "closed"
        items[0]["recommended_timing"] = "moved to external-tracking-only cadence"
        items[0]["reason"] = "External consumer governance closure artifact confirms non-blocking maintenance tracking."

    blockers = []
    if readiness.get("status") == "blocked":
        blockers.append("release_readiness_status=blocked")
    if reviewer.get("status") == "blocked":
        blockers.append("final_reviewer_packet_status=blocked")
    if cadence.get("status") == "blocked":
        blockers.append("maintenance_cadence_status=blocked")

    if blockers:
        status = "blocked"
    elif not items:
        status = "empty"
    else:
        status = "open"

    return {
        "schema_version": "v1",
        "status": status,
        "blocking": False,
        "blocking_reasons": blockers,
        "items": items,
        "closed_items": [item for item in items if item.get("status") == "closed"],
        "active_items": [item for item in items if item.get("status") != "closed"],
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_optional_followups_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation Optional Follow-ups",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- blocking: `{payload.get('blocking')}`",
        f"- active_count: `{len(payload.get('active_items', []))}`",
        f"- closed_count: `{len(payload.get('closed_items', []))}`",
        "",
        "## Items",
        "",
    ]
    items = payload.get("items", [])
    if not items:
        lines.append("- none")
    else:
        for item in items:
            lines.extend(
                [
                    f"- id: `{item.get('id')}`",
                    f"  status: `{item.get('status')}`",
                    f"  blocking_release: `{item.get('blocking_release')}`",
                    f"  recommended_timing: `{item.get('recommended_timing')}`",
                ]
            )
    lines.extend(
        [
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
    return "\n".join(lines)
