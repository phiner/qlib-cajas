"""Test EURUSD pattern review GUI helpers."""
import json
from pathlib import Path

import pandas as pd
import pytest

from cajas.research.eurusd_pattern_review_gui import (
    REVIEW_FIELDS,
    load_clean_view,
    load_review_batch,
    merge_completed_labels,
    extract_chart_window,
    extract_chart_window_with_diagnostics,
    compute_sample_window_bounds,
    format_compact_tick_label,
    build_sample_marker_config,
    compute_sample_marker_y,
    compute_sample_guide_line_x,
    create_candlestick_figure,
    detect_time_axis_gaps,
    build_compressed_gap_axis,
    summarize_compressed_gap_axis,
    build_chart_diagnostic_summary,
    build_compact_chart_diagnostic_summary,
    get_chart_height,
    clamp_sample_index,
    next_sample_index,
    previous_sample_index,
    should_advance_after_save,
    build_compact_save_feedback_message,
    default_review_values,
    build_review_update_row,
    save_review_action,
    save_or_update_completed_review,
    append_review_event_jsonl,
    build_persistence_status_message,
    save_completed_review,
    get_review_progress,
    sanitize_output_columns,
    sanitize_optional_text_value,
    load_rejected_samples,
    get_rejected_sample_ids,
    reject_sample_action,
    next_non_rejected_sample_index,
    previous_non_rejected_sample_index,
)
from cajas.apps.eurusd_pattern_review_app import (
    render_plotly_chart,
    build_compact_chart_status_line,
    enqueue_pending_toast,
    consume_pending_toast_once,
    sample_number_to_global_index,
    global_index_to_sample_number,
    apply_pending_global_sample_index,
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
    assert diag["window_start"] is not None
    assert diag["window_end"] is not None
    assert diag["sample_position_ratio"] is not None
    assert diag["framing_source_kind"] in {"clean_view_source", "full_ohlc_source"}
    assert abs(diag["target_index_in_window"] - int(round((len(window) - 1) * 0.6))) <= 2


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


def test_compute_sample_window_bounds_middle():
    start, end = compute_sample_window_bounds(100, 200, 101, pre_context_ratio=0.6)
    assert (end - start) == 101
    assert 0 <= start < end <= 200
    assert (100 - start) in {60, 61}


def test_compute_sample_window_bounds_edges():
    start_a, end_a = compute_sample_window_bounds(1, 30, 21, pre_context_ratio=0.6)
    assert start_a == 0
    assert end_a == 21
    start_b, end_b = compute_sample_window_bounds(28, 30, 21, pre_context_ratio=0.6)
    assert start_b == 9
    assert end_b == 30


def test_compute_sample_window_bounds_spec_normal_case():
    start, end = compute_sample_window_bounds(500, 1000, 120, pre_context_ratio=0.6)
    assert start == 428
    assert end == 548
    sample_display_index = 500 - start
    assert sample_display_index == 72
    ratio = sample_display_index / (120 - 1)
    assert 0.55 <= ratio <= 0.65


def test_compute_sample_window_bounds_spec_near_start_case():
    start, end = compute_sample_window_bounds(10, 1000, 120, pre_context_ratio=0.6)
    assert start == 0
    assert end == 120
    assert (10 - start) == 10


def test_compute_sample_window_bounds_spec_near_end_case():
    start, end = compute_sample_window_bounds(980, 1000, 120, pre_context_ratio=0.6)
    assert start == 880
    assert end == 1000
    assert (980 - start) == 100


def test_extract_chart_window_with_diagnostics_sample_position_ratio_not_left_non_boundary(clean_view_fixture):
    dates = pd.date_range("2020-01-01", periods=1000, freq="15min")
    clean_view = pd.DataFrame(
        {
            "timestamp": dates,
            "open": [1.1 + i * 0.0001 for i in range(1000)],
            "high": [1.1 + i * 0.0001 + 0.0002 for i in range(1000)],
            "low": [1.1 + i * 0.0001 - 0.0001 for i in range(1000)],
            "close": [1.1 + i * 0.0001 + 0.0001 for i in range(1000)],
        }
    )
    sample_timestamp = clean_view.iloc[500]["timestamp"]
    _, diag = extract_chart_window_with_diagnostics(
        clean_view,
        sample_timestamp,
        lookback=72,
        forward=48,
        pre_context_ratio=0.6,
    )
    assert diag["boundary_clamp_start"] is False
    assert diag["sample_position_ratio"] is not None
    assert float(diag["sample_position_ratio"]) > 0.4


def test_extract_chart_window_full_source_framing_and_debug_fields():
    dates = pd.date_range("2020-01-01", periods=300, freq="15min")
    full_df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": [1.2 + i * 0.0001 for i in range(300)],
            "high": [1.2 + i * 0.0001 + 0.0002 for i in range(300)],
            "low": [1.2 + i * 0.0001 - 0.0001 for i in range(300)],
            "close": [1.2 + i * 0.0001 + 0.0001 for i in range(300)],
        }
    )
    sample_ts = full_df.iloc[150]["timestamp"]
    window, diag = extract_chart_window_with_diagnostics(
        full_df,
        sample_ts,
        lookback=72,
        forward=48,
        pre_context_ratio=0.6,
        full_ohlc_source=full_df,
    )
    assert not window.empty
    assert diag["framing_source_kind"] == "full_ohlc_source"
    assert diag["full_source_row_count"] == 300
    assert diag["window_start"] == 77
    assert diag["window_end"] == 198
    assert diag["target_index_in_window"] == 73
    assert 0.55 <= float(diag["sample_position_ratio"]) <= 0.7
    assert diag["boundary_clamp_start"] is False
    assert diag["source_min_timestamp"] is not None
    assert diag["source_max_timestamp"] is not None


