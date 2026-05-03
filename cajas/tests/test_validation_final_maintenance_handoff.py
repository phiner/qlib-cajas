import json
from pathlib import Path

from cajas.reports.validation_final_maintenance_handoff import (
    build_validation_final_maintenance_handoff,
    render_validation_final_maintenance_handoff_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_final_maintenance_handoff_happy_path(tmp_path: Path) -> None:
    payload = build_validation_final_maintenance_handoff(
        branch="phase-post-merge-research-next",
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        routine_stability_watch_closure=_write(tmp_path / "closure.json", {"status": "closed_non_blocking"}),
        post_freeze_handoff_seal_report=_write(tmp_path / "seal.json", {"status": "sealed"}),
        final_maintenance_archive_closure_report=_write(tmp_path / "archive.json", {"status": "ready"}),
        external_consumer_evidence_closure_report=_write(tmp_path / "external.json", {"status": "closed_unresolved_external"}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"blocking": False, "items": [{"id": "slow-test-optimization"}]}),
    )
    assert payload["status"] == "ready_for_manual_github_merge"
    assert payload["manual_merge_required"] is True
    assert payload["merge_method"] == "manual_github"


def test_final_maintenance_handoff_blocked_path(tmp_path: Path) -> None:
    payload = build_validation_final_maintenance_handoff(
        branch="phase-post-merge-research-next",
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "watch"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": True}),
    )
    assert payload["status"] == "blocked"
    assert payload["blocking"] is True


def test_final_maintenance_handoff_missing_optional_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_final_maintenance_handoff(
        branch="phase-post-merge-research-next",
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed"}),
    )
    assert payload["status"] in {"ready_for_manual_github_merge", "watch"}
    assert payload["status"] != "blocked"


def test_final_maintenance_handoff_markdown_manual_merge_instruction(tmp_path: Path) -> None:
    payload = build_validation_final_maintenance_handoff(
        branch="phase-post-merge-research-next",
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed"}),
    )
    md = render_validation_final_maintenance_handoff_markdown(payload)
    assert "manual" in md.lower()
    assert "github" in md.lower()
    assert "automated merge" in md.lower()
