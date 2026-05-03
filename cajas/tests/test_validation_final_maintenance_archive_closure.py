import json
from pathlib import Path

from cajas.reports.validation_final_maintenance_archive_closure import (
    build_validation_final_maintenance_archive_closure,
    render_validation_final_maintenance_archive_closure_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_final_maintenance_archive_closure_ready_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_final_maintenance_archive_closure(
        maintenance_checklist_report=_write(tmp_path / "checklist.json", {"canonical_artifacts": ["a", "b"]}),
        maintenance_governance_closure_report=_write(tmp_path / "gov.json", {"status": "ready"}),
        external_consumer_evidence_closure_report=_write(tmp_path / "external.json", {"status": "closed_confirmed", "blocking": False}),
        optional_followups_report=_write(tmp_path / "followups.json", {"items": [{"id": "slow-test-optimization", "status": "optional"}]}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet_report=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet_report=_write(tmp_path / "milestone.json", {"blocking": False}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed"}),
    )
    assert payload["status"] == "ready"
    assert payload["blocking"] is False
    md = render_validation_final_maintenance_archive_closure_markdown(payload)
    assert "Canonical Review Surface" in md


def test_final_maintenance_archive_closure_fail_when_release_blocked(tmp_path: Path) -> None:
    payload = build_validation_final_maintenance_archive_closure(
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "blocked"}),
        final_reviewer_packet_report=_write(tmp_path / "reviewer.json", {"status": "blocked"}),
        milestone_packet_report=_write(tmp_path / "milestone.json", {"blocking": True}),
        external_consumer_evidence_closure_report=_write(tmp_path / "external.json", {"status": "fail", "blocking": True}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed"}),
    )
    assert payload["status"] == "fail"
    assert payload["blocking"] is True
