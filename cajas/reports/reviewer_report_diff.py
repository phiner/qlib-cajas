"""Reviewer report diff generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReviewerDiffResult:
    """Reviewer diff result."""

    overall_status: str  # "pass", "warn", "fail"
    baseline_root: str
    current_root: str
    changed_fields: list[dict]
    missing_artifacts: list[str]
    extra_artifacts: list[str]
    quality_score_delta: float | None
    status_change: dict | None
    contract_error_delta: int | None
    semantic_error_delta: int | None
    drift_breaking_delta: int | None
    runtime_budget_change: dict | None
    reviewer_notes: list[str]


def safe_read_json(path: Path) -> dict | None:
    """Safely read JSON file."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compare_dataset_quality_reports(baseline: dict | None, current: dict | None) -> dict:
    """Compare dataset quality reports."""
    if baseline is None and current is None:
        return {"status": "missing", "delta": None}
    if baseline is None:
        return {"status": "new", "delta": None}
    if current is None:
        return {"status": "removed", "delta": None}

    baseline_score = baseline.get("quality_score", {}).get("score")
    current_score = current.get("quality_score", {}).get("score")
    score_delta = None
    if baseline_score is not None and current_score is not None:
        score_delta = current_score - baseline_score

    baseline_status = baseline.get("status")
    current_status = current.get("status")
    status_change = None
    if baseline_status != current_status:
        status_change = {"baseline": baseline_status, "current": current_status}

    return {
        "status": "changed" if score_delta or status_change else "unchanged",
        "score_delta": score_delta,
        "status_change": status_change,
        "baseline_score": baseline_score,
        "current_score": current_score,
    }


def compare_contract_reports(baseline: dict | None, current: dict | None) -> dict:
    """Compare contract reports."""
    if baseline is None and current is None:
        return {"status": "missing"}
    if baseline is None:
        return {"status": "new"}
    if current is None:
        return {"status": "removed"}

    baseline_status = baseline.get("status")
    current_status = current.get("status")
    baseline_errors = baseline.get("error_count", 0)
    current_errors = current.get("error_count", 0)
    baseline_semantic = baseline.get("semantic_error_count", 0)
    current_semantic = current.get("semantic_error_count", 0)
    baseline_drift = baseline.get("drift_summary", {}).get("breaking_count", 0)
    current_drift = current.get("drift_summary", {}).get("breaking_count", 0)

    return {
        "status": "changed" if baseline_status != current_status else "unchanged",
        "status_change": {"baseline": baseline_status, "current": current_status} if baseline_status != current_status else None,
        "error_delta": current_errors - baseline_errors,
        "semantic_error_delta": current_semantic - baseline_semantic,
        "drift_breaking_delta": current_drift - baseline_drift,
    }


def compare_runtime_budget_reports(baseline: dict | None, current: dict | None) -> dict:
    """Compare runtime budget reports."""
    if baseline is None and current is None:
        return {"status": "missing"}
    if baseline is None:
        return {"status": "new"}
    if current is None:
        return {"status": "removed"}

    baseline_status = baseline.get("overall_status")
    current_status = current.get("overall_status")

    return {
        "status": "changed" if baseline_status != current_status else "unchanged",
        "status_change": {"baseline": baseline_status, "current": current_status} if baseline_status != current_status else None,
    }


