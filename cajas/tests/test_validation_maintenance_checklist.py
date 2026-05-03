import json
from pathlib import Path

from cajas.reports.validation_maintenance_checklist import (
    build_validation_maintenance_checklist,
    render_validation_maintenance_checklist_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> dict[str, Path]:
    return {
        "maintenance_cadence": _write(tmp_path / "cadence.json", {"status": "routine", "recommended_cadence": "next_release_cycle"}),
        "release_readiness_report": _write(tmp_path / "readiness.json", {"status": "ready"}),
        "final_reviewer_packet": _write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        "milestone_packet": _write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        "runtime_budget_report": _write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}}),
        "runtime_edge_report": _write(tmp_path / "edge.json", {"status": "pass"}),
        "runtime_release_cycle_report": _write(tmp_path / "cycle.json", {"status": "pass"}),
        "manifest_compatibility_report": _write(tmp_path / "compat.json", {"status": "pass"}),
        "data_source_audit_report": _write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}}),
        "optional_followups": _write(tmp_path / "followups.json", {"status": "open", "blocking": False, "items": [{"id": "x", "reason": "foo"}]}),
    }


def test_maintenance_checklist_ready(tmp_path: Path) -> None:
    payload = build_validation_maintenance_checklist(**_inputs(tmp_path))
    assert payload["status"] == "ready"
    assert payload["mode"] == "routine_maintenance"
    assert payload["review_state"] == "ready_for_review"
    assert payload["optional_followups_blocking"] is False
    assert payload["freeze_policy"]["canonical_review_surface"]
    md = render_validation_maintenance_checklist_markdown(payload)
    assert "Artifact Freeze Policy" in md


def test_maintenance_checklist_blocked_on_runtime_fail(tmp_path: Path) -> None:
    i = _inputs(tmp_path)
    _write(i["runtime_budget_report"], {"overall_status": "fail", "timing_consistency": {"status": "pass"}})
    payload = build_validation_maintenance_checklist(**i)
    assert payload["status"] == "blocked"
    assert "runtime_budget_status=fail" in payload["blocking_items"]
