"""Tests for EURUSD human review quality report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_human_review_quality import build_human_review_quality_report


def _write_batch(path: Path) -> None:
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "candidate_type": ["a", "a", "b"],
            "timestamp": [
                "2026-05-01T00:00:00+00:00",
                "2026-05-01T00:15:00+00:00",
                "2026-05-01T00:30:00+00:00",
            ],
        }
    ).to_csv(path, index=False)


def _write_approval(path: Path, status: str = "not_approved") -> None:
    path.write_text(json.dumps({"approval_status": status}), encoding="utf-8")


def test_missing_completed_is_awaiting_review_input(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval, "not_approved")

    report = build_human_review_quality_report(
        batch_csv=batch,
        completed_csv=tmp_path / "missing.csv",
        approval_json=approval,
    )
    assert report["report_status"] == "awaiting_review_input"
    assert report["completed_review_csv_exists"] is False
    assert report["real_llm_integration_approved"] is False
    assert report["trial_approval_status"] == "not_approved"


def test_malformed_completed_csv_blocks(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval)
    completed.write_text("\x00\x00\x00", encoding="utf-8")

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed, approval_json=approval)
    assert report["report_status"] == "blocked"


def test_empty_completed_headers_is_awaiting_non_crash(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval)
    pd.DataFrame(
        columns=[
            "sample_id",
            "candidate_type",
            "review_updated_at_utc",
            "human_label",
            "human_confidence",
            "human_rationale_zh",
            "human_counterexample_zh",
            "human_uncertainty_reason_zh",
            "human_context_notes_zh",
            "standard_version",
        ]
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed, approval_json=approval)
    assert report["report_status"] == "awaiting_review_input"
    assert report["completed_review_csv_exists"] is True


def test_watch_flags_for_missing_rationale_and_uncertainty_and_high_confidence(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval)
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "candidate_type": ["a", "a", "b"],
            "review_updated_at_utc": ["2026-05-05T00:00:00Z"] * 3,
            "human_label": ["valid_pattern", "unclear", "weak_pattern"],
            "human_confidence": ["high", "medium", "high"],
            "human_rationale_zh": ["", "已有理由", ""],
            "human_counterexample_zh": ["", "", ""],
            "human_uncertainty_reason_zh": ["", "", ""],
            "human_context_notes_zh": ["", "", ""],
            "standard_version": ["eurusd_15m_review_standard_v0", "", "eurusd_15m_review_standard_v0"],
        }
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed, approval_json=approval)
    assert report["report_status"] == "human_review_quality_watch"
    assert report["label_without_rationale_count"] == 2
    assert report["uncertain_without_uncertainty_reason_count"] == 1
    assert report["high_confidence_without_rationale_count"] == 2
    assert report["missing_standard_version_count"] == 1


def test_ready_when_quality_and_standard_version_present(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval)
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "candidate_type": ["a", "b"],
            "review_updated_at_utc": ["2026-05-05T00:00:00Z", "2026-05-05T00:05:00Z"],
            "human_label": ["valid_pattern", "unclear"],
            "human_confidence": ["high", "low"],
            "human_rationale_zh": ["理由1", "理由2"],
            "human_counterexample_zh": ["反例1", ""],
            "human_uncertainty_reason_zh": ["", "上下文不足"],
            "human_context_notes_zh": ["备注1", "备注2"],
            "standard_version": ["eurusd_15m_review_standard_v0", "eurusd_15m_review_standard_v0"],
        }
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed, approval_json=approval)
    assert report["report_status"] == "human_review_quality_ready"
    assert report["reviewed_samples"] == 2
    assert report["missing_standard_version_count"] == 0


def test_non_english_schema_keys_block(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval)
    pd.DataFrame(
        {
            "sample_id": ["s1"],
            "candidate_type": ["a"],
            "review_updated_at_utc": ["2026-05-05T00:00:00Z"],
            "human_label": ["valid_pattern"],
            "human_confidence": ["high"],
            "human_rationale_zh": ["理由"],
            "human_counterexample_zh": [""],
            "human_uncertainty_reason_zh": [""],
            "human_context_notes_zh": [""],
            "standard_version": ["eurusd_15m_review_standard_v0"],
            "中文字段": ["x"],
        }
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed, approval_json=approval)
    assert report["report_status"] == "blocked"


def test_live_provider_markers_in_schema_keys_block(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    approval = tmp_path / "approval.json"
    _write_batch(batch)
    _write_approval(approval)
    pd.DataFrame(
        {
            "sample_id": ["s1"],
            "candidate_type": ["a"],
            "review_updated_at_utc": ["2026-05-05T00:00:00Z"],
            "human_label": ["valid_pattern"],
            "human_confidence": ["high"],
            "human_rationale_zh": ["理由"],
            "human_counterexample_zh": [""],
            "human_uncertainty_reason_zh": [""],
            "human_context_notes_zh": [""],
            "standard_version": ["eurusd_15m_review_standard_v0"],
            "openai_provider": ["x"],
        }
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed, approval_json=approval)
    assert report["report_status"] == "blocked"
