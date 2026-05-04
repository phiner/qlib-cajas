"""Tests for EURUSD current review summary report."""

from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_review_summary_current import (
    build_review_summary_current_report,
)


def test_summary_current_deterministic(tmp_path: Path):
    batch = tmp_path / "batch.csv"
    completed = tmp_path / "completed.csv"
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00", "2020-01-02T00:00:00+00:00"],
            "candidate_type": ["a", "b", "a"],
        }
    ).to_csv(batch, index=False)
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00", "2020-01-02T00:00:00+00:00"],
            "candidate_type": ["a", "b", "a"],
            "review_status": ["reviewed", "pending", "reviewed"],
            "human_pattern_label": ["valid_pattern", "unclear", "weak_pattern"],
            "market_context": ["trend", "unclear", "range"],
            "direction_context": ["up", "unclear", "neutral"],
            "structure_quality": [4, 3, 2],
            "follow_through_quality": [4, 3, 2],
            "review_confidence": [5, 3, 2],
            "review_notes": ["good wick", "", "unclear"],
            "review_updated_at_utc": ["2026-05-04T00:00:00Z", "", "2026-05-04T01:00:00Z"],
        }
    ).to_csv(completed, index=False)

    report = build_review_summary_current_report(batch_csv=batch, completed_csv=completed)
    assert report["status"] == "ready"
    assert report["reviewed_count"] == 2
    assert report["counts_by_candidate_type"]["a"] == 2
    assert report["blank_notes_count"] == 0
    assert report["review_note_keyword_counts"]["good wick"] == 1
