"""Candidate evidence simulation report for confirmed-clear owner response."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_consumer_evidence_candidate_report(
    *,
    candidate_evidence: Path,
    consumer_evidence_closure_report: Path,
    alias_sunset_review: Path,
    alias_removal_plan: Path,
) -> dict[str, Any]:
    candidate = _load_json(candidate_evidence)
    closure = _load_json(consumer_evidence_closure_report)
    sunset = _load_json(alias_sunset_review)
    removal = _load_json(alias_removal_plan)

    closure_status = closure.get("status")
    sunset_status = sunset.get("status")
    removal_status = removal.get("status")

    if closure_status == "complete" and sunset_status in {"ready", "pass"}:
        status = "ready_candidate"
    elif closure_status in {"incomplete", "blocked"} or sunset_status in {"watch", "blocked"}:
        status = "blocked"
    else:
        status = "invalid"

    if status == "ready_candidate":
        projected_release = "ready"
        next_action = "review_candidate_evidence"
    else:
        projected_release = "watch"
        next_action = "collect_missing_consumer_evidence"

    return {
        "schema_version": "v1",
        "status": status,
        "candidate_evidence_file": str(candidate_evidence),
        "evidence_closure_status": closure_status,
        "alias_sunset_projected_status": sunset_status,
        "alias_removal_projected_status": removal_status,
        "release_readiness_projected_status": projected_release,
        "manual_approval_required": True,
        "do_not_auto_apply": True,
        "next_action": next_action,
        "consumer_count": len(candidate.get("consumers", [])),
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_consumer_evidence_candidate_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Consumer Evidence Candidate Simulation",
            "",
            f"- Status: `{payload.get('status', 'invalid')}`",
            f"- candidate_evidence_file: `{payload.get('candidate_evidence_file')}`",
            f"- evidence_closure_status: `{payload.get('evidence_closure_status')}`",
            f"- alias_sunset_projected_status: `{payload.get('alias_sunset_projected_status')}`",
            f"- alias_removal_projected_status: `{payload.get('alias_removal_projected_status')}`",
            f"- release_readiness_projected_status: `{payload.get('release_readiness_projected_status')}`",
            f"- manual_approval_required: `{payload.get('manual_approval_required', True)}`",
            f"- do_not_auto_apply: `{payload.get('do_not_auto_apply', True)}`",
            f"- next_action: `{payload.get('next_action')}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
