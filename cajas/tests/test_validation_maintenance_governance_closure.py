import json
from pathlib import Path

from cajas.reports.validation_maintenance_governance_closure import (
    build_validation_maintenance_governance_closure,
    render_validation_maintenance_governance_closure_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_governance_closure_routine(tmp_path: Path) -> None:
    payload = build_validation_maintenance_governance_closure(
        maintenance_checklist=_write(tmp_path / "checklist.json", {"status": "ready"}),
        optional_followups=_write(tmp_path / "followups.json", {"status": "open", "blocking": False, "items": [{}, {}]}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"overall_status": "watch", "review_state": "ready_for_review", "blocking": False}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        alias_post_removal_closure=_write(tmp_path / "alias.json", {"status": "closed"}),
        runtime_release_cycle_report=_write(tmp_path / "cycle.json", {"status": "pass"}),
        runtime_variance_closure_report=_write(tmp_path / "variance_closure.json", {"status": "closed"}),
    )
    assert payload["conclusion"] == "routine"
    assert payload["status"] == "ready"
    md = render_validation_maintenance_governance_closure_markdown(payload)
    assert "Scope Boundary" in md


def test_governance_closure_blocked_when_followups_blocking(tmp_path: Path) -> None:
    payload = build_validation_maintenance_governance_closure(
        maintenance_checklist=_write(tmp_path / "checklist.json", {"status": "ready"}),
        optional_followups=_write(tmp_path / "followups.json", {"status": "blocked", "blocking": True, "items": []}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"overall_status": "watch", "review_state": "ready_for_review", "blocking": False}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        alias_post_removal_closure=_write(tmp_path / "alias.json", {"status": "closed"}),
    )
    assert payload["conclusion"] == "blocked"
    assert payload["status"] == "blocked"
