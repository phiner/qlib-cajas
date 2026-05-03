import json
from pathlib import Path

from cajas.reports.validation_runtime_release_cycle import build_validation_runtime_release_cycle_report


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_inputs(root: Path, *, edge_status: str, budget_status: str, timing_status: str = "pass") -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    edge_path = _write(root / "edge.json", {"status": edge_status, "remaining_budget_seconds": 10, "remaining_budget_ratio": 0.1})
    budget_path = _write(root / "budget.json", {"overall_status": budget_status, "timing_consistency": {"status": timing_status}})
    timing_path = _write(root / "timing.json", {"total_seconds": 90.0})
    return edge_path, budget_path, timing_path


def test_release_cycle_pass_when_all_runtime_gates_pass(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="pass", budget_status="pass")
    variance = _write(tmp_path / "variance.json", {"status": "pass"})
    triage = _write(tmp_path / "triage.json", {"status": "pass"})
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
        runtime_variance_report=variance,
        runtime_watch_triage_report=triage,
    )
    assert report["status"] == "pass"
    assert report["reason_code"] == "runtime_healthy"


def test_release_cycle_warn_when_edge_warn(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="warn", budget_status="pass")
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
    )
    assert report["status"] == "warn"
    assert report["reason_code"] == "runtime_edge_warn"


def test_release_cycle_watch_when_variance_watch(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="pass", budget_status="pass")
    variance = _write(tmp_path / "variance.json", {"status": "watch"})
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
        runtime_variance_report=variance,
    )
    assert report["status"] == "watch"
    assert report["reason_code"] == "runtime_variance_watch"


def test_release_cycle_fail_when_budget_or_timing_fail(tmp_path: Path) -> None:
    edge, budget, timing = _write_inputs(tmp_path, edge_status="pass", budget_status="fail")
    report = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        fast_timing_json=timing,
    )
    assert report["status"] == "fail"
    assert "runtime_budget_status=fail" in report["blocking_runtime_gates"]

    edge2, budget2, timing2 = _write_inputs(tmp_path / "t", edge_status="pass", budget_status="pass", timing_status="fail")
    report2 = build_validation_runtime_release_cycle_report(
        runtime_edge_report=edge2,
        runtime_budget_report=budget2,
        fast_timing_json=timing2,
    )
    assert report2["status"] == "fail"
    assert "timing_consistency_status=fail" in report2["blocking_runtime_gates"]
