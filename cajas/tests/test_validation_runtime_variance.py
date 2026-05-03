import json
from pathlib import Path

from cajas.reports.validation_runtime_variance import build_validation_runtime_variance_report


def _write_inputs(root: Path, *, total: float, budget_status: str, timing_status: str = "pass", edge_status: str = "pass") -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    t = root / "timing.json"
    b = root / "budget.json"
    e = root / "edge.json"
    t.write_text(json.dumps({"total_seconds": total}), encoding="utf-8")
    b.write_text(json.dumps({"overall_status": budget_status, "timing_consistency": {"status": timing_status}}), encoding="utf-8")
    e.write_text(json.dumps({"status": edge_status}), encoding="utf-8")
    return t, b, e


def test_runtime_variance_pass_watch_warn_fail(tmp_path: Path) -> None:
    t, b, e = _write_inputs(tmp_path / "p", total=90.0, budget_status="pass")
    rep = build_validation_runtime_variance_report(
        fast_timing_json=t,
        runtime_budget_report=b,
        runtime_edge_report=e,
        baselines=[{"label": "a", "fast_total_seconds": 89.0}],
    )
    assert rep["status"] == "pass"

    t2, b2, e2 = _write_inputs(tmp_path / "w", total=100.0, budget_status="pass")
    rep2 = build_validation_runtime_variance_report(
        fast_timing_json=t2,
        runtime_budget_report=b2,
        runtime_edge_report=e2,
        baselines=[{"label": "a", "fast_total_seconds": 89.0}],
    )
    assert rep2["status"] == "watch"

    t3, b3, e3 = _write_inputs(tmp_path / "wr", total=100.0, budget_status="warn")
    rep3 = build_validation_runtime_variance_report(
        fast_timing_json=t3,
        runtime_budget_report=b3,
        runtime_edge_report=e3,
        baselines=[],
    )
    assert rep3["status"] == "warn"

    t4, b4, e4 = _write_inputs(tmp_path / "f", total=100.0, budget_status="fail")
    rep4 = build_validation_runtime_variance_report(
        fast_timing_json=t4,
        runtime_budget_report=b4,
        runtime_edge_report=e4,
        baselines=[],
    )
    assert rep4["status"] == "fail"
