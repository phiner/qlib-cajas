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
)
from cajas.apps.eurusd_pattern_review_app import render_plotly_chart, build_compact_chart_status_line


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
        "direction_context": "sideways",
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
    assert "current_sample_idx" in app_source
    assert "sample_idx_widget" in app_source
    assert "pending_sample_idx" in app_source
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
