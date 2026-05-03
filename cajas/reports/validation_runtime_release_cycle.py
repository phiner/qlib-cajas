"""Release-cycle runtime monitor report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_runtime_release_cycle_report(
    *,
    runtime_edge_report: Path,
    runtime_budget_report: Path,
    fast_timing_json: Path,
    runtime_variance_report: Path | None = None,
) -> dict[str, Any]:
    edge = _load_json(runtime_edge_report)
    budget = _load_json(runtime_budget_report)
    timing = _load_json(fast_timing_json)

    edge_status = edge.get("status", "watch")
    budget_status = budget.get("overall_status", "warn")
    variance = _load_json(runtime_variance_report) if runtime_variance_report and runtime_variance_report.exists() else None
    variance_status = (variance or {}).get("status")

    if budget_status == "fail":
        status = "fail"
        rec = "optimize_before_release"
        trigger = "runtime_budget_fail"
    elif budget_status == "warn" or edge_status == "warn":
        status = "warn"
        rec = "optimize_before_release"
        trigger = "runtime_budget_warn"
    elif edge_status == "watch":
        status = "watch"
        rec = "watch_next_cycle"
        trigger = "remaining_budget_ratio_below_0.15"
    else:
        status = "pass"
        rec = "ok"
        trigger = "manual_next_release"

    if variance_status == "watch" and status == "pass":
        status = "watch"
        rec = "watch_next_cycle"
        trigger = "runtime_variance_watch"
    elif variance_status in {"warn", "fail"}:
        status = variance_status
        rec = "optimize_before_release"
        trigger = "runtime_variance_warn_or_fail"

    return {
        "schema_version": "v1",
        "status": status,
        "current_runtime_edge_status": edge_status,
        "current_fast_total_seconds": timing.get("total_seconds"),
        "remaining_budget_seconds": edge.get("remaining_budget_seconds"),
        "remaining_budget_ratio": edge.get("remaining_budget_ratio"),
        "runtime_budget_status": budget_status,
        "runtime_variance_status": variance_status,
        "release_cycle_recommendation": rec,
        "next_review_trigger": trigger,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_runtime_release_cycle_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Runtime Release-Cycle Monitor",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- Current runtime edge: `{payload.get('current_runtime_edge_status')}`",
            f"- Current fast total seconds: `{payload.get('current_fast_total_seconds')}`",
            f"- Remaining budget seconds: `{payload.get('remaining_budget_seconds')}`",
            f"- Remaining budget ratio: `{payload.get('remaining_budget_ratio')}`",
            f"- Runtime budget status: `{payload.get('runtime_budget_status')}`",
            f"- Recommendation: `{payload.get('release_cycle_recommendation')}`",
            f"- Next review trigger: `{payload.get('next_review_trigger')}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
