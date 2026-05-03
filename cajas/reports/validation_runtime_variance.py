"""Runtime variance triage report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_runtime_variance_report(
    *,
    fast_timing_json: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    baselines: list[dict[str, Any]],
    watch_delta_ratio: float = 0.10,
) -> dict[str, Any]:
    timing = _load_json(fast_timing_json)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)

    current = timing.get("total_seconds")
    deltas: list[dict[str, Any]] = []
    largest_delta_seconds = 0.0
    largest_delta_ratio = 0.0
    if isinstance(current, (int, float)):
        for b in baselines:
            base = b.get("fast_total_seconds")
            if not isinstance(base, (int, float)) or base <= 0:
                continue
            delta = float(current) - float(base)
            ratio = delta / float(base)
            deltas.append(
                {
                    "label": b.get("label", "baseline"),
                    "baseline_fast_total_seconds": base,
                    "delta_seconds": delta,
                    "delta_ratio": ratio,
                }
            )
            if abs(delta) > abs(largest_delta_seconds):
                largest_delta_seconds = delta
            if abs(ratio) > abs(largest_delta_ratio):
                largest_delta_ratio = ratio

    budget_status = budget.get("overall_status", "warn")
    timing_consistency = (budget.get("timing_consistency") or {}).get("status", "warn")
    if budget_status == "fail" or timing_consistency == "fail":
        status = "fail"
        rec = "optimize_before_release"
    elif budget_status == "warn" or timing_consistency == "warn":
        status = "warn"
        rec = "profile_slow_tests"
    elif largest_delta_ratio >= watch_delta_ratio:
        status = "watch"
        rec = "watch_next_cycle"
    else:
        status = "pass"
        rec = "ok"

    return {
        "schema_version": "v1",
        "status": status,
        "current_fast_total_seconds": current,
        "baselines": baselines,
        "deltas": deltas,
        "largest_delta_seconds": largest_delta_seconds,
        "largest_delta_ratio": largest_delta_ratio,
        "runtime_budget_status": budget_status,
        "timing_consistency_status": timing_consistency,
        "runtime_edge_status": edge.get("status"),
        "recommendation": rec,
        "watch_delta_ratio_threshold": watch_delta_ratio,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_runtime_variance_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation Runtime Variance Triage",
        "",
        f"- Status: `{payload.get('status', 'watch')}`",
        f"- Current fast total seconds: `{payload.get('current_fast_total_seconds')}`",
        f"- Largest delta seconds: `{payload.get('largest_delta_seconds')}`",
        f"- Largest delta ratio: `{payload.get('largest_delta_ratio')}`",
        f"- Runtime budget status: `{payload.get('runtime_budget_status')}`",
        f"- Timing consistency status: `{payload.get('timing_consistency_status')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        "",
        "## Deltas",
        "",
        "| Baseline | Baseline Fast Total | Delta Seconds | Delta Ratio |",
        "|---|---:|---:|---:|",
    ]
    for d in payload.get("deltas", []):
        lines.append(
            f"| {d.get('label')} | {d.get('baseline_fast_total_seconds')} | {d.get('delta_seconds')} | {d.get('delta_ratio')} |"
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
