import json
from pathlib import Path

from cajas.reports.validation_post_freeze_handoff_seal import (
    build_validation_post_freeze_handoff_seal,
    render_validation_post_freeze_handoff_seal_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_post_freeze_handoff_seal_sealed_when_ready_and_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_post_freeze_handoff_seal(
        external_consumer_evidence_closure_report=_write(tmp_path / "external.json", {"status": "closed_confirmed"}),
        final_maintenance_archive_closure_report=_write(tmp_path / "archive.json", {"status": "ready"}),
        maintenance_governance_closure_report=_write(tmp_path / "governance.json", {"status": "ready"}),
        maintenance_checklist_report=_write(tmp_path / "checklist.json", {"canonical_artifacts": ["a", "b"]}),
        optional_followups_report=_write(tmp_path / "followups.json", {"items": [{"id": "slow-test-optimization", "status": "optional"}]}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet_report=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet_report=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed", "legacy_read_normalization_kept": True}),
        runtime_release_cycle_report=_write(tmp_path / "runtime.json", {"status": "pass"}),
    )
    assert payload["status"] == "sealed"
    assert payload["blocking"] is False
    md = render_validation_post_freeze_handoff_seal_markdown(payload)
    assert "Reviewer Handoff" in md


def test_post_freeze_handoff_seal_fail_when_release_not_ready(tmp_path: Path) -> None:
    payload = build_validation_post_freeze_handoff_seal(
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "watch"}),
        final_reviewer_packet_report=_write(tmp_path / "reviewer.json", {"status": "watch"}),
        milestone_packet_report=_write(tmp_path / "milestone.json", {"review_state": "watch", "blocking": True}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "watch"}),
    )
    assert payload["status"] == "fail"
    assert payload["blocking"] is True
