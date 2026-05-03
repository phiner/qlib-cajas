import json
from pathlib import Path

from cajas.reports.validation_runtime_edge import (
    build_validation_runtime_edge_report,
    render_validation_runtime_edge_markdown,
)


def _write_inputs(
    root: Path,
    *,
    total: float,
    total_budget: float,
    pytest_fast: float,
    pytest_budget: float,
    overall: str,
    timing_consistency: str = "pass",
) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    timing = {
        "total_seconds": total,
        "results": [
            {"name": "pytest_fast", "seconds": pytest_fast},
        ],
    }
    budget = {
        "overall_status": overall,
        "timing_consistency": {"status": timing_consistency},
        "results": [
            {"component": "fast_total", "budget_seconds": total_budget},
            {"component": "pytest_fast", "budget_seconds": pytest_budget},
        ],
    }
    timing_path = root / "timing.json"
    budget_path = root / "budget.json"
    timing_path.write_text(json.dumps(timing), encoding="utf-8")
    budget_path.write_text(json.dumps(budget), encoding="utf-8")
    return timing_path, budget_path


def test_runtime_edge_pass(tmp_path: Path) -> None:
    timing, budget = _write_inputs(
        tmp_path,
        total=90.0,
        total_budget=105.0,
        pytest_fast=86.0,
        pytest_budget=95.0,
        overall="pass",
    )
    report = build_validation_runtime_edge_report(
        timing_json_path=timing,
        runtime_budget_report_path=budget,
        watch_threshold_ratio=0.10,
    )
    assert report["status"] == "pass"


def test_runtime_edge_watch(tmp_path: Path) -> None:
    timing, budget = _write_inputs(
        tmp_path,
        total=94.0,
        total_budget=105.0,
        pytest_fast=90.0,
        pytest_budget=95.0,
        overall="pass",
    )
    report = build_validation_runtime_edge_report(
        timing_json_path=timing,
        runtime_budget_report_path=budget,
        watch_threshold_ratio=0.15,
    )
    assert report["status"] == "watch"
    assert "remaining_budget_seconds" in report
    md = render_validation_runtime_edge_markdown(report)
    assert "remaining_budget_seconds" in md


def test_runtime_edge_warn_fail_passthrough(tmp_path: Path) -> None:
    timing, budget = _write_inputs(
        tmp_path,
        total=90.0,
        total_budget=105.0,
        pytest_fast=86.0,
        pytest_budget=95.0,
        overall="warn",
    )
    report = build_validation_runtime_edge_report(timing_json_path=timing, runtime_budget_report_path=budget)
    assert report["status"] == "warn"

    timing2, budget2 = _write_inputs(
        tmp_path / "f",
        total=90.0,
        total_budget=105.0,
        pytest_fast=86.0,
        pytest_budget=95.0,
        overall="fail",
    )
    report2 = build_validation_runtime_edge_report(timing_json_path=timing2, runtime_budget_report_path=budget2)
    assert report2["status"] == "fail"
