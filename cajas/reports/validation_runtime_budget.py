"""Validation runtime budget checking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BudgetCheckResult:
    """Budget check result for a component."""

    component: str
    status: str  # "pass", "warn", "fail", "missing"
    observed_seconds: float | None
    budget_seconds: float | None
    delta_seconds: float | None
    ratio: float | None
    reviewer_note: str


def load_budget_config(budget_path: Path) -> dict:
    """Load budget configuration."""
    return json.loads(budget_path.read_text(encoding="utf-8"))


def check_component_budget(
    component: str,
    observed_seconds: float | None,
    budget_seconds: float,
    warn_threshold_ratio: float = 1.15,
) -> BudgetCheckResult:
    """Check a single component against budget."""
    if observed_seconds is None:
        return BudgetCheckResult(
            component=component,
            status="missing",
            observed_seconds=None,
            budget_seconds=budget_seconds,
            delta_seconds=None,
            ratio=None,
            reviewer_note=f"Component '{component}' not found in timing data",
        )

    delta = observed_seconds - budget_seconds
    ratio = observed_seconds / budget_seconds if budget_seconds > 0 else float("inf")

    if observed_seconds <= budget_seconds:
        status = "pass"
        note = f"Within budget ({observed_seconds:.2f}s <= {budget_seconds:.2f}s)"
    elif ratio <= warn_threshold_ratio:
        status = "warn"
        note = f"Slightly over budget ({observed_seconds:.2f}s vs {budget_seconds:.2f}s, +{delta:.2f}s)"
    else:
        status = "fail"
        note = f"Significantly over budget ({observed_seconds:.2f}s vs {budget_seconds:.2f}s, +{delta:.2f}s, {ratio:.2f}x)"

    return BudgetCheckResult(
        component=component,
        status=status,
        observed_seconds=observed_seconds,
        budget_seconds=budget_seconds,
        delta_seconds=delta,
        ratio=ratio,
        reviewer_note=note,
    )


def check_validation_runtime_budgets(
    timing_data: dict,
    budget_config: dict,
) -> tuple[list[BudgetCheckResult], str]:
    """Check validation runtime against budgets."""
    results = []
    budgets = budget_config["budgets_seconds"]
    warn_threshold = budget_config.get("warn_threshold_ratio", 1.15)
    required_components = set(budget_config.get("required_components", []))
    optional_components = set(budget_config.get("optional_components", []))

    # Extract timing from validation results
    timing_map = {}
    if "results" in timing_data:
        for result in timing_data["results"]:
            name = result.get("name")
            seconds = result.get("seconds")
            if name and seconds is not None:
                timing_map[name] = seconds

    # Check total if available
    if "total_seconds" in timing_data:
        timing_map["fast_total"] = timing_data["total_seconds"]

    # Check each budget
    for component, budget_seconds in budgets.items():
        observed = timing_map.get(component)
        result = check_component_budget(component, observed, budget_seconds, warn_threshold)
        results.append(result)

    # Determine overall status with required/optional distinction
    statuses = [r.status for r in results]

    # Check if any required component is missing or failing
    required_missing = []
    required_failing = []
    for result in results:
        if result.component in required_components:
            if result.status == "missing":
                required_missing.append(result.component)
            elif result.status == "fail":
                required_failing.append(result.component)

    # Check if any measured component is failing
    measured_failing = [r for r in results if r.status == "fail" and r.observed_seconds is not None]
    measured_warning = [r for r in results if r.status == "warn" and r.observed_seconds is not None]

    if required_failing or measured_failing:
        overall_status = "fail"
    elif required_missing or measured_warning:
        overall_status = "warn"
    else:
        overall_status = "pass"

    return results, overall_status


def generate_budget_report_markdown(
    results: list[BudgetCheckResult],
    overall_status: str,
    budget_config: dict,
) -> str:
    """Generate reviewer-friendly Markdown report."""
    required_components = set(budget_config.get("required_components", []))
    optional_components = set(budget_config.get("optional_components", []))

    lines = [
        "# Validation Runtime Budget Report",
        "",
        "**Important**: Runtime budgets are engineering guardrails for validation sustainability. They are not performance claims or trading/model performance metrics.",
        "",
        f"- overall_status: `{overall_status}`",
        f"- warn_threshold_ratio: `{budget_config.get('warn_threshold_ratio', 1.15)}`",
        "",
        "## Component Budget Status",
        "",
        "| Component | Status | Observed (s) | Budget (s) | Delta (s) | Ratio | Type |",
        "|-----------|--------|--------------|------------|-----------|-------|------|",
    ]

    for result in results:
        obs_str = f"{result.observed_seconds:.2f}" if result.observed_seconds is not None else "missing"
        budget_str = f"{result.budget_seconds:.2f}" if result.budget_seconds is not None else "N/A"
        delta_str = f"{result.delta_seconds:+.2f}" if result.delta_seconds is not None else "N/A"
        ratio_str = f"{result.ratio:.2f}x" if result.ratio is not None else "N/A"

        status_icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "missing": "❓"}.get(result.status, "?")

        # Determine component type
        if result.component in required_components:
            comp_type = "🔴 required"
        elif result.component in optional_components:
            comp_type = "optional"
        else:
            comp_type = "unknown"

        lines.append(
            f"| {result.component} | {status_icon} {result.status} | {obs_str} | {budget_str} | {delta_str} | {ratio_str} | {comp_type} |"
        )

    lines.extend([
        "",
        "## Largest Deltas",
        "",
    ])

    # Sort by delta (largest positive first)
    sorted_results = sorted(
        [r for r in results if r.delta_seconds is not None],
        key=lambda r: r.delta_seconds,
        reverse=True,
    )

    if sorted_results:
        for result in sorted_results[:5]:
            lines.append(f"- {result.component}: {result.delta_seconds:+.2f}s ({result.reviewer_note})")
    else:
        lines.append("No timing data available for comparison.")

    lines.extend([
        "",
        "## Reviewer Recommendations",
        "",
    ])

    if overall_status == "fail":
        lines.append("**Action required**: One or more required components significantly exceeded budget or failed. Review slow tests and optimize.")
    elif overall_status == "warn":
        lines.append("**Review recommended**: Some required components missing or measured components slightly over budget.")
    else:
        lines.append("**No action needed**: All required components within budget. Optional component timings may be missing (expected).")

    lines.append("")
    return "\n".join(lines)
