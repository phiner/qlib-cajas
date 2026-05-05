"""Tests for EURUSD human review feedback report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_human_review_feedback import build_human_review_feedback_report


def test_awaiting_when_completed_missing(tmp_path: Path) -> None:
    report = build_human_review_feedback_report(completed_csv=tmp_path / "missing.csv")
    assert report["report_status"] == "awaiting_review_data"


def test_blocked_on_missing_required_fields(tmp_path: Path) -> None:
    p = tmp_path / "completed.csv"
    pd.DataFrame({"sample_id": ["s1"]}).to_csv(p, index=False)
    report = build_human_review_feedback_report(completed_csv=p)
    assert report["report_status"] == "blocked"


def test_feedback_ready_with_counts(tmp_path: Path) -> None:
    p = tmp_path / "completed.csv"
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "candidate_type": ["a", "b", "a"],
            "human_label": ["valid_pattern", "unclear", "weak_pattern"],
            "human_confidence": ["high", "low", "medium"],
            "human_rationale_zh": ["理由1", "", "理由3"],
            "human_uncertainty_reason_zh": ["", "", ""],
            "review_updated_at_utc": ["2026-05-01T00:00:00Z", "2026-05-01T00:10:00Z", "2026-05-01T00:20:00Z"],
        }
    ).to_csv(p, index=False)
    report = build_human_review_feedback_report(completed_csv=p)
    assert report["report_status"] == "feedback_ready"
    assert report["reviewed_sample_count"] == 3
    assert report["missing_rationale_count"] == 1
    assert report["uncertain_without_uncertainty_reason_count"] == 1
