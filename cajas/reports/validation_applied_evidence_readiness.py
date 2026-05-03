"""Applied evidence readiness comparison report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_applied_evidence_readiness_report(
    *,
    real_release_readiness: Path,
    real_alias_sunset: Path,
    applied_evidence_closure: Path,
    applied_alias_sunset: Path,
    applied_alias_removal_plan: Path,
    applied_canonical_evidence_apply_report: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
) -> dict[str, Any]:
    real_readiness = _load_json(real_release_readiness)
    real_sunset = _load_json(real_alias_sunset)
    closure = _load_json(applied_evidence_closure)
    applied_sunset = _load_json(applied_alias_sunset)
    applied_removal = _load_json(applied_alias_removal_plan)
    apply_report = _load_json(applied_canonical_evidence_apply_report)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)

    applied_ready = (
        closure.get("status") == "complete"
        and applied_sunset.get("status") == "ready"
        and applied_removal.get("status") == "ready_to_schedule"
    )
    runtime_pass = budget.get("overall_status") == "pass" and edge.get("status") == "pass"
    apply_ok = apply_report.get("status") in {"dry_run_ready", "applied"}

    if applied_ready and runtime_pass and apply_ok:
        status = "ready_for_real_apply"
        next_action = "perform_real_apply_in_dedicated_phase_or_schedule_alias_removal_review"
    elif not runtime_pass:
        status = "blocked"
        next_action = "stabilize_runtime_gates"
    else:
        status = "watch"
        next_action = "resolve_applied_projection_gaps"

    return {
        "schema_version": "v1",
        "status": status,
        "real_current_status": {
            "release_readiness": real_readiness.get("status"),
            "alias_sunset": real_sunset.get("status"),
        },
        "applied_projection": {
            "evidence_closure": closure.get("status"),
            "alias_sunset": applied_sunset.get("status"),
            "alias_removal_plan": applied_removal.get("status"),
        },
        "runtime_status": "pass" if runtime_pass else "not_pass",
        "manual_real_apply_required": True,
        "alias_fallback_removal_ready_after_real_apply": bool(applied_ready),
        "do_not_remove_fallback_in_this_phase": True,
        "next_action": next_action,
        "scope_note": "Offline Qlib validation automation only; this phase does not remove fallback.",
    }


def render_applied_evidence_readiness_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Applied Evidence Readiness Report",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- runtime_status: `{payload.get('runtime_status')}`",
            f"- manual_real_apply_required: `{payload.get('manual_real_apply_required', True)}`",
            f"- alias_fallback_removal_ready_after_real_apply: `{payload.get('alias_fallback_removal_ready_after_real_apply', False)}`",
            f"- do_not_remove_fallback_in_this_phase: `{payload.get('do_not_remove_fallback_in_this_phase', True)}`",
            f"- next_action: `{payload.get('next_action')}`",
            "",
            "## Real Current Status",
            "",
            f"- release_readiness: `{(payload.get('real_current_status') or {}).get('release_readiness')}`",
            f"- alias_sunset: `{(payload.get('real_current_status') or {}).get('alias_sunset')}`",
            "",
            "## Applied Projection",
            "",
            f"- evidence_closure: `{(payload.get('applied_projection') or {}).get('evidence_closure')}`",
            f"- alias_sunset: `{(payload.get('applied_projection') or {}).get('alias_sunset')}`",
            f"- alias_removal_plan: `{(payload.get('applied_projection') or {}).get('alias_removal_plan')}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
