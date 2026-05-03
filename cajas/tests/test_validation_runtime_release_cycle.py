import json
from pathlib import Path

from cajas.reports.validation_runtime_release_cycle import build_validation_runtime_release_cycle_report


def _write_inputs(root: Path, *, edge_status: str, budget_status: str) -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    edge_path = root / "edge.json"
    budget_path = root / "budget.json"
    timing_path = root / "timing.json"
    edge_path.write_text(
        json.dumps({"status": edge_status, "remaining_budget_seconds": 10, "remaining_budget_ratio": 0.1}),
        encoding="utf-8",
    )
    budget_path.write_text(json.dumps({"overall_status": budget_status}), encoding="utf-8")
    timing_path.write_text(json.dumps({"total_seconds": 90.0}), encoding="utf-8")
    return edge_path, budget_path, timing_path


def test_release_cycle_pass(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="pass", budget_status="pass")
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
    )
    assert report["status"] == "pass"


def test_release_cycle_watch(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="watch", budget_status="pass")
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
    )
    assert report["status"] == "watch"


def test_release_cycle_warn_fail(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="warn", budget_status="pass")
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
    )
    assert report["status"] == "warn"

    edge2, budget2, timing2 = _write_inputs(tmp_path / "x", edge_status="pass", budget_status="fail")
    report2 = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge2,
        runtime_budget_report=budget2,
        fast_timing_json=timing2,
    )
    assert report2["status"] == "fail"


def test_release_cycle_escalates_watch_from_variance(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="pass", budget_status="pass")
    variance = tmp_path / "variance.json"
    variance.write_text(json.dumps({"status": "watch"}), encoding="utf-8")
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
        runtime_variance_report=variance,
    )
    assert report["status"] == "watch"