def test_extract_chart_window_prefers_full_source_over_pre_sliced_source():
    dates = pd.date_range("2020-01-01", periods=300, freq="15min")
    full_df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": [1.3 + i * 0.0001 for i in range(300)],
            "high": [1.3 + i * 0.0001 + 0.0002 for i in range(300)],
            "low": [1.3 + i * 0.0001 - 0.0001 for i in range(300)],
            "close": [1.3 + i * 0.0001 + 0.0001 for i in range(300)],
        }
    )
    sample_ts = full_df.iloc[150]["timestamp"]
    pre_sliced = full_df.iloc[150:220].reset_index(drop=True)
    _, diag = extract_chart_window_with_diagnostics(
        pre_sliced,
        sample_ts,
        lookback=72,
        forward=48,
        pre_context_ratio=0.6,
        full_ohlc_source=full_df,
    )
    assert diag["framing_source_kind"] == "full_ohlc_source"
    assert diag["target_index_in_window"] > 0
    assert float(diag["sample_position_ratio"]) > 0.4
    assert diag["boundary_clamp_start"] is False


def test_extract_chart_window_string_timestamp_and_fallback_flag():
    dates = pd.date_range("2020-01-01", periods=300, freq="15min")
    full_df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": [1.4 + i * 0.0001 for i in range(300)],
            "high": [1.4 + i * 0.0001 + 0.0002 for i in range(300)],
            "low": [1.4 + i * 0.0001 - 0.0001 for i in range(300)],
            "close": [1.4 + i * 0.0001 + 0.0001 for i in range(300)],
        }
    )
    exact_ts = str(full_df.iloc[100]["timestamp"])
    _, exact_diag = extract_chart_window_with_diagnostics(
        full_df,
        exact_ts,
        full_ohlc_source=full_df,
    )
    assert exact_diag["exact_timestamp_match_found"] is True
    assert exact_diag["nearest_fallback_used"] is False
    off_grid = pd.Timestamp(full_df.iloc[100]["timestamp"]) + pd.Timedelta(minutes=1)
    _, near_diag = extract_chart_window_with_diagnostics(
        full_df,
        off_grid,
        full_ohlc_source=full_df,
    )
    assert near_diag["exact_timestamp_match_found"] is False
    assert near_diag["nearest_fallback_used"] is True


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
    row = completed.loc[completed["sample_id"] == "s1"].iloc[0]
    for field in REVIEW_FIELDS:
        assert field in completed.columns
    for field in ["sample_id", "timestamp", "candidate_type", "confidence_score", "review_updated_at_utc"]:
        assert field in completed.columns
    assert row["review_updated_at_utc"]


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
        assert "timestamp=" in str(fig.data[0].hovertemplate)
        assert fig.layout.xaxis.tickangle == 0


def test_build_sample_marker_config_wick_sensitive():
    cfg = build_sample_marker_config("lower_wick_rejection_candidate")
    assert cfg["mode"] == "annotation_only"
    assert cfg["offset_x"] == 0.0
    assert cfg["show_symbol"] is True


