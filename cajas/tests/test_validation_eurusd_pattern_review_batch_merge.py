"""Test EURUSD pattern review batch merge."""
import json
from pathlib import Path

import pandas as pd
import pytest

from cajas.reports.validation_eurusd_pattern_review_batch_merge import build_batch_merge_report


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def label_schema(temp_dir):
    schema = {
        "schema_version": "eurusd_15m_pattern_review_v2",
        "compatible_schema_versions": ["eurusd_15m_pattern_review_v1", "eurusd_15m_pattern_review_v2"],
        "status": "ready",
        "allowed_values": {
            "human_pattern_label": ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
            "market_context": ["trend", "range", "pullback", "transition", "breakout", "reversal_attempt", "high_volatility", "low_volatility", "unclear"],
            "direction_context": ["up", "down", "neutral", "mixed", "up_pullback", "down_pullback", "reversal_up", "reversal_down", "unclear"]
        },
        "legacy_allowed_values": {"direction_context": ["sideways"]},
    }
    path = temp_dir / "schema.json"
    path.write_text(json.dumps(schema))
    return path


@pytest.fixture
def completion_report_awaiting(temp_dir):
    report = {"status": "awaiting_completed_batch"}
    path = temp_dir / "completion.json"
    path.write_text(json.dumps(report))
    return path


@pytest.fixture
def completion_report_ready(temp_dir):
    report = {"status": "ready"}
    path = temp_dir / "completion.json"
    path.write_text(json.dumps(report))
    return path


def test_merge_missing_completed_batch(temp_dir, completion_report_awaiting, label_schema):
    report = build_batch_merge_report(
        batch_completion_report_json=completion_report_awaiting,
        completed_batch_csv=temp_dir / "completed.csv",
        full_completed_review_csv=temp_dir / "full.csv",
        label_schema_json=label_schema
    )
    
    assert report["status"] == "awaiting_completed_batch"
    assert report["blocking"] is False
    assert report["merge_performed"] is False
    assert report["reviewed_count_added"] == 0
    assert report["next_action"] == "fill_batch_001_review"


def test_merge_creates_new_file(temp_dir, completion_report_ready, label_schema):
    completed_batch = pd.DataFrame({
        "sample_id": ["s1", "s2", "s3"],
        "timestamp": ["2020-01-01T00:00:00+00:00"] * 3,
        "candidate_type": ["test"] * 3,
        "review_status": ["reviewed"] * 3,
        "human_pattern_label": ["valid_pattern"] * 3,
        "market_context": ["trend"] * 3,
        "direction_context": ["up"] * 3
    })
    completed_csv = temp_dir / "completed.csv"
    completed_batch.to_csv(completed_csv, index=False)
    
    full_csv = temp_dir / "full.csv"
    
    report = build_batch_merge_report(
        batch_completion_report_json=completion_report_ready,
        completed_batch_csv=completed_csv,
        full_completed_review_csv=full_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "ready"
    assert report["merge_performed"] is True
    assert report["reviewed_count_added"] == 3
    assert report["reviewed_count_total"] == 3
    assert report["created_new_completed_file"] is True
    assert full_csv.exists()


def test_merge_updates_existing_file(temp_dir, completion_report_ready, label_schema):
    existing_full = pd.DataFrame({
        "sample_id": ["s1", "s2"],
        "timestamp": ["2020-01-01T00:00:00+00:00"] * 2,
        "candidate_type": ["test"] * 2,
        "review_status": ["reviewed", "pending"],
        "human_pattern_label": ["valid_pattern", "unclear"],
        "market_context": ["trend", "unclear"],
        "direction_context": ["up", "unclear"]
    })
    full_csv = temp_dir / "full.csv"
    existing_full.to_csv(full_csv, index=False)
    
    completed_batch = pd.DataFrame({
        "sample_id": ["s2", "s3"],
        "timestamp": ["2020-01-01T00:00:00+00:00"] * 2,
        "candidate_type": ["test"] * 2,
        "review_status": ["reviewed"] * 2,
        "human_pattern_label": ["weak_pattern", "valid_pattern"],
        "market_context": ["range", "trend"],
        "direction_context": ["neutral", "up"]
    })
    completed_csv = temp_dir / "completed.csv"
    completed_batch.to_csv(completed_csv, index=False)
    
    report = build_batch_merge_report(
        batch_completion_report_json=completion_report_ready,
        completed_batch_csv=completed_csv,
        full_completed_review_csv=full_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "ready"
    assert report["merge_performed"] is True
    assert report["reviewed_count_added"] == 2
    assert report["updated_existing_count"] == 1
    assert "backup_path" in report


def test_merge_invalid_enum(temp_dir, completion_report_ready, label_schema):
    completed_batch = pd.DataFrame({
        "sample_id": ["s1"],
        "timestamp": ["2020-01-01T00:00:00+00:00"],
        "candidate_type": ["test"],
        "review_status": ["reviewed"],
        "human_pattern_label": ["invalid_label"],
        "market_context": ["trend"],
        "direction_context": ["up"]
    })
    completed_csv = temp_dir / "completed.csv"
    completed_batch.to_csv(completed_csv, index=False)
    
    full_csv = temp_dir / "full.csv"
    
    report = build_batch_merge_report(
        batch_completion_report_json=completion_report_ready,
        completed_batch_csv=completed_csv,
        full_completed_review_csv=full_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "blocked"
    assert report["merge_performed"] is False
    assert "invalid_enum_values" in report["reason"]


def test_merge_forbidden_columns(temp_dir, completion_report_ready, label_schema):
    completed_batch = pd.DataFrame({
        "sample_id": ["s1"],
        "timestamp": ["2020-01-01T00:00:00+00:00"],
        "candidate_type": ["test"],
        "review_status": ["reviewed"],
        "buy": [1],
        "sell": [0]
    })
    completed_csv = temp_dir / "completed.csv"
    completed_batch.to_csv(completed_csv, index=False)
    
    full_csv = temp_dir / "full.csv"
    
    report = build_batch_merge_report(
        batch_completion_report_json=completion_report_ready,
        completed_batch_csv=completed_csv,
        full_completed_review_csv=full_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "blocked"
    assert report["merge_performed"] is False
    assert "forbidden_trading_columns_detected" in report["reason"]
