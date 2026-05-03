"""Runtime variance closure classification report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_runtime_variance_closure(
    *,
    runtime_variance_report: Path,
    runtime_release_cycle_report: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
) -> dict[str, Any]:
    variance = _load_json(runtime_variance_report)
    cycle = _load_json(runtime_release_cycle_report)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)

    variance_status = variance.get("status")
    cycle_status = cycle.get("status")
    budget_status = budget.get("overall_status")
    edge_status = edge.get("status")
    timing_consistency_status = (budget.get("timing_consistency") or {}).get("status")

    blocking = (
        budget_status == "fail"
        or edge_status == "fail"
        or timing_consistency_status == "fail"
        or cycle_status == "fail"
        or variance_status == "fail"
    )

    if blocking:
        status = "blocked"
        reason_code = "runtime_blocked"
        followup = "resolve_runtime_blockers"
        cadence = "immediate"
    elif variance_status in {"watch", "warn"} or cycle_status in {"watch", "warn"}:
        status = "monitoring_only"
        reason_code = "variance_watch_non_blocking"
        followup = "monitor_next_cycle"
        cadence = "next_release_cycle"
    else:
        status = "closed"
        reason_code = "variance_pass"
        followup = "none"
        cadence = "routine"

    return {
        "schema_version": "v1",
        "status": status,
        "runtime_variance_status": variance_status,
        "runtime_release_cycle_status": cycle_status,
        "runtime_budget_status": budget_status,
        "runtime_edge_status": edge_status,
        "timing_consistency_status": timing_consistency_status,
        "blocking": blocking,
        "remaining_followup": followup,
        "recommended_cadence": cadence,
        "reason_code": reason_code,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_runtime_variance_closure_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Runtime Variance Closure",
            "",
            f"- Status: `{payload.get('status')}`",
            f"- reason_code: `{payload.get('reason_code')}`",
            f"- runtime_variance_status: `{payload.get('runtime_variance_status')}`",
            f"- runtime_release_cycle_status: `{payload.get('runtime_release_cycle_status')}`",
            f"- runtime_budget_status: `{payload.get('runtime_budget_status')}`",
            f"- runtime_edge_status: `{payload.get('runtime_edge_status')}`",
            f"- timing_consistency_status: `{payload.get('timing_consistency_status')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- remaining_followup: `{payload.get('remaining_followup')}`",
            f"- recommended_cadence: `{payload.get('recommended_cadence')}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
