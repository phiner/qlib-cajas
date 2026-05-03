import json
from pathlib import Path

from cajas.reports.validation_routine_maintenance_continuation import (
    build_validation_routine_maintenance_continuation,
    render_validation_routine_maintenance_continuation_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_routine_maintenance_continuation_happy_path(tmp_path: Path) -> None:
    payload = build_validation_routine_maintenance_continuation(
        post_merge_mainline_report=_write(tmp_path / "mainline.json", {"status": "mainline_validated"}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        optional_followups_report=_write(tmp_path / "followups.json", {"blocking": False, "active_items": [{"id": "slow-test-optimization"}]}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    assert payload["status"] == "routine_continues"
    assert payload["repo_posture"]["fork_relationship"] == "kept"
    assert payload["repo_posture"]["upstream_sync_planned"] is False
    assert payload["repo_posture"]["repo_migration_planned"] is False
    assert payload["repo_posture"]["manual_merge_policy"] == "github_only"


def test_routine_maintenance_continuation_blocked_path(tmp_path: Path) -> None:
    payload = build_validation_routine_maintenance_continuation(
        post_merge_mainline_report=_write(tmp_path / "mainline.json", {"status": "mainline_validated"}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "watch", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": True}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    assert payload["status"] == "blocked"


def test_routine_maintenance_continuation_missing_optional_context(tmp_path: Path) -> None:
    payload = build_validation_routine_maintenance_continuation(
        post_merge_mainline_report=_write(tmp_path / "mainline.json", {"status": "mainline_validated"}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    assert payload["status"] in {"routine_continues", "watch"}
    assert payload["status"] != "blocked"


def test_routine_maintenance_continuation_markdown_policy_lines(tmp_path: Path) -> None:
    payload = build_validation_routine_maintenance_continuation(
        post_merge_mainline_report=_write(tmp_path / "mainline.json", {"status": "mainline_validated"}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        milestone_packet=_write(tmp_path / "milestone.json", {"review_state": "ready_for_review", "blocking": False}),
        review_bundle_manifest=_write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
    )
    md = render_validation_routine_maintenance_continuation_markdown(payload)
    lower = md.lower()
    assert "routine maintenance continues" in lower
    assert "fork relationship is kept" in lower
    assert "no upstream sync is planned in this phase" in lower
    assert "no automated merge operations were performed" in lower
