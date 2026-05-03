"""Runtime edge risk report for validation fast tier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_budget_seconds(runtime_budget_report: dict[str, Any], component: str) -> float | None:
    for item in runtime_budget_report.get("results", []):
        if item.get("component") == component:
            value = item.get("budget_seconds")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _get_observed_seconds(timing_json: dict[str, Any], component: str) -> float | None:
    if component == "fast_total":
        value = timing_json.get("total_seconds")
        return float(value) if isinstance(value, (int, float)) else None
    for item in timing_json.get("results", []):
        if item.get("name") == component and isinstance(item.get("seconds"), (int, float)):
            return float(item["seconds"])
    return None


def build_validation_runtime_edge_report(
    *,
    timing_json_path: Path,
    runtime_budget_report_path: Path,
    watch_threshold_ratio: float = 0.15,
) -> dict[str, Any]:
    timing = _load_json(timing_json_path)
    runtime_budget = _load_json(runtime_budget_report_path)

    fast_total = _get_observed_seconds(timing, "fast_total")
    fast_total_budget = _get_budget_seconds(runtime_budget, "fast_total")
    pytest_fast = _get_observed_seconds(timing, "pytest_fast")
    pytest_fast_budget = _get_budget_seconds(runtime_budget, "pytest_fast")

    remaining_budget_seconds = None
    remaining_budget_ratio = None
    if fast_total is not None and fast_total_budget is not None and fast_total_budget > 0:
        remaining_budget_seconds = fast_total_budget - fast_total
        remaining_budget_ratio = remaining_budget_seconds / fast_total_budget

    runtime_overall = runtime_budget.get("overall_status", "warn")
    if runtime_overall == "fail":
        status = "fail"
        recommendation = "optimize_tests"
    elif runtime_overall == "warn":
        status = "warn"
        recommendation = "watch_runtime_variance"
    elif remaining_budget_ratio is not None and remaining_budget_ratio < watch_threshold_ratio:
        status = "watch"
        recommendation = "watch_runtime_variance"
    else:
        status = "pass"
        recommendation = "ok"

    return {
        "schema_version": "v1",
        "status": status,
        "fast_total_seconds": fast_total,
        "fast_total_budget_seconds": fast_total_budget,
        "remaining_budget_seconds": remaining_budget_seconds,
        "remaining_budget_ratio": remaining_budget_ratio,
        "pytest_fast_seconds": pytest_fast,
        "pytest_fast_budget_seconds": pytest_fast_budget,
        "watch_threshold_ratio": watch_threshold_ratio,
        "runtime_budget_overall_status": runtime_overall,
        "timing_consistency_status": (runtime_budget.get("timing_consistency") or {}).get("status"),
        "recommendation": recommendation,
    }


def render_validation_runtime_edge_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Runtime Edge Report",
            "",
            f"- Status: `{payload.get('status', 'warn')}`",
            f"- Recommendation: `{payload.get('recommendation', 'watch_runtime_variance')}`",
            f"- fast_total_seconds: `{payload.get('fast_total_seconds')}`",
            f"- fast_total_budget_seconds: `{payload.get('fast_total_budget_seconds')}`",
            f"- remaining_budget_seconds: `{payload.get('remaining_budget_seconds')}`",
            f"- remaining_budget_ratio: `{payload.get('remaining_budget_ratio')}`",
            f"- pytest_fast_seconds: `{payload.get('pytest_fast_seconds')}`",
            f"- pytest_fast_budget_seconds: `{payload.get('pytest_fast_budget_seconds')}`",
            f"- runtime_budget_overall_status: `{payload.get('runtime_budget_overall_status')}`",
            f"- timing_consistency_status: `{payload.get('timing_consistency_status')}`",
            "",
            "> Reviewer note: this report is an edge-risk view; runtime budget report remains the source of budget pass/fail truth.",
            "",
        ]
    )
