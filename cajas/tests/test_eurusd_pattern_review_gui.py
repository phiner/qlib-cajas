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
    extract_chart_window_with_diagnostics,
    create_candlestick_figure,
    build_chart_diagnostic_summary,
    save_completed_review,
    get_review_progress,
    sanitize_output_columns,
    sanitize_optional_text_value,
)
from cajas.apps.eurusd_pattern_review_app import render_plotly_chart


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
    assert (window["timestamp"] == sample_timestamp).any()


def test_extract_chart_window_with_diagnostics_valid_timestamp(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    sample_timestamp = clean_view.iloc[40]["timestamp"]
    window, diag = extract_chart_window_with_diagnostics(clean_view, sample_timestamp, lookback=8, forward=4)
    assert not window.empty
    assert diag["exact_timestamp_match_found"] is True
    assert diag["nearest_fallback_used"] is False
    assert diag["chart_window_row_count"] > 0
    assert diag["target_index_in_window"] is not None


def test_extract_chart_window_with_diagnostics_missing_timestamp(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    missing_timestamp = pd.Timestamp("2030-01-01 00:00:00")
    window, diag = extract_chart_window_with_diagnostics(clean_view, missing_timestamp)
    assert window.empty
    assert diag["chart_window_row_count"] == 0
    assert diag["error"] == "timestamp_not_found_within_tolerance"


def test_extract_chart_window_with_diagnostics_nearest_fallback(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    off_grid_timestamp = clean_view.iloc[20]["timestamp"] + pd.Timedelta(minutes=1)
    window, diag = extract_chart_window_with_diagnostics(clean_view, off_grid_timestamp)
    assert not window.empty
    assert diag["exact_timestamp_match_found"] is False
    assert diag["nearest_fallback_used"] is True
    assert diag["target_index_in_window"] is not None


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
    fig = create_candlestick_figure(window, sample_timestamp, sample_id="s1", candidate_type="test")
    assert fig is None or hasattr(fig, "to_dict")
    if fig is not None:
        assert len(fig.data) >= 1


def test_get_review_progress(batch_fixture):
    batch_df = load_review_batch(batch_fixture)
    batch_df.loc[0, "review_status"] = "reviewed"
    
    progress = get_review_progress(batch_df)
    
    assert progress["total"] == 3
    assert progress["reviewed"] == 1
    assert progress["pending"] == 2


def test_save_completed_review_sanitizes_nan_notes(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    labels = {
        "review_notes": float("nan"),
        "review_status": "reviewed",
    }
    save_completed_review(batch_df, "s1", labels, output_path)
    completed = pd.read_csv(output_path)
    row = completed.loc[completed["sample_id"] == "s1"].iloc[0]
    assert sanitize_optional_text_value(row["review_notes"]) == ""


def test_build_chart_diagnostic_summary_contains_required_fields():
    diag = {
        "chart_window_row_count": 61,
        "exact_timestamp_match_found": True,
        "nearest_fallback_used": False,
        "target_index_in_window": 33,
    }
    summary = build_chart_diagnostic_summary(diag, trace_count=1)
    assert "61 rows" in summary
    assert "traces: 1" in summary
    assert "exact match: True" in summary
    assert "fallback: False" in summary
    assert "target index: 33" in summary


def test_render_plotly_chart_prefers_width_stretch_and_falls_back():
    calls = []

    class FakeStreamlit:
        def __init__(self):
            self.raise_on_width = True

        def plotly_chart(self, fig, **kwargs):
            calls.append(kwargs)
            if self.raise_on_width and "width" in kwargs:
                self.raise_on_width = False
                raise TypeError("width not supported")

    fake_st = FakeStreamlit()
    render_plotly_chart(fake_st, fig=object())
    assert len(calls) == 2
    assert calls[0].get("width") == "stretch"
    assert calls[1].get("use_container_width") is True
