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
            "test_count": 479,
        },
    )
    edge = _write(tmp_path / "edge.json", {"status": "watch", "remaining_budget_seconds": 11.0, "remaining_budget_ratio": 0.10})
    variance = _write(tmp_path / "variance.json", {"status": "pass"})
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["status"] == "watch"
    assert report["likely_cause"] == "test_count_growth"


def test_runtime_watch_triage_pass_status(tmp_path: Path) -> None:
    timing = _write(
        tmp_path / "timing.json",
        {"total_seconds": 88.0, "results": [{"name": "pytest_fast", "seconds": 84.0}], "test_count": 470},
    )
    edge = _write(tmp_path / "edge.json", {"status": "pass", "remaining_budget_seconds": 17.0, "remaining_budget_ratio": 0.16})
    variance = _write(tmp_path / "variance.json", {"status": "pass"})
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["status"] == "pass"


def test_runtime_watch_triage_warn_status(tmp_path: Path) -> None:
    timing = _write(
        tmp_path / "timing.json",
        {"total_seconds": 99.0, "results": [{"name": "pytest_fast", "seconds": 96.0}], "test_count": 480},
    )
    edge = _write(tmp_path / "edge.json", {"status": "warn", "remaining_budget_seconds": 3.0, "remaining_budget_ratio": 0.03})
    variance = _write(tmp_path / "variance.json", {"status": "watch"})
    report = build_validation_runtime_watch_triage_report(
        fast_timing_json=timing,
        runtime_edge_report=edge,
        runtime_variance_report=variance,
        baselines=[{"label": "p1", "fast_total_seconds": 88.0}],
    )
    assert report["status"] == "warn"
    assert report["recommendation"] == "optimize"
