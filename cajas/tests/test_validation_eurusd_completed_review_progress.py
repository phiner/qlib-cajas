"""Tests for EURUSD completed review progress report."""

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_completed_review_progress import (
    build_completed_review_progress_report,
)


def _schema(path: Path):
    path.write_text(
        json.dumps(
            {
                "allowed_values": {
                    "human_pattern_label": ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
                    "market_context": ["trend", "range", "pullback", "transition", "breakout", "reversal_attempt", "high_volatility", "low_volatility", "unclear"],
                    "direction_context": ["up", "down", "neutral", "mixed", "up_pullback", "down_pullback", "reversal_up", "reversal_down", "unclear"],
                    "review_status": ["pending", "reviewed", "needs_recheck", "skip"],
                },
                "legacy_allowed_values": {"direction_context": ["sideways"]},
            }
        ),
        encoding="utf-8",
    )


def _batch(path: Path):
    df = pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00", "2020-01-02T00:00:00+00:00"],
            "candidate_type": ["a", "b", "a"],
        }
    )
    df.to_csv(path, index=False)


def _completed(path: Path):
    df = pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00", "2020-01-02T00:00:00+00:00"],
            "candidate_type": ["a", "b", "a"],
            "review_status": ["reviewed", "pending", "pending"],
            "human_pattern_label": ["valid_pattern", "unclear", "unclear"],
            "market_context": ["trend", "unclear", "unclear"],
            "direction_context": ["up", "unclear", "unclear"],
            "structure_quality": [4, 3, 3],
            "follow_through_quality": [4, 3, 3],
            "review_confidence": [4, 3, 3],
            "review_notes": ["good wick", "", ""],
            "review_updated_at_utc": ["2026-05-04T15:00:00Z", "", ""],
        }
    )
    df.to_csv(path, index=False)


def _events(path: Path):
    rows = [
        {
            "sample_id": "s1",
            "review": {
                "review_status": "reviewed",
                "human_pattern_label": "valid_pattern",
                "market_context": "trend",
                "direction_context": "up",
                "structure_quality": 4,
                "follow_through_quality": 4,
                "review_confidence": 4,
                "review_notes": "good wick",
            },
        },
        {
            "sample_id": "s1",
            "review": {
                "review_status": "reviewed",
                "human_pattern_label": "valid_pattern",
                "market_context": "trend",
                "direction_context": "up",
                "structure_quality": 4,
                "follow_through_quality": 4,
                "review_confidence": 4,
                "review_notes": "good wick",
            },
        },
    ]
    path.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")


def test_progress_valid_in_progress(tmp_path: Path):
    batch = tmp_path / "batch.csv"
    comp = tmp_path / "completed.csv"
    events = tmp_path / "events.jsonl"
    schema = tmp_path / "schema.json"
    _batch(batch)
    _completed(comp)
    _events(events)
    _schema(schema)

    report = build_completed_review_progress_report(
        batch_csv=batch,
        completed_csv=comp,
        events_jsonl=events,
        label_schema_json=schema,
    )
    assert report["status"] in {"valid_in_progress", "warning"}
    assert report["completed_count"] == 1
    assert report["pending_count"] == 2
    assert report["next_action"] == "continue_human_review"


def test_progress_missing_completed_csv(tmp_path: Path):
    batch = tmp_path / "batch.csv"
    schema = tmp_path / "schema.json"
    _batch(batch)
    _schema(schema)
    report = build_completed_review_progress_report(
        batch_csv=batch,
        completed_csv=tmp_path / "missing.csv",
        events_jsonl=tmp_path / "events.jsonl",
        label_schema_json=schema,
    )
    assert report["status"] == "awaiting_review_input"
    assert report["blocking"] is False
    assert report["completed_count"] == 0
    assert report["pending_count"] == 3
    assert report["csv_schema_status"] == "not_applicable"
    assert report["jsonl_audit_status"] == "not_applicable"
    assert report["csv_jsonl_value_compare"] == "not_applicable"
    assert report["preliminary_summary_status"] == "not_applicable"
    assert report["next_action"] == "begin_human_review"


def test_progress_missing_batch_csv_is_blocked(tmp_path: Path):
    schema = tmp_path / "schema.json"
    _schema(schema)
    report = build_completed_review_progress_report(
        batch_csv=tmp_path / "missing_batch.csv",
        completed_csv=tmp_path / "missing_completed.csv",
        events_jsonl=tmp_path / "missing_events.jsonl",
        label_schema_json=schema,
    )
    assert report["status"] == "blocked"
    assert report["reason"] == "batch_csv_missing"
    assert report["blocking"] is True


def test_progress_jsonl_malformed_warning(tmp_path: Path):
    batch = tmp_path / "batch.csv"
    comp = tmp_path / "completed.csv"
    events = tmp_path / "events.jsonl"
    schema = tmp_path / "schema.json"
    _batch(batch)
    _completed(comp)
    _schema(schema)
    events.write_text('{"sample_id":"s1","review":{}}\nnot json\n', encoding="utf-8")
    report = build_completed_review_progress_report(
        batch_csv=batch,
        completed_csv=comp,
        events_jsonl=events,
        label_schema_json=schema,
    )
    assert report["jsonl_malformed_line_count"] == 1
    assert report["status"] in {"warning", "valid_in_progress"}

def test_progress_rejected_counts_and_usable_completion(tmp_path: Path):
    batch = tmp_path / "batch.csv"
    comp = tmp_path / "completed.csv"
    events = tmp_path / "events.jsonl"
    schema = tmp_path / "schema.json"
    rejected = tmp_path / "rejected.csv"
    _batch(batch)
    _completed(comp)
    _events(events)
    _schema(schema)
    pd.DataFrame({"sample_id": ["s2", "s3"]}).to_csv(rejected, index=False)

    report = build_completed_review_progress_report(
        batch_csv=batch,
        completed_csv=comp,
        events_jsonl=events,
        label_schema_json=schema,
        rejected_csv=rejected,
    )
    assert report["rejected_count"] == 2
    assert report["active_reviewable_count"] == 1
    assert report["usable_completed_count"] == 1
    assert report["usable_pending_count"] == 0
    assert report["status"] == "valid_ready_for_summary"
