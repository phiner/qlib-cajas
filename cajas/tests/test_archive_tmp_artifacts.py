from __future__ import annotations

import json
from pathlib import Path

from cajas.scripts.archive_tmp_artifacts import execute_archive


def _plan(tmp_root: Path, archive_candidates: list[str]) -> dict:
    return {
        "report_status": "tmp_cleanup_plan_ready",
        "tmp_root": str(tmp_root),
        "archive_dir": str(tmp_root / "archive/20260506_000000_market_state_cleanup"),
        "archive_candidates": archive_candidates,
        "protected_paths": ["eurusd/EURUSD_15m_Bid_clean_view.csv"],
        "active_artifact_paths": ["validation-eurusd-market-state.json"],
        "manual_artifact_paths": ["eurusd/EURUSD_15m_market_state_inspection_packet_completed.csv"],
    }


def test_dry_run_does_not_move_files(tmp_path: Path) -> None:
    tmp_root = tmp_path / "tmp"
    (tmp_root / "old.json").parent.mkdir(parents=True)
    (tmp_root / "old.json").write_text("{}", encoding="utf-8")
    plan_json = tmp_path / "plan.json"
    plan_json.write_text(json.dumps(_plan(tmp_root, ["old.json"])), encoding="utf-8")
    result = execute_archive(plan_json, dry_run=True, apply=False)
    assert result["mode"] == "dry_run"
    assert result["would_archive_count"] == 1
    assert (tmp_root / "old.json").exists()


def test_apply_moves_only_archive_candidates_and_preserves_relative_paths(tmp_path: Path) -> None:
    tmp_root = tmp_path / "tmp"
    (tmp_root / "a" / "b.json").parent.mkdir(parents=True)
    (tmp_root / "a" / "b.json").write_text("{}", encoding="utf-8")
    plan_json = tmp_path / "plan.json"
    plan_json.write_text(json.dumps(_plan(tmp_root, ["a/b.json"])), encoding="utf-8")
    result = execute_archive(plan_json, dry_run=False, apply=True)
    assert result["mode"] == "apply"
    archive_dir = Path(result["archive_dir"])
    assert (archive_dir / "a" / "b.json").exists()
    assert not (tmp_root / "a" / "b.json").exists()
    assert Path(result["manifest_json"]).exists()


def test_protected_manual_and_outside_paths_are_rejected(tmp_path: Path) -> None:
    tmp_root = tmp_path / "tmp"
    (tmp_root / "eurusd").mkdir(parents=True)
    (tmp_root / "eurusd/EURUSD_15m_Bid_clean_view.csv").write_text("x", encoding="utf-8")
    (tmp_root / "eurusd/EURUSD_15m_market_state_inspection_packet_completed.csv").write_text("x", encoding="utf-8")
    plan_json = tmp_path / "plan.json"
    plan_json.write_text(
        json.dumps(
            _plan(
                tmp_root,
                [
                    "eurusd/EURUSD_15m_Bid_clean_view.csv",
                    "eurusd/EURUSD_15m_market_state_inspection_packet_completed.csv",
                    "../outside.txt",
                ],
            )
        ),
        encoding="utf-8",
    )
    result = execute_archive(plan_json, dry_run=True, apply=False)
    assert result["blocked_candidate_count"] == 3
    assert result["would_archive_count"] == 0


def test_missing_plan_blocks(tmp_path: Path) -> None:
    try:
        execute_archive(tmp_path / "missing.json", dry_run=True, apply=False)
    except ValueError as exc:
        assert "plan_json_missing" in str(exc)
    else:
        raise AssertionError("expected ValueError")
