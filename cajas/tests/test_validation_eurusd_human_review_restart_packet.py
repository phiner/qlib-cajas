"""Tests for EURUSD human review restart packet."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_human_review_restart_packet import build_human_review_restart_packet


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _build_all(tmp_path: Path, *, trial_status: str = "not_approved", standard_status: str = "review_standard_v0_ready") -> dict:
    return build_human_review_restart_packet(
        language_boundary_json=_write(tmp_path / "language.json", {"status": "language_boundary_ready"}),
        zh_rationale_json=_write(tmp_path / "zh.json", {"status": "zh_rationale_fields_ready"}),
        human_review_quality_json=_write(tmp_path / "quality.json", {"report_status": "awaiting_review_input"}),
        review_standard_json=_write(tmp_path / "standard.json", {"status": standard_status}),
        llm_artifacts_json=_write(tmp_path / "artifacts.json", {"report_status": "llm_review_artifacts_ready"}),
        llm_second_review_json=_write(tmp_path / "second.json", {"report_status": "llm_second_review_protocol_ready"}),
        real_llm_readiness_json=_write(tmp_path / "readiness.json", {"status": "ready_for_explicit_approval"}),
        trial_approval_json=_write(tmp_path / "trial.json", {"status": trial_status}),
        fast_validation_timing_json=_write(tmp_path / "fast.json", {"overall_status": "pass"}),
    )


def test_ready_to_restart_with_expected_statuses(tmp_path: Path) -> None:
    report = _build_all(tmp_path)
    assert report["report_status"] == "ready_to_restart_human_review"


def test_blocks_if_trial_status_not_not_approved(tmp_path: Path) -> None:
    report = _build_all(tmp_path, trial_status="approved")
    assert report["report_status"] == "blocked"


def test_includes_required_zh_fields_and_gui_command(tmp_path: Path) -> None:
    report = _build_all(tmp_path)
    assert "human_rationale_zh" in report["required_zh_fields"]
    assert report["gui_run_command"] == "./scripts/run_eurusd_review_gui.sh"


def test_includes_post_review_commands_and_paths(tmp_path: Path) -> None:
    report = _build_all(tmp_path)
    assert report["post_review_validation_commands"]
    assert report["completed_review_csv_path"].endswith("_completed.csv")
    assert report["review_events_jsonl_path"].endswith("_completed_events.jsonl")


def test_runtime_keys_english_only_and_completed_not_required(tmp_path: Path) -> None:
    report = _build_all(tmp_path)
    assert all(k.isascii() for k in report.keys())
    assert report["human_review_quality_status"] == "awaiting_review_input"


def test_blocks_when_review_standard_missing_or_blocked(tmp_path: Path) -> None:
    report = _build_all(tmp_path, standard_status="blocked")
    assert report["report_status"] == "blocked"
