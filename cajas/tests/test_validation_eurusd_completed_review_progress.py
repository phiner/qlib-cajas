"""Tests for EURUSD completed review progress report."""

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_completed_review_progress import build_completed_review_progress_report


def _schema(path: Path):
    path.write_text(
        json.dumps(
            {
                "allowed_values": {
                    "market_context": ["uptrend", "downtrend", "range", "compression", "expansion", "transition", "choppy", "unclear", "not_reviewed"],
                    "trend_direction": ["up", "down", "sideways", "mixed", "unclear", "not_reviewed"],
                    "trend_stage": ["early_trend", "mid_trend", "late_trend", "trend_exhaustion", "pullback", "reversal_attempt", "consolidation_after_impulse", "range_transition", "unclear", "not_reviewed"],
                    "volatility_state": ["low_volatility", "normal_volatility", "high_volatility", "compression", "expansion", "post_expansion", "unclear", "not_reviewed"],
                    "recent_move_context": ["sharp_rise", "sharp_drop", "rise_then_pullback", "drop_then_rebound", "spike_up_reversal", "spike_down_reversal", "sharp_rise_then_consolidation", "sharp_drop_then_consolidation", "range_breakout_attempt", "range_breakdown_attempt", "sweep_high_then_reclaim", "sweep_low_then_reclaim", "unclear", "not_reviewed"],
                    "session_context": ["asia", "london", "new_york", "overlap", "rollover", "normal", "unclear", "not_reviewed"],
                    "structure_location": ["prior_high", "prior_low", "range_high", "range_low", "range_middle", "breakdown_area", "breakout_area", "pullback_area", "retest_area", "support_area", "resistance_area", "liquidity_sweep_area", "middle_of_range", "trend_continuation_area", "trend_exhaustion_area", "middle_of_nowhere", "unclear", "not_reviewed"],
                    "level_quality": ["strong", "medium", "weak", "none", "unclear", "not_reviewed"],
                    "local_behavior": ["lower_wick_rejection", "upper_wick_rejection", "doji", "small_body_indecision", "strong_bull_body", "strong_bear_body", "strong_body_breakout", "failed_breakout_reclaim", "compression_cluster", "expansion_bar", "trend_push", "reclaim", "unclear", "not_reviewed"],
                    "confirmation_result": ["confirmed", "failed", "no_follow_through", "partial_follow_through", "delayed_follow_through", "unclear", "not_reviewed"],
                    "review_outcome": ["valid_pattern", "weak_pattern", "false_positive", "not_enough_context", "unclear", "not_reviewed"],
                    "pattern_quality": ["strong", "medium", "weak", "invalid", "unclear", "not_reviewed"],
                    "false_positive_reason": ["none", "no_structure_level", "low_volatility_noise", "trend_middle_noise", "overlapping_labels", "insufficient_context", "bad_candidate_anchor", "level_too_local", "session_noise", "spread_or_data_noise", "news_spike_like", "middle_of_nowhere", "weak_follow_through", "other", "not_reviewed"],
                    "review_confidence": ["high", "medium", "low", "unclear", "not_reviewed"],
                    "primary_candidate_family": ["market_context", "volatility_state", "candle_observation", "structure_event", "confirmation_event", "mixed_overlap", "unclear", "not_reviewed"],
                    "secondary_candidate_family": ["market_context", "volatility_state", "candle_observation", "structure_event", "confirmation_event", "mixed_overlap", "none", "unclear", "not_reviewed"],
                },
                "legacy_allowed_values": {},
            }
        ),
        encoding="utf-8",
    )


def _batch(path: Path):
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00", "2020-01-02T00:00:00+00:00"],
            "candidate_type": ["a", "b", "a"],
        }
    ).to_csv(path, index=False)


def _completed(path: Path):
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "timestamp": ["2020-01-01T00:00:00+00:00", "2020-01-01T00:15:00+00:00", "2020-01-02T00:00:00+00:00"],
            "candidate_type": ["a", "b", "a"],
            "market_context": ["uptrend", "not_reviewed", "not_reviewed"],
            "trend_direction": ["up", "not_reviewed", "not_reviewed"],
            "trend_stage": ["mid_trend", "not_reviewed", "not_reviewed"],
            "volatility_state": ["normal_volatility", "not_reviewed", "not_reviewed"],
            "recent_move_context": ["spike_up_reversal", "not_reviewed", "not_reviewed"],
            "session_context": ["london", "not_reviewed", "not_reviewed"],
            "structure_location": ["prior_high", "not_reviewed", "not_reviewed"],
            "level_quality": ["medium", "not_reviewed", "not_reviewed"],
            "local_behavior": ["upper_wick_rejection", "not_reviewed", "not_reviewed"],
            "confirmation_result": ["confirmed", "not_reviewed", "not_reviewed"],
            "review_outcome": ["valid_pattern", "not_reviewed", "not_reviewed"],
            "pattern_quality": ["strong", "not_reviewed", "not_reviewed"],
            "false_positive_reason": ["none", "not_reviewed", "not_reviewed"],
            "review_confidence": ["high", "not_reviewed", "not_reviewed"],
            "primary_candidate_family": ["structure_event", "not_reviewed", "not_reviewed"],
            "secondary_candidate_family": ["none", "not_reviewed", "not_reviewed"],
            "review_notes": ["good wick", "", ""],
            "review_updated_at_utc": ["2026-05-04T15:00:00Z", "", ""],
        }
    ).to_csv(path, index=False)


def _events(path: Path):
    rows = [
        {
            "sample_id": "s1",
            "review": {
                "market_context": "uptrend",
                "trend_direction": "up",
                "trend_stage": "mid_trend",
                "volatility_state": "normal_volatility",
                "recent_move_context": "spike_up_reversal",
                "session_context": "london",
                "structure_location": "prior_high",
                "level_quality": "medium",
                "local_behavior": "upper_wick_rejection",
                "confirmation_result": "confirmed",
                "review_outcome": "valid_pattern",
                "pattern_quality": "strong",
                "false_positive_reason": "none",
                "review_confidence": "high",
                "primary_candidate_family": "structure_event",
                "secondary_candidate_family": "none",
                "review_notes": "good wick",
            },
        }
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


def test_progress_blocks_on_legacy_shape(tmp_path: Path):
    batch = tmp_path / "batch.csv"
    comp = tmp_path / "completed.csv"
    events = tmp_path / "events.jsonl"
    schema = tmp_path / "schema.json"
    _batch(batch)
    _schema(schema)
    pd.DataFrame(
        {
            "sample_id": ["s1"],
            "timestamp": ["2020-01-01T00:00:00+00:00"],
            "candidate_type": ["a"],
            "review_status": ["reviewed"],
            "direction_context": ["up"],
            "structure_quality": [3],
            "follow_through_quality": [3],
            "review_confidence_level": ["high"],
        }
    ).to_csv(comp, index=False)
    events.write_text("", encoding="utf-8")

    report = build_completed_review_progress_report(
        batch_csv=batch,
        completed_csv=comp,
        events_jsonl=events,
        label_schema_json=schema,
    )
    assert report["status"] == "blocked"
    assert report["csv_schema_status"] == "blocked"
    assert "market_context" in report["missing_review_fields"]
