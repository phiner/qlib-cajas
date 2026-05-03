import json
from pathlib import Path

from cajas.reports.validation_maintenance_cadence import (
    build_validation_maintenance_cadence_report,
    render_validation_maintenance_cadence_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> dict[str, Path]:
    return {
        "release_readiness_report": _write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        "release_ready_closure": _write(tmp_path / "closure.json", {"status": "ready", "ready_for_review": True, "blocking": False, "non_blocking_followups": []}),
        "final_reviewer_packet": _write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        "alias_post_removal_closure": _write(tmp_path / "alias.json", {"status": "closed"}),
        "runtime_budget_report": _write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}}),
        "runtime_edge_report": _write(tmp_path / "edge.json", {"status": "pass"}),
        "runtime_release_cycle_report": _write(tmp_path / "cycle.json", {"status": "pass"}),
        "data_source_audit_report": _write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}}),
    }


def test_maintenance_cadence_routine(tmp_path: Path) -> None:
    payload = build_validation_maintenance_cadence_report(**_inputs(tmp_path))
    assert payload["status"] == "routine"
    assert payload["recommended_cadence"] == "next_release_cycle"
    assert payload["data_source_audit_expected_read_csv_count"] == 29
    md = render_validation_maintenance_cadence_markdown(payload)
    assert "Scope Boundary" in md


def test_maintenance_cadence_active_for_non_blocking_watch(tmp_path: Path) -> None:
    i = _inputs(tmp_path)
    _write(i["runtime_release_cycle_report"], {"status": "watch"})
    payload = build_validation_maintenance_cadence_report(**i)
    assert payload["status"] == "active"
    assert "runtime_release_cycle_status=watch" in payload["watch_items"]


def test_maintenance_cadence_blocked(tmp_path: Path) -> None:
    i = _inputs(tmp_path)
    _write(i["runtime_budget_report"], {"overall_status": "fail", "timing_consistency": {"status": "pass"}})
    payload = build_validation_maintenance_cadence_report(**i)
    assert payload["status"] == "blocked"
    assert "runtime_budget_status=fail" in payload["blocking_reasons"]
