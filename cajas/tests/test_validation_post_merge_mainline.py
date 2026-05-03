import json
from pathlib import Path

from cajas.reports.validation_post_merge_mainline import (
    build_validation_post_merge_mainline,
    render_validation_post_merge_mainline_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_post_merge_mainline_happy_path(tmp_path: Path) -> None:
    payload = build_validation_post_merge_mainline(
        branch="main",
        source_branch="phase-post-merge-research-next",
        merge_confirmed=True,
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        final_maintenance_handoff_report=_write(tmp_path / "handoff.json", {"status": "ready_for_manual_github_merge"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        routine_stability_watch_closure_report=_write(tmp_path / "watch.json", {"status": "closed_non_blocking"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"blocking": False, "active_items": [{"id": "slow-test-optimization"}]}),
        alias_post_removal_closure_report=_write(tmp_path / "alias.json", {"status": "closed"}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    assert payload["status"] == "mainline_validated"


def test_post_merge_mainline_blocked_path(tmp_path: Path) -> None:
    payload = build_validation_post_merge_mainline(
        branch="main",
        source_branch="phase-post-merge-research-next",
        merge_confirmed=True,
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "watch"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        final_maintenance_handoff_report=_write(tmp_path / "handoff.json", {"status": "ready_for_manual_github_merge"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": True}),
        routine_stability_watch_closure_report=_write(tmp_path / "watch.json", {"status": "closed_non_blocking"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"blocking": False, "active_items": [{"id": "slow-test-optimization"}]}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    assert payload["status"] == "blocked"


def test_post_merge_mainline_watch_when_optional_context_missing(tmp_path: Path) -> None:
    payload = build_validation_post_merge_mainline(
        branch="main",
        source_branch="phase-post-merge-research-next",
        merge_confirmed=False,
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        final_maintenance_handoff_report=_write(tmp_path / "handoff.json", {"status": "ready_for_manual_github_merge"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        routine_stability_watch_closure_report=_write(tmp_path / "watch.json", {"status": "closed_non_blocking"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"blocking": False, "active_items": [{"id": "slow-test-optimization"}]}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    assert payload["status"] == "watch"


def test_post_merge_markdown_mainline_and_no_automated_merge(tmp_path: Path) -> None:
    payload = build_validation_post_merge_mainline(
        branch="main",
        source_branch="phase-post-merge-research-next",
        merge_confirmed=True,
        release_readiness_report=_write(tmp_path / "ready.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        final_maintenance_handoff_report=_write(tmp_path / "handoff.json", {"status": "ready_for_manual_github_merge"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        routine_stability_watch_closure_report=_write(tmp_path / "watch.json", {"status": "closed_non_blocking"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"blocking": False, "active_items": [{"id": "slow-test-optimization"}]}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    md = render_validation_post_merge_mainline_markdown(payload)
    assert "mainline_validated" in md
    assert "continue_routine_maintenance" in md
    assert "No automated merge operations were performed." in md
