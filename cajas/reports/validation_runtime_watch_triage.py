"""Runtime watch triage report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_runtime_watch_triage_report(
    *,
    fast_timing_json: Path,
    runtime_edge_report: Path,
    runtime_variance_report: Path,
    pytest_runtime_profile: Path | None,
    baselines: list[dict[str, Any]],
) -> dict[str, Any]:
    timing = _load_json(fast_timing_json)
    edge = _load_json(runtime_edge_report)
    variance = _load_json(runtime_variance_report)
    profile = _load_json(pytest_runtime_profile) if pytest_runtime_profile and pytest_runtime_profile.exists() else {}

    current = timing.get("total_seconds")
    results = timing.get("results", [])
    largest_step = None
    largest_step_seconds = -1.0
    for row in results:
        sec = row.get("seconds")
        if isinstance(sec, (int, float)) and sec > largest_step_seconds:
            largest_step_seconds = float(sec)
            largest_step = row.get("name")

    baseline_comparisons = []
    if isinstance(current, (int, float)):
        for b in baselines:
            base = b.get("fast_total_seconds")
            if not isinstance(base, (int, float)) or base <= 0:
                continue
            delta = float(current) - float(base)
            ratio = delta / float(base)
            baseline_comparisons.append(
                {
                    "label": b.get("label", "baseline"),
                    "baseline_fast_total_seconds": base,
                    "delta_seconds": delta,
                    "delta_ratio": ratio,
                }
            )

    edge_status = edge.get("status", "watch")
    variance_status = variance.get("status", "watch")
    remaining_budget = edge.get("remaining_budget_seconds")
    remaining_ratio = edge.get("remaining_budget_ratio")
    test_summary = timing.get("test_summary") or {}
    tests_passed = test_summary.get("passed")
    tests_deselected = test_summary.get("deselected")
    test_count = tests_passed
    seconds_per_test = None
    if isinstance(test_count, int) and test_count > 0 and isinstance(current, (int, float)):
        seconds_per_test = float(current) / float(test_count)

    profile_slowest_tests = profile.get("slowest_tests") if isinstance(profile.get("slowest_tests"), list) else []
    profile_slowest_files = profile.get("slowest_files") if isinstance(profile.get("slowest_files"), list) else []
    profile_recommendation = profile.get("recommendation")

    if edge_status in {"warn", "fail"}:
        status = edge_status
        if profile_slowest_tests:
            likely_cause = "slow_tests"
            recommendation = "optimize_slow_tests"
        else:
            likely_cause = "utility_step" if largest_step and largest_step != "pytest_fast" else "test_count_growth"
            recommendation = "optimize"
    elif edge_status == "watch":
        status = "watch"
        if profile_slowest_tests:
            likely_cause = "slow_tests"
            recommendation = "optimize_slow_tests"
        elif largest_step == "pytest_fast":
            likely_cause = "test_count_growth"
            recommendation = "profile_slow_tests"
        else:
            likely_cause = "runtime_variance"
            recommendation = "monitor"
    else:
        status = "pass"
        likely_cause = "runtime_variance" if variance_status == "pass" else "unknown"
        recommendation = "monitor"

    return {
        "schema_version": "v1",
        "status": status,
        "current_fast_total_seconds": current,
        "remaining_budget_seconds": remaining_budget,
        "remaining_budget_ratio": remaining_ratio,
        "largest_step": largest_step,
        "largest_step_seconds": largest_step_seconds if largest_step_seconds >= 0 else None,
        "test_count": test_count,
        "tests_deselected": tests_deselected,
        "seconds_per_test": seconds_per_test,
        "test_count_source": "fast_timing_json.test_summary" if test_count is not None else "missing",
        "pytest_runtime_profile_status": profile.get("status"),
        "pytest_runtime_profile_recommendation": profile_recommendation,
        "slowest_tests": profile_slowest_tests,
        "slowest_files": profile_slowest_files,
        "baseline_comparisons": baseline_comparisons,
        "likely_cause": likely_cause,
        "recommendation": recommendation,
        "runtime_edge_status": edge_status,
        "runtime_variance_status": variance_status,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_runtime_watch_triage_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Runtime Watch Triage",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- Current fast total seconds: `{payload.get('current_fast_total_seconds')}`",
            f"- Remaining budget seconds: `{payload.get('remaining_budget_seconds')}`",
            f"- Remaining budget ratio: `{payload.get('remaining_budget_ratio')}`",
            f"- Largest step: `{payload.get('largest_step')}` ({payload.get('largest_step_seconds')}s)",
            f"- test_count: `{payload.get('test_count')}`",
            f"- tests_deselected: `{payload.get('tests_deselected')}`",
            f"- seconds_per_test: `{payload.get('seconds_per_test')}`",
            f"- pytest_runtime_profile_status: `{payload.get('pytest_runtime_profile_status')}`",
            f"- Likely cause: `{payload.get('likely_cause')}`",
            f"- Recommendation: `{payload.get('recommendation')}`",
            "",
            "## Slowest Tests (Profile)",
            "",
            *(
                [
                    f"- `{row.get('seconds')}s` `{row.get('nodeid')}`"
                    for row in (payload.get("slowest_tests") or [])[:10]
                ]
                if payload.get("slowest_tests")
                else ["- none"]
            ),
            "",
            "## Slowest Files (Profile)",
            "",
            *(
                [
                    f"- `{row.get('file')}` total=`{row.get('total_seconds')}s` tests=`{row.get('test_count')}`"
                    for row in (payload.get("slowest_files") or [])[:10]
                ]
                if payload.get("slowest_files")
                else ["- none"]
            ),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
