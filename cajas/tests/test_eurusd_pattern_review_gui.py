"""Test EURUSD pattern review GUI helpers."""
import json
from pathlib import Path

import pandas as pd
import pytest

from cajas.research.eurusd_pattern_review_gui import (
    load_clean_view,
    load_review_batch,
    merge_completed_labels,
    extract_chart_window,
    create_candlestick_figure,
    save_completed_review,
    get_review_progress,
    sanitize_output_columns,
)


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def clean_view_fixture(temp_dir):
    dates = pd.date_range("2020-01-01", periods=100, freq="15min")
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [1.1 + i * 0.0001 for i in range(100)],
        "high": [1.1 + i * 0.0001 + 0.0002 for i in range(100)],
        "low": [1.1 + i * 0.0001 - 0.0001 for i in range(100)],
        "close": [1.1 + i * 0.0001 + 0.0001 for i in range(100)]
    })
    path = temp_dir / "clean_view.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def batch_fixture(temp_dir):
    df = pd.DataFrame({
        "sample_id": ["s1", "s2", "s3"],
        "timestamp": pd.to_datetime(["2020-01-01 01:00:00", "2020-01-01 02:00:00", "2020-01-01 03:00:00"]),
        "candidate_type": ["test"] * 3,
        "confidence_score": [0.8, 0.7, 0.9],
        "review_priority": ["high", "low", "high"],
        "reason_codes": ["test"] * 3,
        "review_status": ["pending"] * 3,
        "human_pattern_label": ["unclear"] * 3,
        "market_context": ["unclear"] * 3,
        "direction_context": ["unclear"] * 3,
        "structure_quality": [3] * 3,
        "follow_through_quality": [3] * 3,
        "review_confidence": [3] * 3,
        "review_notes": [""] * 3
    })
    path = temp_dir / "batch.csv"
    df.to_csv(path, index=False)
    return path


def test_load_clean_view(clean_view_fixture):
    df = load_clean_view(clean_view_fixture)
    assert len(df) == 100
    assert "timestamp" in df.columns


def test_load_review_batch(batch_fixture):
    df = load_review_batch(batch_fixture)
    assert len(df) == 3
    assert "sample_id" in df.columns


def test_merge_completed_labels(batch_fixture):
    batch_df = load_review_batch(batch_fixture)
    
    completed_df = pd.DataFrame({
        "sample_id": ["s1"],
        "timestamp": pd.to_datetime(["2020-01-01 01:00:00"]),
        "human_pattern_label": ["valid_pattern"],
        "review_status": ["reviewed"]
    })
    
    merged = merge_completed_labels(batch_df, completed_df)
    
    assert merged.loc[merged["sample_id"] == "s1", "human_pattern_label"].iloc[0] == "valid_pattern"
    assert merged.loc[merged["sample_id"] == "s1", "review_status"].iloc[0] == "reviewed"
    assert merged.loc[merged["sample_id"] == "s2", "review_status"].iloc[0] == "pending"


def test_extract_chart_window(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    sample_timestamp = clean_view.iloc[50]["timestamp"]
    
    window = extract_chart_window(clean_view, sample_timestamp, lookback=10, forward=5)
    
    assert len(window) <= 16
    assert sample_timestamp in window["timestamp"].values


def test_save_completed_review(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    
    labels = {
        "human_pattern_label": "valid_pattern",
        "market_context": "trend",
        "direction_context": "up",
        "structure_quality": 5,
        "follow_through_quality": 4,
        "review_confidence": 5,
        "review_notes": "test note",
        "review_status": "reviewed"
    }
    
    save_completed_review(batch_df, "s1", labels, output_path)
    
    assert output_path.exists()
    completed = pd.read_csv(output_path)
    assert completed.loc[completed["sample_id"] == "s1", "human_pattern_label"].iloc[0] == "valid_pattern"


def test_save_blocks_forbidden_columns(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    
    labels = {
        "human_pattern_label": "valid_pattern",
        "buy": 1,
        "sell": 0,
        "review_status": "reviewed"
    }
    
    save_completed_review(batch_df, "s1", labels, output_path)
    
    completed = pd.read_csv(output_path)
    assert "buy" not in completed.columns
    assert "sell" not in completed.columns


def test_save_completed_review_deduplicates_sample_id(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    existing = batch_df.copy()
    existing = pd.concat([existing, existing.iloc[[0]]], ignore_index=True)
    existing.to_csv(output_path, index=False)

    save_completed_review(batch_df, "s1", {"review_status": "reviewed"}, output_path)
    completed = pd.read_csv(output_path)
    assert completed["sample_id"].value_counts().get("s1", 0) == 1


def test_sanitize_output_columns():
    df = pd.DataFrame({"sample_id": ["s1"], "buy": [1], "review_status": ["pending"]})
    out = sanitize_output_columns(df)
    assert "buy" not in out.columns
    assert "review_status" in out.columns


def test_create_candlestick_figure_optional_dependency(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    sample_timestamp = clean_view.iloc[10]["timestamp"]
    window = extract_chart_window(clean_view, sample_timestamp, lookback=5, forward=5)
    fig = create_candlestick_figure(window, sample_timestamp)
    assert fig is None or hasattr(fig, "to_dict")


def test_get_review_progress(batch_fixture):
    batch_df = load_review_batch(batch_fixture)
    batch_df.loc[0, "review_status"] = "reviewed"
    
    progress = get_review_progress(batch_df)
    
    assert progress["total"] == 3
    assert progress["reviewed"] == 1
    assert progress["pending"] == 2
