"""Tests for EURUSD human review quality report."""

from __future__ import annotations

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


def test_blocked_when_completed_missing(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    _write_batch(batch)
    report = build_human_review_quality_report(batch_csv=batch, completed_csv=tmp_path / "missing.csv")
    assert report["status"] == "blocked"


def test_watch_flags_for_missing_rationale_rules(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    _write_batch(batch)
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
        }
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed)
    assert report["status"] == "human_review_quality_watch"
    assert report["samples_with_label_but_no_rationale"] == 2
    assert report["samples_uncertain_but_missing_uncertainty_reason"] == 1
    assert report["samples_high_confidence_but_empty_rationale"] == 2


def test_ready_when_core_completeness_present(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    _write_batch(batch)
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
        }
    ).to_csv(completed, index=False)

    report = build_human_review_quality_report(batch_csv=batch, completed_csv=completed)
    assert report["status"] == "human_review_quality_ready"
    assert report["reviewed_samples"] == 2
    assert report["samples_with_human_label"] == 2
    assert report["samples_with_human_confidence"] == 2
    assert report["samples_with_human_rationale_zh"] == 2
    assert report["samples_uncertain_but_missing_uncertainty_reason"] == 0
    assert report["standard_version"] == "eurusd_15m_review_standard_v0"