def test_build_sample_marker_config_default_offset():
    cfg = build_sample_marker_config("short_trend_up_candidate")
    assert cfg["mode"] == "offset_line_with_arrow"
    assert abs(float(cfg["offset_x"]) - 0.35) < 1e-9
    assert cfg["show_symbol"] is True


def test_compute_sample_marker_y_above_sample_high():
    y = compute_sample_marker_y(sample_high=1.1050, visible_high=1.1060, visible_low=1.1000, offset_ratio=0.04)
    assert y > 1.1050
    assert y <= 1.1060 + ((1.1060 - 1.1000) * 0.12)


def test_compute_sample_marker_y_near_top_clamped():
    y = compute_sample_marker_y(sample_high=1.1060, visible_high=1.1060, visible_low=1.1000, offset_ratio=0.10)
    assert y <= 1.1060 + ((1.1060 - 1.1000) * 0.12)


def test_compute_sample_guide_line_x_default_left():
    guide = compute_sample_guide_line_x(72.0, direction="left", offset=0.45, min_x=0.0, max_x=120.0)
    assert abs(guide["guide_line_x"] - 71.55) < 1e-9
    assert guide["side"] == "left"
    assert abs(guide["offset"] - 0.45) < 1e-9


def test_compute_sample_guide_line_x_left_boundary_switch_to_right():
    guide = compute_sample_guide_line_x(0.2, direction="left", offset=0.45, min_x=0.0, max_x=120.0)
    assert guide["guide_line_x"] > 0.2
    assert guide["side"] == "right"


