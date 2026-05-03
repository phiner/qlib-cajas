"""Evidence candidate approval gate report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_evidence_candidate_approval_report(
    *,
    real_evidence: Path,
    candidate_evidence: Path,
    owner_response_validation: Path,
    consumer_evidence_candidate_report: Path,
    alias_sunset_review: Path,
    alias_removal_plan: Path,
    approval_file: Path | None = None,
) -> dict[str, Any]:
    real = _load_json(real_evidence)
    candidate = _load_json(candidate_evidence)
    owner_validation = _load_json(owner_response_validation)
    candidate_report = _load_json(consumer_evidence_candidate_report)
    sunset = _load_json(alias_sunset_review)
    removal = _load_json(alias_removal_plan)
    approval = _load_json(approval_file) if approval_file and approval_file.exists() else {}

    approval_checklist = [
        "Confirm owner identity",
        "Confirm evidence text/link",
        "Confirm consumer reads manifest.history",
        "Confirm requires_history_update=false",
        "Confirm last_checked date",
    ]

    candidate_valid = owner_validation.get("status") == "valid_ready_to_apply"
    candidate_safe = bool(owner_validation.get("safe_to_update_evidence", False))
    real_unchanged = real != candidate
    approval_flag = bool(approval.get("approved", False)) if approval else False

    if not candidate_valid or not candidate_safe:
        status = "invalid"
        next_action = "fix_candidate_validation_inputs"
    elif approval and approval.get("approved") is True:
        status = "approved_candidate"
        next_action = "apply_in_dedicated_phase"
    elif approval and approval.get("approved") is False:
        status = "approval_required"
        next_action = "manual_review_candidate"
    elif approval and "approved" not in approval:
        status = "invalid"
        next_action = "fix_approval_file_schema"
    else:
        status = "approval_required"
        next_action = "manual_review_candidate"

    if candidate_report.get("status") not in {"ready_candidate", "blocked", "invalid"}:
        status = "invalid"
        next_action = "fix_candidate_report_inputs"

    return {
        "schema_version": "v1",
        "status": status,
        "candidate_valid": candidate_valid,
        "candidate_safe_to_apply": candidate_safe,
        "manual_approval_required": True,
        "real_evidence_unchanged": real_unchanged,
        "approval_file_present": bool(approval),
        "approval_flag": approval_flag if approval else None,
        "approval_checklist": approval_checklist,
        "post_approval_projection": {
            "evidence_closure_status": "complete" if candidate_report.get("status") == "ready_candidate" else "incomplete",
            "alias_sunset_status": sunset.get("status"),
            "alias_removal_plan_status": removal.get("status"),
        },
        "next_action": next_action,
        "do_not_auto_apply": True,
        "scope_note": "Offline Qlib validation automation only; this phase does not remove fallback.",
    }


def render_evidence_candidate_approval_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Evidence Candidate Approval Gate",
            "",
            f"- Status: `{payload.get('status', 'invalid')}`",
            f"- candidate_valid: `{payload.get('candidate_valid', False)}`",
            f"- candidate_safe_to_apply: `{payload.get('candidate_safe_to_apply', False)}`",
            f"- manual_approval_required: `{payload.get('manual_approval_required', True)}`",
            f"- real_evidence_unchanged: `{payload.get('real_evidence_unchanged', True)}`",
            f"- approval_file_present: `{payload.get('approval_file_present', False)}`",
            f"- approval_flag: `{payload.get('approval_flag')}`",
            f"- next_action: `{payload.get('next_action')}`",
            "",
            "## Approval Checklist",
            "",
            *[f"- {item}" for item in payload.get("approval_checklist", [])],
            "",
            "## Post-Approval Projection",
            "",
            f"- evidence_closure_status: `{(payload.get('post_approval_projection') or {}).get('evidence_closure_status')}`",
            f"- alias_sunset_status: `{(payload.get('post_approval_projection') or {}).get('alias_sunset_status')}`",
            f"- alias_removal_plan_status: `{(payload.get('post_approval_projection') or {}).get('alias_removal_plan_status')}`",
            "",
            "## Non-Goal",
            "",
            "- Do not remove fallback in this phase.",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
