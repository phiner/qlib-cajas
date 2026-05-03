"""Canonical evidence update plan report built from approval simulation signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _consumer_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("name"): item for item in payload.get("consumers", []) if item.get("name")}


def _build_diff_summary(real: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    real_map = _consumer_map(real)
    candidate_map = _consumer_map(candidate)
    changed_consumers: list[str] = []
    status_changes: list[dict[str, str]] = []

    for name, cand in candidate_map.items():
        old = real_map.get(name, {})
        if old.get("status") != cand.get("status"):
            changed_consumers.append(name)
            status_changes.append(
                {
                    "consumer": name,
                    "from": str(old.get("status")),
                    "to": str(cand.get("status")),
                }
            )

    return {
        "changed_consumers": changed_consumers,
        "status_changes": status_changes,
    }


def build_canonical_evidence_update_plan(
    *,
    real_evidence: Path,
    candidate_evidence: Path,
    evidence_candidate_approval_report: Path,
    owner_response_validation: Path,
    consumer_evidence_candidate_report: Path,
    alias_sunset_schedule: Path,
) -> dict[str, Any]:
    real = _load_json(real_evidence)
    candidate = _load_json(candidate_evidence)
    approval = _load_json(evidence_candidate_approval_report)
    owner_validation = _load_json(owner_response_validation)
    candidate_report = _load_json(consumer_evidence_candidate_report)
    schedule = _load_json(alias_sunset_schedule)

    approval_status = approval.get("status")
    candidate_valid = owner_validation.get("status") == "valid_ready_to_apply"
    schedule_status = schedule.get("status")

    if not candidate_valid or candidate_report.get("status") == "invalid":
        status = "blocked"
        recommendation = "fix_candidate_validation_before_update"
    elif approval_status != "approved_candidate":
        status = "not_ready"
        recommendation = "wait_for_approval"
    elif schedule_status == "ready_to_schedule":
        status = "ready_to_apply"
        recommendation = "apply_in_dedicated_phase"
    else:
        status = "blocked"
        recommendation = "resolve_schedule_blockers"

    required_steps = [
        "Review approval file and candidate evidence diff.",
        "If approved, copy candidate evidence into canonical evidence file in a dedicated phase.",
        "Regenerate evidence closure, alias sunset review, removal plan, release readiness, and milestone packet.",
        "Only after regenerated real evidence reports are ready should alias fallback removal be scheduled.",
    ]
    post_update_validation_commands = [
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_consumer_evidence_closure_report.py --consumer-evidence cajas/data_examples/history_alias_external_consumers.json --out-json tmp/history-alias-consumer-evidence-closure.json --out-md tmp/history-alias-consumer-evidence-closure.md",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_alias_sunset_review.py --migration-readiness-report tmp/history-alias-migration-readiness.json --milestone-packet tmp/validation-milestone-packet.json --consumer-evidence cajas/data_examples/history_alias_external_consumers.json --out-json tmp/history-alias-sunset-review.json --out-md tmp/history-alias-sunset-review.md",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_alias_removal_plan.py --alias-sunset-review tmp/history-alias-sunset-review.json --migration-readiness-report tmp/history-alias-migration-readiness.json --release-readiness-report tmp/validation-release-readiness.json --out-json tmp/history-alias-removal-plan.json --out-md tmp/history-alias-removal-plan.md",
    ]

    return {
        "schema_version": "v1",
        "status": status,
        "real_evidence_file": str(real_evidence),
        "candidate_evidence_file": str(candidate_evidence),
        "approval_status": approval_status,
        "candidate_valid": candidate_valid,
        "manual_update_required": True,
        "do_not_auto_apply": True,
        "required_steps": required_steps,
        "post_update_validation_commands": post_update_validation_commands,
        "recommendation": recommendation,
        "evidence_diff_summary": _build_diff_summary(real, candidate),
        "scope_note": "Offline Qlib validation automation only; this phase does not update canonical evidence automatically.",
    }


def render_canonical_evidence_update_plan_markdown(payload: dict[str, Any]) -> str:
    diff = payload.get("evidence_diff_summary") or {}
    return "\n".join(
        [
            "# Canonical Evidence Update Plan",
            "",
            f"- Status: `{payload.get('status', 'not_ready')}`",
            f"- approval_status: `{payload.get('approval_status')}`",
            f"- candidate_valid: `{payload.get('candidate_valid', False)}`",
            f"- manual_update_required: `{payload.get('manual_update_required', True)}`",
            f"- do_not_auto_apply: `{payload.get('do_not_auto_apply', True)}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "",
            "## Evidence Diff Summary",
            "",
            f"- changed_consumers: `{diff.get('changed_consumers', [])}`",
            f"- status_changes: `{diff.get('status_changes', [])}`",
            "",
            "## Required Steps",
            "",
            *[f"- {item}" for item in payload.get("required_steps", [])],
            "",
            "## Post-Update Validation Commands",
            "",
            *[f"- `{item}`" for item in payload.get("post_update_validation_commands", [])],
            "",
            "## Non-Goal",
            "",
            "- This phase does not auto-apply candidate evidence or remove fallback.",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
