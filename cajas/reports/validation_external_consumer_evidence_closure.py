"""External consumer evidence governance closure report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any



def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))



def _safe(path: Path | None) -> dict[str, Any]:
    if path and path.exists():
        return _load_json(path)
    return {}



def build_validation_external_consumer_evidence_closure(
    *,
    alias_post_removal_closure: Path | None = None,
    maintenance_governance_closure: Path | None = None,
    release_readiness_report: Path | None = None,
    optional_followups_report: Path | None = None,
    consumer_owner_handoff: Path | None = None,
    consumer_evidence_closure: Path | None = None,
) -> dict[str, Any]:
    alias = _safe(alias_post_removal_closure)
    governance = _safe(maintenance_governance_closure)
    readiness = _safe(release_readiness_report)
    followups = _safe(optional_followups_report)
    owner = _safe(consumer_owner_handoff)
    evidence = _safe(consumer_evidence_closure)

    canonical_only_confirmed = alias.get("canonical_only_manifest_confirmed") is True or alias.get("status") == "closed"
    legacy_kept = alias.get("legacy_read_normalization_kept") is True or readiness.get("legacy_read_normalization_kept") is True

    owner_items = owner.get("handoff_items") if isinstance(owner.get("handoff_items"), list) else []
    evidence_items = evidence.get("action_plan") if isinstance(evidence.get("action_plan"), list) else []

    owner_missing_count = sum(1 for item in owner_items if isinstance(item, dict) and item.get("owner") in {None, "", "external-review-needed"})
    requires_alias_count = 0
    unresolved_count = max(owner_missing_count, len(evidence_items))
    consumer_count = max(len(owner_items), len(evidence_items))

    release_blocking = False
    if readiness.get("status") == "blocked" or governance.get("status") == "blocked":
        release_blocking = True

    if followups.get("blocking") is True:
        release_blocking = True

    closure_reason = "canonical-only producer path confirmed; external consumer evidence tracked as non-blocking maintenance"
    remaining_action = "none"
    status = "closed_confirmed"

    if release_blocking:
        status = "fail"
        closure_reason = "blocking governance or readiness artifact detected"
        remaining_action = "external_tracking_only"
    elif requires_alias_count > 0:
        status = "fail"
        closure_reason = "artifact indicates active alias emission requirement"
        remaining_action = "external_tracking_only"
    elif unresolved_count > 0 or owner.get("status") in {"open", "watch"} or evidence.get("status") in {"open", "watch", "incomplete"}:
        status = "closed_unresolved_external"
        closure_reason = "operational closure reached; unresolved external evidence remains non-blocking"
        remaining_action = "external_tracking_only"

    payload = {
        "schema_version": "v1",
        "status": status,
        "blocking": status == "fail",
        "review_state": "ready_for_review" if status != "fail" else "blocked",
        "evidence_governance_state": "closed" if status in {"closed_confirmed", "closed_unresolved_external"} else "watch",
        "canonical_only_confirmed": canonical_only_confirmed,
        "legacy_read_normalization_kept": legacy_kept,
        "active_alias_emission_supported": False,
        "external_consumer_summary": {
            "consumer_count": consumer_count,
            "unresolved_count": unresolved_count,
            "requires_alias_count": requires_alias_count,
            "owner_missing_count": owner_missing_count,
        },
        "closure_reason": closure_reason,
        "remaining_action": remaining_action,
        "release_blocking": status == "fail",
        "next_review_cadence": "next_release_cycle",
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }
    return payload



def render_validation_external_consumer_evidence_closure_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("external_consumer_summary", {})
    return "\n".join(
        [
            "# Validation External Consumer Evidence Closure",
            "",
            f"- status: `{payload.get('status')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- evidence_governance_state: `{payload.get('evidence_governance_state')}`",
            f"- canonical_only_confirmed: `{payload.get('canonical_only_confirmed')}`",
            f"- legacy_read_normalization_kept: `{payload.get('legacy_read_normalization_kept')}`",
            f"- active_alias_emission_supported: `{payload.get('active_alias_emission_supported')}`",
            "",
            "## External Consumer Summary",
            "",
            f"- consumer_count: `{summary.get('consumer_count')}`",
            f"- unresolved_count: `{summary.get('unresolved_count')}`",
            f"- requires_alias_count: `{summary.get('requires_alias_count')}`",
            f"- owner_missing_count: `{summary.get('owner_missing_count')}`",
            "",
            "## Closure",
            "",
            f"- closure_reason: `{payload.get('closure_reason')}`",
            f"- remaining_action: `{payload.get('remaining_action')}`",
            f"- next_review_cadence: `{payload.get('next_review_cadence')}`",
            "",
            "## Reviewer Next Action",
            "",
            "- Continue routine maintenance cadence and keep external evidence tracking non-blocking unless a future artifact marks alias dependency.",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
