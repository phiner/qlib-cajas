import json
from pathlib import Path

from cajas.reports.validation_routine_stability_watch_closure import (
    build_validation_routine_stability_watch_closure,
    render_validation_routine_stability_watch_closure_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_routine_stability_watch_closure_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_routine_stability_watch_closure(
        routine_release_cycle_stability_report=_write(
            tmp_path / "stability.json", {"status": "watch", "blocking": False}
        ),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(
            tmp_path / "milestone.json",
            {"review_state": "ready_for_review", "blocking": False},
        ),
        optional_followups_report=_write(
            tmp_path / "followups.json",
            {"status": "open", "blocking": False, "items": [{"id": "slow-test-optimization"}]},
        ),
    )
    assert payload["status"] == "closed_non_blocking"
    assert payload["blocking"] is False
    assert payload["optional_followup_count"] == 1
    assert payload["remaining_followup_type"] == "slow_test_optimization"
    md = render_validation_routine_stability_watch_closure_markdown(payload)
    assert "non-blocking maintenance signal" in md


def test_routine_stability_watch_closure_blocked_when_readiness_not_ready(tmp_path: Path) -> None:
    payload = build_validation_routine_stability_watch_closure(
        routine_release_cycle_stability_report=_write(
            tmp_path / "stability.json", {"status": "watch", "blocking": False}
        ),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "watch"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(
            tmp_path / "milestone.json",
            {"review_state": "ready_for_review", "blocking": False},
        ),
        optional_followups_report=_write(
            tmp_path / "followups.json",
            {"status": "open", "blocking": False, "items": [{"id": "slow-test-optimization"}]},
        ),
    )
    assert payload["status"] == "blocked"
    assert payload["blocking"] is True
    assert "release_readiness_not_ready" in payload["reason_details"]


def test_routine_stability_watch_closure_missing_optional_followups(tmp_path: Path) -> None:
    payload = build_validation_routine_stability_watch_closure(
        routine_release_cycle_stability_report=_write(
            tmp_path / "stability.json", {"status": "watch", "blocking": False}
        ),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(
            tmp_path / "milestone.json",
            {"review_state": "ready_for_review", "blocking": False},
        ),
    )
    assert payload["status"] == "closed_non_blocking"
    assert "optional_followups_report_missing" in payload["reason_details"]
