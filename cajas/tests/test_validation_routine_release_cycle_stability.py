import json
from pathlib import Path

from cajas.reports.validation_routine_release_cycle_stability import (
    build_validation_routine_release_cycle_stability,
    render_validation_routine_release_cycle_stability_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_routine_release_cycle_stability_stable(tmp_path: Path) -> None:
    report = build_validation_routine_release_cycle_stability(
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        runtime_budget_report=_write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}}),
        runtime_edge_report=_write(tmp_path / "edge.json", {"status": "pass"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "pass"}),
        runtime_variance_closure_report=_write(tmp_path / "variance.json", {"status": "closed"}),
        data_source_audit_report=_write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}}),
        maintenance_checklist=_write(tmp_path / "checklist.json", {"status": "ready"}),
        maintenance_governance_closure=_write(tmp_path / "governance.json", {"status": "ready"}),
        final_maintenance_archive_closure_report=_write(tmp_path / "archive.json", {"status": "ready", "blocking": False}),
        external_consumer_evidence_closure_report=_write(tmp_path / "external.json", {"status": "closed_unresolved_external", "blocking": False}),
        post_freeze_handoff_seal_report=_write(tmp_path / "handoff.json", {"status": "sealed", "blocking": False}),
        optional_followups=_write(tmp_path / "followups.json", {"status": "open", "blocking": False, "items": []}),
    )
    assert report["status"] == "stable"
    assert report["review_state"] == "ready_for_review"
    assert report["blocking"] is False
    md = render_validation_routine_release_cycle_stability_markdown(report)
    assert "Validation Routine Release-Cycle Stability" in md


def test_routine_release_cycle_stability_watch_with_optional_followups(tmp_path: Path) -> None:
    report = build_validation_routine_release_cycle_stability(
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        runtime_budget_report=_write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}}),
        runtime_edge_report=_write(tmp_path / "edge.json", {"status": "pass"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "pass"}),
        runtime_variance_closure_report=_write(tmp_path / "variance.json", {"status": "closed"}),
        data_source_audit_report=_write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}}),
        optional_followups=_write(tmp_path / "followups.json", {"status": "open", "blocking": False, "items": [{"id": "x"}]}),
    )
    assert report["status"] == "watch"
    assert report["review_state"] == "ready_for_review"


def test_routine_release_cycle_stability_blocked_when_runtime_fails(tmp_path: Path) -> None:
    report = build_validation_routine_release_cycle_stability(
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        runtime_budget_report=_write(tmp_path / "budget.json", {"overall_status": "fail", "timing_consistency": {"status": "pass"}}),
        runtime_edge_report=_write(tmp_path / "edge.json", {"status": "pass"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "pass"}),
        runtime_variance_closure_report=_write(tmp_path / "variance.json", {"status": "closed"}),
        data_source_audit_report=_write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}}),
    )
    assert report["status"] == "blocked"
    assert report["blocking"] is True
