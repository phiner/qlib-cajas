"""Validation runtime budget checking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class BudgetCheckResult:
    """Budget check result for a component."""

    component: str
    status: str  # "pass", "warn", "fail", "missing"
    observed_seconds: float | None
    budget_seconds: float | None
    delta_seconds: float | None
    ratio: float | None
    warn_margin_seconds: float | None
    reason_code: str
    reviewer_note: str


def load_budget_config(budget_path: Path) -> dict:
    """Load budget configuration."""
    return json.loads(budget_path.read_text(encoding="utf-8"))


def check_component_budget(
    component: str,
    observed_seconds: float | None,
    budget_seconds: float,
    warn_threshold_ratio: float = 1.15,
    warn_margin_seconds: float = 0.0,
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
            warn_margin_seconds=warn_margin_seconds,
            reason_code="missing_required_timing",
            reviewer_note=f"Component '{component}' not found in timing data",
        )

    delta = observed_seconds - budget_seconds
    ratio = observed_seconds / budget_seconds if budget_seconds > 0 else float("inf")

    if observed_seconds <= budget_seconds:
        status = "pass"
        reason_code = "within_budget"
        note = f"Within budget ({observed_seconds:.2f}s <= {budget_seconds:.2f}s)"
    elif delta <= max(0.0, warn_margin_seconds):
        status = "warn"
        reason_code = "within_variance_margin"
        note = (
            f"Over budget but within variance margin "
            f"({observed_seconds:.2f}s vs {budget_seconds:.2f}s, +{delta:.2f}s, margin={warn_margin_seconds:.2f}s)"
        )
    elif ratio <= warn_threshold_ratio:
        status = "warn"
        reason_code = "over_budget_warn"
        note = f"Slightly over budget ({observed_seconds:.2f}s vs {budget_seconds:.2f}s, +{delta:.2f}s)"
    else:
        status = "fail"
        reason_code = "over_budget_fail"
        note = f"Significantly over budget ({observed_seconds:.2f}s vs {budget_seconds:.2f}s, +{delta:.2f}s, {ratio:.2f}x)"

    return BudgetCheckResult(
        component=component,
        status=status,
        observed_seconds=observed_seconds,
        budget_seconds=budget_seconds,
        delta_seconds=delta,
        ratio=ratio,
        warn_margin_seconds=warn_margin_seconds,
        reason_code=reason_code,
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
    warn_margins = budget_config.get("warn_margin_seconds", {})
    global_margin = budget_config.get("global_warn_margin_seconds", 0.0)
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
        margin = warn_margins.get(component, global_margin)
        result = check_component_budget(component, observed, budget_seconds, warn_threshold, float(margin))
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


def _append_issue(issues: list[dict[str, str]], severity: str, code: str, message: str) -> None:
    issues.append({"severity": severity, "code": code, "message": message})


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _build_timing_map(timing_data: dict) -> dict[str, Any]:
    timing_map: dict[str, Any] = {}
    if "results" in timing_data and isinstance(timing_data["results"], list):
        for result in timing_data["results"]:
            if isinstance(result, dict):
                name = result.get("name")
                seconds = result.get("seconds")
                if isinstance(name, str) and seconds is not None:
                    timing_map[name] = seconds
    if "total_seconds" in timing_data:
        timing_map["fast_total"] = timing_data["total_seconds"]
    return timing_map


def assess_timing_consistency(
    timing_data: dict,
    budget_config: dict,
    *,
    expected_tier: str | None = "fast",
    max_age_seconds: int | None = 3600,
    timing_path: Path | None = None,
    now: datetime | None = None,
    step_total_tolerance_seconds: float = 0.75,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    now_dt = now or datetime.now(timezone.utc)
    created_at_raw = timing_data.get("created_at")

    required_meta = ("created_at", "run_id", "tier", "timing_source")
    for field in required_meta:
        if field not in timing_data:
            _append_issue(issues, "warning", "legacy_missing_metadata", f"Timing JSON missing metadata field: {field}")

    created_at: datetime | None = None
    if created_at_raw is not None:
        if not isinstance(created_at_raw, str):
            _append_issue(issues, "warning", "created_at_not_string", "created_at exists but is not a string.")
        else:
            try:
                created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
            except ValueError:
                _append_issue(issues, "warning", "created_at_unparseable", "created_at is present but not parseable ISO datetime.")

    if expected_tier:
        tier = timing_data.get("tier")
        if tier is None:
            _append_issue(issues, "warning", "tier_missing", "tier is missing from timing JSON.")
        elif tier != expected_tier:
            _append_issue(issues, "warning", "tier_mismatch", f"timing tier '{tier}' does not match expected '{expected_tier}'.")

    if max_age_seconds is not None and max_age_seconds >= 0:
        age_seconds: float | None = None
        if timing_path and timing_path.exists():
            age_seconds = max(0.0, now_dt.timestamp() - timing_path.stat().st_mtime)
        elif created_at is not None:
            age_seconds = max(0.0, (now_dt - created_at).total_seconds())
        if age_seconds is not None and age_seconds > max_age_seconds:
            _append_issue(
                issues,
                "warning",
                "timing_stale",
                f"timing JSON appears stale ({age_seconds:.1f}s old; max_age_seconds={max_age_seconds}).",
            )

    timing_map = _build_timing_map(timing_data)
    required_components = set(budget_config.get("required_components", []))
    budgets = budget_config.get("budgets_seconds", {})
    for component in required_components:
        if component in budgets:
            raw_value = timing_map.get(component)
            numeric = _coerce_float(raw_value)
            if raw_value is None:
                _append_issue(issues, "fail", "required_timing_missing", f"Required timing component '{component}' missing.")
            elif numeric is None:
                _append_issue(issues, "fail", "required_timing_not_numeric", f"Required timing component '{component}' is not numeric.")
            elif numeric < 0:
                _append_issue(issues, "fail", "required_timing_negative", f"Required timing component '{component}' is negative ({numeric}).")

    for component, raw_value in timing_map.items():
        numeric = _coerce_float(raw_value)
        if numeric is None:
            _append_issue(issues, "fail", "timing_not_numeric", f"Timing component '{component}' is not numeric.")
        elif numeric < 0:
            _append_issue(issues, "fail", "timing_negative", f"Timing component '{component}' is negative ({numeric}).")

    total_seconds = _coerce_float(timing_data.get("total_seconds"))
    if total_seconds is None and "total_seconds" in timing_data:
        _append_issue(issues, "fail", "total_not_numeric", "total_seconds exists but is not numeric.")
    if isinstance(timing_data.get("results"), list) and total_seconds is not None:
        step_seconds = 0.0
        valid_steps = True
        for item in timing_data["results"]:
            if not isinstance(item, dict):
                continue
            value = _coerce_float(item.get("seconds"))
            if value is None:
                valid_steps = False
                break
            step_seconds += value
        if valid_steps:
            delta = abs(total_seconds - step_seconds)
            if delta > step_total_tolerance_seconds:
                _append_issue(
                    issues,
                    "warning",
                    "total_step_mismatch",
                    f"total_seconds differs from step sum by {delta:.3f}s (> {step_total_tolerance_seconds:.3f}s tolerance).",
                )

    severities = {issue["severity"] for issue in issues}
    if "fail" in severities:
        status = "fail"
    elif "warning" in severities:
        status = "warn"
    else:
        status = "pass"
    return {
        "status": status,
        "issues": issues,
        "expected_tier": expected_tier,
        "max_age_seconds": max_age_seconds,
        "timing_path": str(timing_path) if timing_path else None,
    }


def build_validation_runtime_budget_report(
    timing_data: dict,
    budget_config: dict,
    *,
    expected_tier: str | None = "fast",
    max_age_seconds: int | None = 3600,
    timing_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    results, budget_status = check_validation_runtime_budgets(timing_data, budget_config)
    consistency = assess_timing_consistency(
        timing_data,
        budget_config,
        expected_tier=expected_tier,
        max_age_seconds=max_age_seconds,
        timing_path=timing_path,
        now=now,
    )
    overall_status = budget_status
    if consistency["status"] == "fail":
        overall_status = "fail"
    elif consistency["status"] == "warn" and overall_status == "pass":
        overall_status = "warn"
    return {
        "overall_status": overall_status,
        "budget_status": budget_status,
        "timing_consistency": consistency,
        "warn_threshold_ratio": budget_config.get("warn_threshold_ratio", 1.15),
        "results": [
            {
                "component": r.component,
                "status": r.status,
                "observed_seconds": r.observed_seconds,
                "budget_seconds": r.budget_seconds,
                "delta_seconds": r.delta_seconds,
                "ratio": r.ratio,
                "warn_margin_seconds": r.warn_margin_seconds,
                "reason_code": r.reason_code,
                "reviewer_note": r.reviewer_note,
            }
            for r in results
        ],
    }


def generate_budget_report_markdown(
    results: list[BudgetCheckResult],
    overall_status: str,
    budget_config: dict,
    timing_consistency: dict[str, Any] | None = None,
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
        f"- global_warn_margin_seconds: `{budget_config.get('global_warn_margin_seconds', 0.0)}`",
        "",
        "## Component Budget Status",
        "",
        "| Component | Status | Reason | Observed (s) | Budget (s) | Delta (s) | Ratio | Margin (s) | Type |",
        "|-----------|--------|--------|--------------|------------|-----------|-------|------------|------|",
    ]

    for result in results:
        obs_str = f"{result.observed_seconds:.2f}" if result.observed_seconds is not None else "missing"
        budget_str = f"{result.budget_seconds:.2f}" if result.budget_seconds is not None else "N/A"
        delta_str = f"{result.delta_seconds:+.2f}" if result.delta_seconds is not None else "N/A"
        ratio_str = f"{result.ratio:.2f}x" if result.ratio is not None else "N/A"
        margin_str = f"{result.warn_margin_seconds:.2f}" if result.warn_margin_seconds is not None else "0.00"

        status_icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "missing": "❓"}.get(result.status, "?")

        # Determine component type
        if result.component in required_components:
            comp_type = "🔴 required"
        elif result.component in optional_components:
            comp_type = "optional"
        else:
            comp_type = "unknown"

        lines.append(
            f"| {result.component} | {status_icon} {result.status} | {result.reason_code} | {obs_str} | {budget_str} | {delta_str} | {ratio_str} | {margin_str} | {comp_type} |"
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
        "## Timing Consistency",
        "",
    ])
    if timing_consistency:
        lines.append(f"- timing_consistency_status: `{timing_consistency.get('status', 'warn')}`")
        issues = timing_consistency.get("issues", [])
        if issues:
            lines.append("- timing_consistency_issues:")
            for issue in issues:
                lines.append(
                    f"  - [{issue.get('severity', 'warning')}] {issue.get('code', 'unknown')}: {issue.get('message', '')}"
                )
        else:
            lines.append("- timing_consistency_issues: none")
    else:
        lines.append("- timing_consistency_status: `unknown`")
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
