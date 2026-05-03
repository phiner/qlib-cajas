import json
from pathlib import Path

from cajas.reports.validation_runtime_variance_closure import build_validation_runtime_variance_closure


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_variance_closure_closed(tmp_path: Path) -> None:
    report = build_validation_runtime_variance_closure(
        runtime_variance_report=_write(tmp_path / "variance.json", {"status": "pass"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "pass"}),
        runtime_budget_report=_write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}}),
        runtime_edge_report=_write(tmp_path / "edge.json", {"status": "pass"}),
    )
    assert report["status"] == "closed"
    assert report["blocking"] is False


def test_variance_closure_monitoring_only(tmp_path: Path) -> None:
    report = build_validation_runtime_variance_closure(
        runtime_variance_report=_write(tmp_path / "variance.json", {"status": "watch"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "watch"}),
        runtime_budget_report=_write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}}),
        runtime_edge_report=_write(tmp_path / "edge.json", {"status": "pass"}),
    )
    assert report["status"] == "monitoring_only"
    assert report["reason_code"] == "variance_watch_non_blocking"


def test_variance_closure_blocked(tmp_path: Path) -> None:
    report = build_validation_runtime_variance_closure(
        runtime_variance_report=_write(tmp_path / "variance.json", {"status": "pass"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "pass"}),
        runtime_budget_report=_write(tmp_path / "budget.json", {"overall_status": "fail", "timing_consistency": {"status": "pass"}}),
        runtime_edge_report=_write(tmp_path / "edge.json", {"status": "pass"}),
    )
    assert report["status"] == "blocked"
    assert report["blocking"] is True