def test_create_candlestick_figure_marker_is_offset_for_normal_type(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    sample_timestamp = clean_view.iloc[20]["timestamp"]
    window = extract_chart_window(clean_view, sample_timestamp, lookback=10, forward=5)
    fig = create_candlestick_figure(
        window,
        sample_timestamp,
        sample_id="s1",
        candidate_type="short_trend_up_candidate",
    )
    if fig is None:
        return
    sample_idx = int(window.index[window["timestamp"] == sample_timestamp][0]) - int(window.index[0])
    sample_x = sample_idx
    xs = [float(s.x0) for s in fig.layout.shapes] if fig.layout.shapes else []
    assert any(abs(x - sample_x) > 0.2 for x in xs)
    assert all(abs(x - sample_x) > 1e-9 for x in xs)
    sample_marker_traces = [t for t in fig.data if getattr(t, "name", "") == "Sample marker"]
    assert len(sample_marker_traces) == 1
    assert str(fig.layout.annotations[0].text) == "Sample"
    assert fig.layout.meta is not None
    assert "sample_guide_line_x" in fig.layout.meta
    assert float(fig.layout.meta["sample_guide_line_x"]) != float(fig.layout.meta["sample_display_x"])


def test_create_candlestick_figure_marker_no_full_height_line_for_wick_sensitive(clean_view_fixture):
    clean_view = load_clean_view(clean_view_fixture)
    sample_timestamp = clean_view.iloc[22]["timestamp"]
    window = extract_chart_window(clean_view, sample_timestamp, lookback=10, forward=5)
    fig = create_candlestick_figure(
        window,
        sample_timestamp,
        sample_id="s2",
        candidate_type="lower_wick_rejection_candidate",
    )
    if fig is None:
        return
    # No sample line shape should be drawn for wick-sensitive markers (only optional gap markers).
    sample_ts = str(sample_timestamp)
    sample_shapes = []
    guide_shapes = []
    for s in list(fig.layout.shapes):
        s_json = s.to_plotly_json()
        if s_json.get("type") == "line" and s_json.get("line", {}).get("dash") == "dash":
            sample_shapes.append(s_json)
        if s_json.get("type") == "line" and s_json.get("line", {}).get("dash") == "dot":
            guide_shapes.append(s_json)
    assert len(sample_shapes) == 0
    assert len(guide_shapes) >= 1
    assert len(fig.layout.annotations) >= 1
    assert str(fig.layout.annotations[0].text) == "Sample"
    sample_marker_traces = [t for t in fig.data if getattr(t, "name", "") == "Sample marker"]
    assert len(sample_marker_traces) == 1
    assert fig.layout.meta is not None
    assert fig.layout.meta.get("sample_marker_mode") == "annotation_only"


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


def test_default_review_values_match_reset_contract():
    defaults = default_review_values()
    assert defaults["human_pattern_label"] == "unclear"
    assert defaults["market_context"] == "unclear"
    assert defaults["direction_context"] == "unclear"
    assert defaults["structure_quality"] == 3
    assert defaults["follow_through_quality"] == 3
    assert defaults["review_confidence"] == 3
    assert defaults["review_notes"] == ""
    assert defaults["review_status"] == "pending"


def test_build_review_update_row_fills_required_fields():
    row = build_review_update_row({"review_notes": float("nan"), "review_status": "reviewed"})
    for field in [
        "human_pattern_label",
        "market_context",
        "direction_context",
        "structure_quality",
        "follow_through_quality",
        "review_confidence",
        "review_notes",
        "review_status",
    ]:
        assert field in row
    assert row["review_notes"] == ""
    assert row["review_status"] == "reviewed"


def test_save_or_update_completed_review_updates_without_duplicate(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    save_or_update_completed_review(
        batch_df=batch_df,
        sample_id="s1",
        review_values={"human_pattern_label": "weak_pattern", "review_notes": "first"},
        output_path=output_path,
    )
    save_or_update_completed_review(
        batch_df=batch_df,
        sample_id="s1",
        review_values={"human_pattern_label": "valid_pattern", "review_notes": "second", "review_status": "reviewed"},
        output_path=output_path,
    )
    completed = pd.read_csv(output_path)
    assert completed["sample_id"].value_counts().get("s1", 0) == 1
    row = completed.loc[completed["sample_id"] == "s1"].iloc[0]
    assert row["human_pattern_label"] == "valid_pattern"
    assert row["review_notes"] == "second"


def test_save_or_update_returns_insert_then_update(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    first = save_or_update_completed_review(
        batch_df=batch_df,
        sample_id="s2",
        review_values={"review_notes": "a"},
        output_path=output_path,
    )
    second = save_or_update_completed_review(
        batch_df=batch_df,
        sample_id="s2",
        review_values={"review_notes": "b"},
        output_path=output_path,
    )
    assert first["action_result"] == "insert"
    assert second["action_result"] == "update"


def test_save_or_update_persists_identity_and_update_timestamp(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    output_path = temp_dir / "completed.csv"
    save_or_update_completed_review(
        batch_df=batch_df,
        sample_id="s3",
        review_values={"review_notes": "identity-check", "review_status": "reviewed"},
        output_path=output_path,
    )
    completed = pd.read_csv(output_path)
    row = completed.loc[completed["sample_id"] == "s3"].iloc[0]
    assert row["candidate_type"] == "test"
    assert float(row["confidence_score"]) == 0.9
    assert row["review_updated_at_utc"]


def test_append_review_event_jsonl_writes_required_fields(temp_dir):
    jsonl_path = temp_dir / "events.jsonl"
    completed_csv_path = temp_dir / "completed.csv"
    review_values = {
        "human_pattern_label": "weak_pattern",
        "market_context": "range",
        "direction_context": "neutral",
        "structure_quality": 2,
        "follow_through_quality": 2,
        "review_confidence": 3,
        "review_notes": "note",
        "review_status": "reviewed",
    }
    append_review_event_jsonl(
        jsonl_path=jsonl_path,
        sample_id="s9",
        review_values=review_values,
        action_type="save",
        completed_csv_path=completed_csv_path,
        batch_path="tmp/eurusd/batch.csv",
    )
    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["sample_id"] == "s9"
    assert record["action_type"] == "save"
    assert "event_timestamp_utc" in record
    assert "schema_version" in record
    assert record["completed_csv_path"] == str(completed_csv_path)
    assert record["source_batch_path"] == "tmp/eurusd/batch.csv"
    assert record["review"]["review_notes"] == "note"


def test_append_review_event_jsonl_is_append_friendly(temp_dir):
    jsonl_path = temp_dir / "events.jsonl"
    completed_csv_path = temp_dir / "completed.csv"
    append_review_event_jsonl(
        jsonl_path=jsonl_path,
        sample_id="s1",
        review_values={"review_status": "pending"},
        action_type="save",
        completed_csv_path=completed_csv_path,
        batch_path="tmp/eurusd/batch.csv",
    )
    append_review_event_jsonl(
        jsonl_path=jsonl_path,
        sample_id="s1",
        review_values={"review_status": "reviewed"},
        action_type="save_and_next",
        completed_csv_path=completed_csv_path,
        batch_path="tmp/eurusd/batch.csv",
    )
    lines = [line for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["action_type"] == "save"
    assert second["action_type"] == "save_and_next"


def test_save_review_action_writes_csv_and_jsonl(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    completed_path = temp_dir / "completed.csv"
    events_path = temp_dir / "events.jsonl"
    action = save_review_action(
        batch_df=batch_df,
        sample_id="s1",
        review_values={"review_notes": "ok", "review_status": "reviewed"},
        completed_csv_path=completed_path,
        audit_jsonl_path=events_path,
        action_type="save",
        source_batch_path="tmp/eurusd/batch.csv",
    )
    assert action["ok"] is True
    assert action["csv_saved"] is True
    assert action["jsonl_appended"] is True
    assert action["warning"] is None
    completed = pd.read_csv(completed_path)
    assert completed["sample_id"].value_counts().get("s1", 0) == 1
    lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1


def test_save_review_action_duplicate_safe_with_two_events(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    completed_path = temp_dir / "completed.csv"
    events_path = temp_dir / "events.jsonl"
    save_review_action(
        batch_df=batch_df,
        sample_id="s2",
        review_values={"review_notes": "one", "review_status": "pending"},
        completed_csv_path=completed_path,
        audit_jsonl_path=events_path,
        action_type="save",
        source_batch_path="tmp/eurusd/batch.csv",
    )
    save_review_action(
        batch_df=batch_df,
        sample_id="s2",
        review_values={"review_notes": "two", "review_status": "reviewed"},
        completed_csv_path=completed_path,
        audit_jsonl_path=events_path,
        action_type="save_and_next",
        source_batch_path="tmp/eurusd/batch.csv",
    )
    completed = pd.read_csv(completed_path)
    row = completed.loc[completed["sample_id"] == "s2"].iloc[0]
    assert completed["sample_id"].value_counts().get("s2", 0) == 1
    assert row["review_notes"] == "two"
    lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2


def test_save_review_action_csv_success_jsonl_warning(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    completed_path = temp_dir / "completed.csv"
    jsonl_dir = temp_dir / "events_dir"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    action = save_review_action(
        batch_df=batch_df,
        sample_id="s3",
        review_values={"review_notes": "warn-case", "review_status": "reviewed"},
        completed_csv_path=completed_path,
        audit_jsonl_path=jsonl_dir,
        action_type="save_and_next",
        source_batch_path="tmp/eurusd/batch.csv",
    )
    assert action["ok"] is True
    assert action["csv_saved"] is True
    assert action["jsonl_appended"] is False
    assert action["warning"] is not None
    completed = pd.read_csv(completed_path)
    assert completed["sample_id"].value_counts().get("s3", 0) == 1


def test_app_does_not_use_top_level_stale_persist_review_symbol():
    app_path = Path("cajas/apps/eurusd_pattern_review_app.py")
    text = app_path.read_text(encoding="utf-8")
    assert "\nif __name__ == \"__main__\":\n    main()\n    def persist_review" not in text


def test_build_persistence_status_message_contains_expected_fields():
    msg = build_persistence_status_message(
        sample_id="s1",
        action_result="update",
        action_type="save_and_next",
        completed_csv_path="tmp/eurusd/completed.csv",
        jsonl_path="tmp/eurusd/events.jsonl",
        jsonl_status="written",
        sample_index=4,
    )
    assert "sample_id=s1" in msg
    assert "save_and_next" in msg
    assert "csv=tmp/eurusd/completed.csv" in msg
    assert "jsonl=tmp/eurusd/events.jsonl [written]" in msg
    assert "sample_index=4" in msg


def test_sample_index_helpers():
    assert clamp_sample_index(0, 5) == 0
    assert clamp_sample_index(-2, 5) == 0
    assert clamp_sample_index(99, 5) == 4
    assert next_sample_index(0, 5) == 1
    assert next_sample_index(4, 5) == 4
    assert next_sample_index(8, 5) == 4
    assert previous_sample_index(5, 10) == 4
    assert previous_sample_index(0, 10) == 0


def test_should_advance_after_save_semantics():
    assert should_advance_after_save({"ok": True, "csv_saved": True, "jsonl_appended": True}) is True
    assert should_advance_after_save({"ok": True, "csv_saved": True, "jsonl_appended": False, "warning": "x"}) is True
    assert should_advance_after_save({"ok": False, "csv_saved": False}) is False


def test_app_uses_decoupled_sample_index_keys():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert 'key="sample_idx"' not in app_source
    assert "current_global_sample_idx" in app_source
    assert "sample_number_input" in app_source
    assert "pending_global_sample_idx" in app_source
    assert "Previous Sample" in app_source
    assert "Next Sample" in app_source
    assert "Last Save Details" in app_source
    assert "Reset Form" not in app_source


def test_compact_save_feedback_message_does_not_include_paths():
    save_msg = build_compact_save_feedback_message(sample_id="eurusd15m_000030", action_type="save")
    assert save_msg == "Saved eurusd15m_000030"
    assert "csv=" not in save_msg
    assert "jsonl=" not in save_msg

    save_next_msg = build_compact_save_feedback_message(
        sample_id="eurusd15m_000030",
        action_type="save_and_next",
        moved_to_human_index=31,
        total_count=500,
    )
    assert save_next_msg == "Saved eurusd15m_000030 -> moved to sample 31/500"
    assert "csv=" not in save_next_msg
    assert "jsonl=" not in save_next_msg


def test_compact_chart_status_line_is_single_line():
    base = "Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60"
    line = build_compact_chart_status_line(
        base,
        {"display_axis": "real_time_axis", "time_gap_count": 0, "gap_markers": 0, "largest_gap_hours": 0.0},
    )
    assert "\n" not in line
    assert "display_axis=real_time_axis" in line
    assert "time_gap_count=0" in line


def test_app_imports_default_review_values_when_used():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert "default_review_values()" in app_source
    assert "default_review_values," in app_source


def test_detect_time_axis_gaps_no_gap():
    timestamps = pd.date_range("2020-01-03 00:00:00", periods=10, freq="15min")
    gaps = detect_time_axis_gaps(list(timestamps))
    assert gaps == []


def test_detect_time_axis_gaps_weekend():
    timestamps = [
        pd.Timestamp("2020-01-03 21:45:00+00:00"),
        pd.Timestamp("2020-01-03 22:00:00+00:00"),
        pd.Timestamp("2020-01-05 22:15:00+00:00"),
    ]
    gaps = detect_time_axis_gaps(timestamps)
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap["classification"] == "weekend_or_market_closed_gap"
    assert gap["gap_hours"] > 24


def test_build_compressed_gap_axis_with_marker():
    timestamps = [
        pd.Timestamp("2020-01-03 22:00:00+00:00"),
        pd.Timestamp("2020-01-06 00:00:00+00:00"),
        pd.Timestamp("2020-01-06 00:15:00+00:00"),
    ]
    axis = build_compressed_gap_axis(timestamps)
    assert axis["display_x"] == [0, 1, 2]
    assert axis["display_axis"] == "compressed_gap_axis"
    assert len(axis["gap_markers"]) == 1
    assert axis["gap_markers"][0]["display_x"] == 0.5
    assert all("\n" not in t for t in axis["ticktext"])
    assert all(len(t) <= 11 for t in axis["ticktext"])


def test_format_compact_tick_label():
    label = format_compact_tick_label("2020-01-02T03:15:00+00:00")
    assert label == "01-02 03:15"


def test_summarize_compressed_gap_axis():
    axis = {
        "display_axis": "compressed_gap_axis",
        "raw_time_axis_preserved_in_hover": True,
        "gaps": [{"gap_hours": 48.0}],
        "gap_markers": [{"display_x": 0.5}],
    }
    summary = summarize_compressed_gap_axis(axis)
    assert summary["display_axis"] == "compressed_gap_axis"
    assert summary["raw_time_axis_preserved_in_hover"] is True
    assert summary["time_gap_count"] == 1
    assert summary["largest_gap_hours"] == 48.0
    assert summary["gap_markers"] == 1


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


def test_build_compact_chart_diagnostic_summary_contains_required_fields():
    diag = {
        "chart_window_row_count": 91,
        "exact_timestamp_match_found": True,
        "nearest_fallback_used": False,
        "target_index_in_window": 60,
    }
    summary = build_compact_chart_diagnostic_summary(diag, trace_count=1)
    assert "Window 91 bars" in summary
    assert "traces 1" in summary
    assert "exact match ✓" in summary
    assert "fallback ✗" in summary
    assert "target index 60" in summary


def test_get_chart_height_defaults():
    assert get_chart_height(compact_mode=True, compact_height=420) == 420
    assert get_chart_height(compact_mode=False, compact_height=420) == 600


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


def test_pending_toast_enqueue_and_consume_once():
    state = {}
    enqueue_pending_toast(state, "Saved s1", kind="success", icon="✅")
    assert state["pending_toast_message"] == "Saved s1"
    assert state["pending_toast_kind"] == "success"
    assert state["pending_toast_icon"] == "✅"

    calls = []

    class FakeSidebar:
        def warning(self, msg):
            calls.append(("warning", msg))

        def success(self, msg):
            calls.append(("success", msg))

    class FakeStreamlit:
        def __init__(self):
            self.sidebar = FakeSidebar()

        def toast(self, msg, icon=None):
            calls.append(("toast", msg, icon))

    fake_st = FakeStreamlit()
    consume_pending_toast_once(fake_st, state)
    assert calls == [("toast", "Saved s1", "✅")]
    assert "pending_toast_message" not in state
    assert "pending_toast_kind" not in state
    assert "pending_toast_icon" not in state

    consume_pending_toast_once(fake_st, state)
    assert calls == [("toast", "Saved s1", "✅")]


def test_last_save_details_persists_after_toast_consume():
    state = {
        "last_save_details": {"sample_id": "s1", "action_type": "save"},
    }
    enqueue_pending_toast(state, "Saved s1")

    class FakeSidebar:
        def warning(self, _msg):
            raise AssertionError("warning should not be called in this test")

        def success(self, _msg):
            raise AssertionError("sidebar.success should not be called in this test")

    class FakeStreamlit:
        def __init__(self):
            self.sidebar = FakeSidebar()

        def toast(self, _msg, icon=None):
            assert icon == "✅"

    consume_pending_toast_once(FakeStreamlit(), state)
    assert state["last_save_details"] == {"sample_id": "s1", "action_type": "save"}
    assert "pending_toast_message" not in state


def test_pending_navigation_can_coexist_with_pending_toast():
    state = {"pending_global_sample_idx": 12}
    enqueue_pending_toast(state, "Saved s2 -> moved to sample 13/100")

    class FakeSidebar:
        def warning(self, _msg):
            raise AssertionError("warning should not be called in this test")

        def success(self, _msg):
            raise AssertionError("sidebar.success should not be called in this test")

    class FakeStreamlit:
        def __init__(self):
            self.sidebar = FakeSidebar()

        def toast(self, _msg, icon=None):
            assert icon == "✅"

    consume_pending_toast_once(FakeStreamlit(), state)
    assert state["pending_global_sample_idx"] == 12
    assert "pending_toast_message" not in state


def test_apply_pending_global_sample_index_updates_current_and_input_and_clears_pending():
    state = {
        "pending_global_sample_idx": 33,
        "current_global_sample_idx": 0,
        "sample_number_input": 1,
    }
    apply_pending_global_sample_index(
        state,
        pending_key="pending_global_sample_idx",
        current_key="current_global_sample_idx",
        input_key="sample_number_input",
        batch_count=100,
    )
    assert state["current_global_sample_idx"] == 33
    assert state["sample_number_input"] == 34
    assert "pending_global_sample_idx" not in state


def test_apply_pending_global_sample_index_clamps_out_of_range():
    state = {
        "pending_global_sample_idx": 999,
        "current_global_sample_idx": 0,
        "sample_number_input": 1,
    }
    apply_pending_global_sample_index(
        state,
        pending_key="pending_global_sample_idx",
        current_key="current_global_sample_idx",
        input_key="sample_number_input",
        batch_count=10,
    )
    assert state["current_global_sample_idx"] == 9
    assert state["sample_number_input"] == 10


def test_app_source_uses_pending_toast_consume_pattern():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert "pending_toast_message" in app_source
    assert "consume_pending_toast_once(st, st.session_state)" in app_source
    assert 'st.toast(st.session_state["last_action_msg"]' not in app_source
    assert "last_action_msg" not in app_source


def test_global_sample_number_conversion_and_clamp():
    assert sample_number_to_global_index(1, 100) == 0
    assert sample_number_to_global_index(34, 100) == 33
    assert sample_number_to_global_index(100, 100) == 99
    assert sample_number_to_global_index(0, 100) == 0
    assert sample_number_to_global_index(999, 100) == 99
    assert global_index_to_sample_number(0) == 1
    assert global_index_to_sample_number(33) == 34
    assert global_index_to_sample_number(99) == 100


def test_direct_jump_resolution_uses_global_batch_order_ignoring_filters():
    batch = pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3", "s4"],
            "candidate_type": ["A", "A", "B", "A"],
            "review_status": ["pending", "reviewed", "pending", "pending"],
        }
    )
    filtered = batch[(batch["candidate_type"] == "A") & (batch["review_status"] == "pending")]
    assert list(filtered["sample_id"]) == ["s1", "s4"]
    global_idx = sample_number_to_global_index(3, len(batch))
    sample = batch.iloc[global_idx]
    assert sample["sample_id"] == "s3"


def test_app_source_uses_global_sample_number_wording_and_keys():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert "Sample Number" in app_source
    assert "Go to Sample" in app_source
    assert "Global position in full review batch; ignores filters." in app_source
    assert "Filters are active; direct Sample Number jump uses full batch order." in app_source
    assert "current_global_sample_idx" in app_source
    assert "pending_global_sample_idx" in app_source
    assert "sample_number_input" in app_source


def test_app_source_removes_redundant_main_sample_header_and_compacts_title():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert "#### EURUSD 15m Review · Sample" in app_source
    assert 'f"### EURUSD 15m Review · Sample' not in app_source
    assert "st.subheader(f\"Sample {sample['sample_id']}\")" not in app_source
    assert "st.header(f\"Sample: {sample['sample_id']}\")" not in app_source


def test_app_source_moves_long_metadata_to_sample_details_expander():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert 'with st.expander("Sample Details", expanded=False):' in app_source
    assert "st.caption(meta_line)" in app_source
    assert 'st.subheader("Candlestick Chart")' not in app_source
    assert 'st.markdown("##### Chart")' in app_source


def test_app_source_injects_compact_css_and_hides_streamlit_chrome():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert "def inject_compact_review_css" in app_source
    assert '[data-testid="stHeader"] { display: none; }' in app_source
    assert '[data-testid="stToolbar"] { display: none; }' in app_source
    assert '[data-testid="stDecoration"] { display: none; }' in app_source
    assert "inject_compact_review_css(st)" in app_source
    assert "EURUSD 15m Review · Sample" in app_source


def test_app_source_keeps_sidebar_and_toast_behavior():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert "st.sidebar.header(\"Configuration\")" in app_source
    assert "consume_pending_toast_once(st, st.session_state)" in app_source
    assert "[data-testid=\"stSidebar\"]" not in app_source


def test_app_source_uses_compact_left_form_right_actions_layout():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert 'left_col, right_col = st.columns([3.2, 1.4], gap="large")' in app_source
    assert 'st.markdown("#### Review Labels")' in app_source
    assert 'st.markdown("#### Bad Sample Workflow")' in app_source
    assert 'st.markdown("#### Actions")' in app_source


def test_app_source_actions_kept_in_right_column():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    assert 'if st.button("Save", use_container_width=True):' in app_source
    assert 'if st.button("Save and Next", use_container_width=True):' in app_source
    assert 'if st.button("Previous Sample", disabled=sample_idx <= 0, use_container_width=True):' in app_source
    assert 'if st.button("Next Sample", disabled=sample_idx >= row_count - 1, use_container_width=True):' in app_source
    assert 'if st.button("Reject Sample", disabled=not confirm_reject, use_container_width=True):' in app_source


def test_app_source_resolves_sample_before_sidebar_sample_id_caption():
    app_source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text(encoding="utf-8")
    sample_assign = app_source.find("sample = batch.iloc[sample_idx]")
    sidebar_caption = app_source.find("st.sidebar.caption(f\"sample_id={sample['sample_id']} | global_index={sample_idx}\")")
    assert sample_assign != -1
    assert sidebar_caption != -1
    assert sample_assign < sidebar_caption


def test_reject_sample_action_and_navigation(batch_fixture, temp_dir):
    batch_df = load_review_batch(batch_fixture)
    rejected_csv = temp_dir / "rejected.csv"
    rejected_events = temp_dir / "rejected_events.jsonl"

    action = reject_sample_action(
        batch_df=batch_df,
        sample_id="s2",
        reason="bad_context",
        notes="bad sample",
        rejected_csv_path=rejected_csv,
        rejected_events_jsonl_path=rejected_events,
        review_batch_id="batch_001",
        source_batch_csv="batch.csv",
    )
    assert action["ok"] is True
    assert rejected_csv.exists()
    assert rejected_events.exists()

    rej_df = load_rejected_samples(rejected_csv)
    rej_ids = get_rejected_sample_ids(rej_df)
    assert "s2" in rej_ids

    sample_ids = ["s1", "s2", "s3"]
    assert next_non_rejected_sample_index(0, 3, rej_ids, sample_ids) == 2
    assert previous_non_rejected_sample_index(2, 3, rej_ids, sample_ids) == 0
