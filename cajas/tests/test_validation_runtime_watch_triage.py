import json
from pathlib import Path

from cajas.reports.validation_runtime_watch_triage import build_validation_runtime_watch_triage_report


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_runtime_watch_triage_watch_status(tmp_path: Path) -> None:
    timing = _write(
        tmp_path / "timing.json",
        {
            "total_seconds": 94.0,
            "results": [{"name": "compileall", "seconds": 0.1}, {"name": "pytest_fast", "seconds": 90.0}],
            "test_summary": {"passed": 479, "deselected": 16, "failed": 0, "total_reported": 495},
        },
    )
    edge = _write(tmp_path / "edge.json", {"status": "watch", "remaining_budget_seconds": 11.0, "remaining_budget_ratio": 0.10})
    variance = _write(tmp_path / "variance.json", {"status": "pass"})
    profile = _write(
        tmp_path / "profile.json",
        {"status": "watch", "recommendation": "monitor", "slowest_tests": [], "slowest_files": []},
    )
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        pytest_runtime_profile=profile,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["status"] == "watch"
    assert report["likely_cause"] == "test_count_growth"
    assert report["test_count"] == 479
    assert report["seconds_per_test"] is not None


def test_runtime_watch_triage_pass_status(tmp_path: Path) -> None:
    timing = _write(
        tmp_path / "timing.json",
        {"total_seconds": 88.0, "results": [{"name": "pytest_fast", "seconds": 84.0}], "test_summary": {"passed": 470, "deselected": 10, "failed": 0}},
    )
    edge = _write(tmp_path / "edge.json", {"status": "pass", "remaining_budget_seconds": 17.0, "remaining_budget_ratio": 0.16})
    variance = _write(tmp_path / "variance.json", {"status": "pass"})
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        pytest_runtime_profile=None,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["status"] == "pass"


def test_runtime_watch_triage_warn_status(tmp_path: Path) -> None:
    timing = _write(
        tmp_path / "timing.json",
        {"total_seconds": 99.0, "results": [{"name": "pytest_fast", "seconds": 96.0}], "test_summary": {"passed": 480, "deselected": 15, "failed": 0}},
    )
    edge = _write(tmp_path / "edge.json", {"status": "warn", "remaining_budget_seconds": 3.0, "remaining_budget_ratio": 0.03})
    variance = _write(tmp_path / "variance.json", {"status": "watch"})
    profile = _write(
        tmp_path / "profile.json",
        {
            "status": "warn",
            "recommendation": "optimize_slow_tests",
            "slowest_tests": [{"nodeid": "cajas/tests/test_big.py::test_x", "seconds": 3.2}],
            "slowest_files": [{"file": "cajas/tests/test_big.py", "total_seconds": 3.2, "test_count": 1}],
        },
    )
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        pytest_runtime_profile=profile,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["status"] == "warn"
    assert report["recommendation"] == "optimize_slow_tests"
    assert report["likely_cause"] == "slow_tests"


def test_runtime_watch_triage_compatible_when_test_summary_missing(tmp_path: Path) -> None:
    timing = _write(tmp_path / "timing.json", {"total_seconds": 90.0, "results": [{"name": "pytest_fast", "seconds": 85.0}]})
    edge = _write(tmp_path / "edge.json", {"status": "pass", "remaining_budget_seconds": 15.0, "remaining_budget_ratio": 0.15})
    variance = _write(tmp_path / "variance.json", {"status": "pass"})
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        pytest_runtime_profile=None,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["test_count"] is None
