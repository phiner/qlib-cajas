"""Test EURUSD pattern review batch completion."""
import json
from pathlib import Path

import pandas as pd
import pytest

from cajas.reports.validation_eurusd_pattern_review_batch_completion import build_batch_completion_report


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def label_schema(temp_dir):
    schema = {
        "schema_version": "eurusd_15m_pattern_review_v1",
        "status": "ready",
        "allowed_values": {
            "human_pattern_label": ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
            "market_context": ["trend", "range", "transition", "high_volatility", "low_volatility", "unclear"],
            "direction_context": ["up", "down", "sideways", "mixed", "unclear"]
        }
    }
    path = temp_dir / "schema.json"
    path.write_text(json.dumps(schema))
    return path


@pytest.fixture
def batch_csv(temp_dir):
    df = pd.DataFrame({
        "timestamp": ["2020-01-01T00:00:00+00:00"] * 10,
        "candidate_type": ["test"] * 10,
        "review_status": ["pending"] * 10
    })
    path = temp_dir / "batch.csv"
    df.to_csv(path, index=False)
    return path


def test_completion_awaiting_completed_batch(temp_dir, batch_csv, label_schema):
    report = build_batch_completion_report(
        batch_csv=batch_csv,
        completed_batch_csv=temp_dir / "completed.csv",
        label_schema_json=label_schema
    )
    
    assert report["status"] == "awaiting_completed_batch"
    assert report["blocking"] is False
    assert report["reviewed_count"] == 0
    assert report["pending_count"] == 10
    assert report["next_action"] == "fill_batch_001_review"


def test_completion_valid_completed_batch(temp_dir, batch_csv, label_schema):
    df = pd.DataFrame({
        "timestamp": ["2020-01-01T00:00:00+00:00"] * 10,
        "candidate_type": ["test"] * 10,
        "review_status": ["reviewed"] * 5 + ["pending"] * 5,
        "human_pattern_label": ["valid_pattern"] * 5 + ["unclear"] * 5,
        "market_context": ["trend"] * 10,
        "direction_context": ["up"] * 10
    })
    completed_csv = temp_dir / "completed.csv"
    df.to_csv(completed_csv, index=False)
    
    report = build_batch_completion_report(
        batch_csv=batch_csv,
        completed_batch_csv=completed_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "ready"
    assert report["reviewed_count"] == 5
    assert report["pending_count"] == 5


def test_completion_invalid_enum(temp_dir, batch_csv, label_schema):
    df = pd.DataFrame({
        "timestamp": ["2020-01-01T00:00:00+00:00"],
        "candidate_type": ["test"],
        "review_status": ["reviewed"],
        "human_pattern_label": ["invalid_label"],
        "market_context": ["trend"],
        "direction_context": ["up"]
    })
    completed_csv = temp_dir / "completed.csv"
    df.to_csv(completed_csv, index=False)
    
    report = build_batch_completion_report(
        batch_csv=batch_csv,
        completed_batch_csv=completed_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "blocked"
    assert "invalid_enum_values" in report["reason"]


def test_completion_forbidden_columns(temp_dir, batch_csv, label_schema):
    df = pd.DataFrame({
        "timestamp": ["2020-01-01T00:00:00+00:00"],
        "candidate_type": ["test"],
        "review_status": ["reviewed"],
        "buy": [1],
        "sell": [0]
    })
    completed_csv = temp_dir / "completed.csv"
    df.to_csv(completed_csv, index=False)
    
    report = build_batch_completion_report(
        batch_csv=batch_csv,
        completed_batch_csv=completed_csv,
        label_schema_json=label_schema
    )
    
    assert report["status"] == "blocked"
    assert "forbidden_trading_columns_detected" in report["reason"]
