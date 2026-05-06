from __future__ import annotations

from pathlib import Path

from cajas.reports.validation_tmp_artifact_cleanup_plan import build_tmp_artifact_cleanup_plan


def test_tmp_cleanup_plan_classifies_files(tmp_path: Path) -> None:
    tmp_root = tmp_path / "tmp"
    (tmp_root / "eurusd").mkdir(parents=True)
    (tmp_root / "eurusd" / "EURUSD_15m_Bid_clean_view.csv").write_text("x", encoding="utf-8")
    (tmp_root / "validation-eurusd-market-state.json").write_text("{}", encoding="utf-8")
    (tmp_root / "eurusd" / "EURUSD_15m_market_state_inspection_packet_completed.csv").write_text("x", encoding="utf-8")
    (tmp_root / "old_report.json").write_text("{}", encoding="utf-8")

    report = build_tmp_artifact_cleanup_plan(tmp_root)
    assert report["report_status"] == "tmp_cleanup_plan_ready"
    assert report["protected_input_count"] >= 1
    assert report["active_artifact_count"] >= 1
    assert report["manual_artifact_count"] >= 1
    assert report["archive_candidate_count"] >= 1
    assert report["dry_run_only"] is True


def test_tmp_cleanup_plan_blocks_when_root_missing(tmp_path: Path) -> None:
    report = build_tmp_artifact_cleanup_plan(tmp_path / "missing")
    assert report["report_status"] == "blocked"
