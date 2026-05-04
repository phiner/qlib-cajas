"""Tests for EURUSD rejected samples report."""

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_rejected_samples import (
    build_rejected_samples_report,
    format_rejected_samples_markdown,
)


def test_rejected_report_ready(tmp_path: Path):
    csv_path = tmp_path / "rejected.csv"
    jsonl_path = tmp_path / "rejected_events.jsonl"
    df = pd.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00"],
            "candidate_type": ["wick", "wick"],
            "rejection_reason": ["bad_context", "duplicate_region"],
            "rejection_notes": ["n1", "n2"],
            "rejected_at_utc": ["2026-05-04T00:00:00Z", "2026-05-04T01:00:00Z"],
            "review_batch_id": ["b1", "b1"],
            "source_batch_csv": ["batch.csv", "batch.csv"],
            "reviewer_id_optional": ["", ""],
            "schema_version": ["eurusd_15m_rejected_sample_v1", "eurusd_15m_rejected_sample_v1"],
        }
    )
    df.to_csv(csv_path, index=False)
    jsonl_path.write_text(json.dumps({"event_type": "sample_rejected", "sample_id": "s1"}) + "\n", encoding="utf-8")

    report = build_rejected_samples_report(rejected_csv=csv_path, rejected_events_jsonl=jsonl_path)
    assert report["status"] == "ready"
    assert report["rejected_count"] == 2
    assert report["reason_distribution"]["bad_context"] == 1
    md = format_rejected_samples_markdown(report)
    assert "# EURUSD Rejected Samples Report" in md


def test_rejected_report_not_found(tmp_path: Path):
    report = build_rejected_samples_report(
        rejected_csv=tmp_path / "missing.csv",
        rejected_events_jsonl=tmp_path / "missing.jsonl",
    )
    assert report["status"] == "not_found"
    assert report["rejected_count"] == 0
