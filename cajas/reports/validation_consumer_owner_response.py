"""Validate owner responses before applying alias evidence updates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_response(response: dict[str, Any], known_consumers: set[str]) -> tuple[str, list[str], bool]:
    issues: list[str] = []
    consumer = response.get("consumer")
    status = response.get("status")
    owner = response.get("owner")
    evidence = response.get("evidence")
    last_checked = response.get("last_checked")
    requires_history_update = response.get("requires_history_update")

    if consumer not in known_consumers:
        issues.append("unknown_consumer")
    if not owner:
        issues.append("missing_owner")
    if status not in {"confirmed_clear", "requires_alias", "unknown"}:
        issues.append("invalid_status")
    if status == "confirmed_clear":
        if not evidence:
            issues.append("missing_evidence_for_confirmed_clear")
        if not last_checked:
            issues.append("missing_last_checked_for_confirmed_clear")
        if requires_history_update is not False:
            issues.append("requires_history_update_must_be_false_for_confirmed_clear")
    elif status == "requires_alias":
        if not evidence:
            issues.append("missing_evidence_for_requires_alias")
        if requires_history_update is not True:
            issues.append("requires_history_update_must_be_true_for_requires_alias")
    else:  # unknown
        if not response.get("next_action"):
            issues.append("missing_next_action_for_unknown")

    if issues:
        return "invalid", issues, False
    if status == "confirmed_clear":
        return "valid_ready_to_apply", [], True
    if status == "requires_alias":
        return "valid_requires_alias", [], False
    return "incomplete", [], False


def _build_updated_evidence_candidate(evidence: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(evidence))
    consumer = response.get("consumer")
    for item in updated.get("consumers", []):
        if item.get("name") != consumer:
            continue
        item["owner"] = response.get("owner")
        item["status"] = response.get("status")
        item["requires_history_update"] = response.get("requires_history_update")
        item["evidence"] = response.get("evidence")
        item["last_checked"] = response.get("last_checked")
        item["next_action"] = response.get("next_action", "none")
        item["blocking_alias_sunset"] = response.get("status") != "confirmed_clear"
    meta = updated.setdefault("candidate_metadata", {})
    meta["manual_approval_required"] = True
    meta["do_not_auto_apply"] = True
    return updated


def validate_consumer_owner_response(
    *,
    consumer_evidence: Path,
    owner_response: Path,
    consumer_owner_handoff: Path | None = None,
    apply_to_out: Path | None = None,
) -> dict[str, Any]:
    evidence = _load_json(consumer_evidence)
    response = _load_json(owner_response)
    handoff = _load_json(consumer_owner_handoff) if consumer_owner_handoff and consumer_owner_handoff.exists() else {}

    known_consumers = {c.get("name") for c in evidence.get("consumers", []) if c.get("name")}
    status, issues, safe_to_apply = _validate_response(response, known_consumers)

    out_path = None
    candidate_written = False
    manual_approval_required = True
    if apply_to_out and safe_to_apply:
        updated = _build_updated_evidence_candidate(evidence, response)
        updated["candidate_metadata"]["source_owner_response_file"] = str(owner_response)
        updated["candidate_metadata"]["generated_by"] = "validate_consumer_owner_response"
        updated["candidate_metadata"]["generated_at"] = response.get("response_date")
        updated["candidate_metadata"]["candidate_output_path"] = str(apply_to_out)
        updated["candidate_metadata"]["canonical_evidence_path"] = str(consumer_evidence)
        updated["candidate_metadata"]["is_canonical_path"] = str(apply_to_out) == str(consumer_evidence)
        apply_to_out.parent.mkdir(parents=True, exist_ok=True)
        apply_to_out.write_text(json.dumps(updated, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        out_path = str(apply_to_out)
        candidate_written = True

    return {
        "schema_version": "v1",
        "status": status,
        "safe_to_update_evidence": safe_to_apply,
        "candidate_written": candidate_written,
        "candidate_output_path": out_path,
        "manual_approval_required": manual_approval_required,
        "do_not_auto_apply": True,
        "issues": issues,
        "consumer": response.get("consumer"),
        "owner": response.get("owner"),
        "owner_response_status": response.get("status"),
        "requires_history_update": response.get("requires_history_update"),
        "consumer_owner_handoff_status": handoff.get("status"),
        "consumer_owner_handoff_blocking_count": handoff.get("blocking_consumer_count"),
        "updated_evidence_candidate_path": out_path,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_consumer_owner_response_validation_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Consumer Owner Response Validation",
            "",
            f"- Status: `{payload.get('status', 'invalid')}`",
            f"- safe_to_update_evidence: `{payload.get('safe_to_update_evidence', False)}`",
            f"- candidate_written: `{payload.get('candidate_written', False)}`",
            f"- candidate_output_path: `{payload.get('candidate_output_path')}`",
            f"- manual_approval_required: `{payload.get('manual_approval_required', True)}`",
            f"- do_not_auto_apply: `{payload.get('do_not_auto_apply', True)}`",
            f"- consumer: `{payload.get('consumer')}`",
            f"- owner: `{payload.get('owner')}`",
            f"- owner_response_status: `{payload.get('owner_response_status')}`",
            f"- requires_history_update: `{payload.get('requires_history_update')}`",
            f"- consumer_owner_handoff_status: `{payload.get('consumer_owner_handoff_status')}`",
            f"- consumer_owner_handoff_blocking_count: `{payload.get('consumer_owner_handoff_blocking_count')}`",
            f"- updated_evidence_candidate_path: `{payload.get('updated_evidence_candidate_path')}`",
            "",
            "## Issues",
            "",
            *([f"- {x}" for x in payload.get("issues", [])] if payload.get("issues") else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