def build_reviewer_diff_report(
    baseline_root: Path,
    current_root: Path,
) -> ReviewerDiffResult:
    """Build reviewer diff report."""
    changed_fields = []
    missing_artifacts = []
    extra_artifacts = []
    reviewer_notes = []

    # Compare dataset quality reports
    baseline_dq = safe_read_json(baseline_root / "dataset_quality" / "dataset_quality_report.json")
    current_dq = safe_read_json(current_root / "dataset_quality" / "dataset_quality_report.json")
    dq_diff = compare_dataset_quality_reports(baseline_dq, current_dq)

    quality_score_delta = dq_diff.get("score_delta")
    status_change = dq_diff.get("status_change")

    if dq_diff["status"] == "missing":
        missing_artifacts.append("dataset_quality_report")
    elif dq_diff["status"] == "changed":
        changed_fields.append({"artifact": "dataset_quality_report", "changes": dq_diff})

    # Compare contract reports
    baseline_contract = safe_read_json(baseline_root / "contract" / "dataset_quality_contract_report.json")
    current_contract = safe_read_json(current_root / "contract" / "dataset_quality_contract_report.json")
    contract_diff = compare_contract_reports(baseline_contract, current_contract)

    contract_error_delta = contract_diff.get("error_delta")
    semantic_error_delta = contract_diff.get("semantic_error_delta")
    drift_breaking_delta = contract_diff.get("drift_breaking_delta")

    if contract_diff["status"] == "missing":
        missing_artifacts.append("contract_report")
    elif contract_diff["status"] == "changed":
        changed_fields.append({"artifact": "contract_report", "changes": contract_diff})

    # Compare runtime budget reports (optional)
    baseline_budget = safe_read_json(baseline_root / "validation_runtime_budget_report.json")
    current_budget = safe_read_json(current_root / "validation_runtime_budget_report.json")
    budget_diff = compare_runtime_budget_reports(baseline_budget, current_budget)

    runtime_budget_change = budget_diff.get("status_change")

    if budget_diff["status"] == "missing":
        reviewer_notes.append("Runtime budget reports not present (optional)")
    elif budget_diff["status"] == "changed":
        changed_fields.append({"artifact": "runtime_budget_report", "changes": budget_diff})

    # Determine overall status
    overall_status = "pass"

    # Fail conditions
    if contract_diff.get("status_change") and contract_diff["status_change"]["current"] == "fail":
        overall_status = "fail"
        reviewer_notes.append("Contract status changed to fail")
    elif semantic_error_delta and semantic_error_delta > 0:
        overall_status = "fail"
        reviewer_notes.append(f"Semantic errors increased by {semantic_error_delta}")
    elif drift_breaking_delta and drift_breaking_delta > 0:
        overall_status = "warn"
        reviewer_notes.append(f"Breaking drift increased by {drift_breaking_delta}")

    # Warn conditions
    if quality_score_delta and quality_score_delta < -5:
        if overall_status == "pass":
            overall_status = "warn"
        reviewer_notes.append(f"Quality score decreased by {abs(quality_score_delta):.1f}")

    if missing_artifacts:
        if overall_status == "pass":
            overall_status = "warn"
        reviewer_notes.append(f"Missing artifacts: {', '.join(missing_artifacts)}")

    if not reviewer_notes:
        reviewer_notes.append("No material changes detected")

    return ReviewerDiffResult(
        overall_status=overall_status,
        baseline_root=str(baseline_root),
        current_root=str(current_root),
        changed_fields=changed_fields,
        missing_artifacts=missing_artifacts,
        extra_artifacts=extra_artifacts,
        quality_score_delta=quality_score_delta,
        status_change=status_change,
        contract_error_delta=contract_error_delta,
        semantic_error_delta=semantic_error_delta,
        drift_breaking_delta=drift_breaking_delta,
        runtime_budget_change=runtime_budget_change,
        reviewer_notes=reviewer_notes,
    )


def generate_reviewer_diff_markdown(result: ReviewerDiffResult) -> str:
    """Generate reviewer-friendly Markdown report."""
    lines = [
        "# Reviewer Diff Report",
        "",
        "**Important**: This report compares offline Qlib research infrastructure artifacts only. It is not a trading, execution, alpha, or model performance report.",
        "",
        "## Executive Summary",
        "",
        f"- overall_status: `{result.overall_status}`",
        f"- baseline_root: `{result.baseline_root}`",
        f"- current_root: `{result.current_root}`",
        "",
        "## Key Changes",
        "",
    ]

    if result.quality_score_delta is not None:
        lines.append(f"- Quality Score Delta: {result.quality_score_delta:+.1f}")

    if result.status_change:
        lines.append(f"- Status Change: {result.status_change['baseline']} → {result.status_change['current']}")

    if result.contract_error_delta is not None and result.contract_error_delta != 0:
        lines.append(f"- Contract Error Delta: {result.contract_error_delta:+d}")

    if result.semantic_error_delta is not None and result.semantic_error_delta != 0:
        lines.append(f"- Semantic Error Delta: {result.semantic_error_delta:+d}")

    if result.drift_breaking_delta is not None and result.drift_breaking_delta != 0:
        lines.append(f"- Breaking Drift Delta: {result.drift_breaking_delta:+d}")

    if result.runtime_budget_change:
        lines.append(f"- Runtime Budget Status: {result.runtime_budget_change['baseline']} → {result.runtime_budget_change['current']}")

    if not any([result.quality_score_delta, result.status_change, result.contract_error_delta, result.semantic_error_delta, result.drift_breaking_delta, result.runtime_budget_change]):
        lines.append("- No material changes detected")

    lines.extend([
        "",
        "## Artifact Presence",
        "",
        "| Artifact | Status |",
        "|----------|--------|",
    ])

    all_artifacts = ["dataset_quality_report", "contract_report", "runtime_budget_report"]
    for artifact in all_artifacts:
        if artifact in result.missing_artifacts:
            lines.append(f"| {artifact} | ❌ missing |")
        elif artifact in result.extra_artifacts:
            lines.append(f"| {artifact} | ➕ new |")
        else:
            lines.append(f"| {artifact} | ✅ present |")

    lines.extend([
        "",
        "## Changed Fields",
        "",
    ])

    if result.changed_fields:
        for change in result.changed_fields:
            lines.append(f"### {change['artifact']}")
            lines.append("")
            for key, value in change["changes"].items():
                if value is not None and key != "status":
                    lines.append(f"- {key}: `{value}`")
            lines.append("")
    else:
        lines.append("No changed fields detected.")
        lines.append("")

    lines.extend([
        "## Reviewer Recommendations",
        "",
    ])

    for note in result.reviewer_notes:
        lines.append(f"- {note}")

    lines.append("")
    return "\n".join(lines)
