from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_sample_export import (
    build_market_state_sample_export,
    render_market_state_sample_export_markdown,
)


def _synthetic_market_state() -> pd.DataFrame:
    rows = []
    for i in range(20):
        rows.append(
            {
                "timestamp": f"2025-01-01T00:{i:02d}:00Z",
                "open": 1.1 + i * 0.0001,
                "high": 1.11 + i * 0.0001,
                "low": 1.09 + i * 0.0001,
                "close": 1.105 + i * 0.0001,
                "symbol": "EURUSD",
                "timeframe": "15m",
                "micro_pattern_event_3": "micro_noise" if i % 2 == 0 else "lower_sweep_reclaim",
                "micro_pattern_direction_3": "neutral",
                "micro_pattern_strength_3": "weak",
                "micro_event_reason_code": "reason_code",
                "micro_event_rationale_zh": "微观形态说明",
                "micro_pattern_rule_version": "v0",
                "short_term_state_8": "range_chop",
                "mid_term_state_24": "pullback_in_uptrend",
                "long_term_state_128": "high_level_consolidation",
                "local_structure_state": "range_chop",
                "structure_confidence": "medium",
                "short_structure_reason_code": "short_reason",
                "mid_structure_reason_code": "mid_reason",
                "long_structure_reason_code": "long_reason",
                "market_state_rationale_zh": "市场状态说明",
                "market_state_rule_version": "eurusd_market_state_rules_v0",
                "prev_open_1": 1.1,
                "prev_high_1": 1.11,
                "prev_low_1": 1.09,
                "prev_close_1": 1.1,
                "prev_open_2": 1.1,
                "prev_high_2": 1.11,
                "prev_low_2": 1.09,
                "prev_close_2": 1.1,
                "return_8": 0.01,
                "return_24": 0.02,
                "return_128": 0.03,
                "range_position_8": 0.4,
                "range_position_24": 0.5,
                "range_position_128": 0.6,
                "range_width_8": 0.01,
                "range_width_24": 0.02,
                "range_width_128": 0.03,
                "slope_8": 0.1,
                "slope_24": 0.2,
                "slope_128": 0.3,
                "normalized_slope_8": 0.11,
                "normalized_slope_24": 0.21,
                "normalized_slope_128": 0.31,
                "volatility_state_8": "normal",
                "volatility_state_24": "normal",
                "volatility_state_128": "normal",
                "gap_count_128": 0,
                "largest_gap_hours_128": 0.0,
            }
        )
    return pd.DataFrame(rows)


def test_export_builds_and_contains_required_structure(tmp_path: Path) -> None:
    market_csv = tmp_path / "market.csv"
    raw_csv = tmp_path / "raw.csv"
    output_csv = tmp_path / "samples.csv"
    output_jsonl = tmp_path / "samples.jsonl"
    trial_json = tmp_path / "trial.json"
    _synthetic_market_state().to_csv(market_csv, index=False)
    _synthetic_market_state()[["timestamp", "open", "high", "low", "close"]].to_csv(raw_csv, index=False)
    trial_json.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")

    report = build_market_state_sample_export(
        market_state_csv=market_csv,
        raw_csv=raw_csv,
        output_csv=output_csv,
        output_jsonl=output_jsonl,
        trial_approval_json=trial_json,
        max_rows=10,
    )
    assert report["report_status"] == "market_state_sample_export_ready"
    assert report["sample_row_count"] <= 10
    assert report["pattern_sample_count"] > 0
    assert report["market_state_sample_count"] > 0
    assert report["four_layers_present"] is True
    assert report["pattern_layer_present"] is True
    assert report["market_layers_present"] is True
    assert report["actual_bars_used_valid"] is True
    assert report["bars_3_ohlc_context_present"] is True
    assert report["market_layer_summaries_present"] is True
    assert report["trial_approval_status"] == "not_approved"

    rows = pd.read_csv(output_csv)
    assert set(rows["pattern_3_layer_type"].unique().tolist()) == {"pattern_event"}
    assert set(rows["market_8_layer_type"].unique().tolist()) == {"market_state"}
    assert set(rows["market_24_layer_type"].unique().tolist()) == {"market_state"}
    assert set(rows["market_128_layer_type"].unique().tolist()) == {"market_state"}
    assert bool((rows["pattern_3_actual_bars_used"] <= rows["pattern_3_max_bars"]).all())
    assert bool((rows["market_8_actual_bars_used"] <= rows["market_8_max_bars"]).all())
    assert bool((rows["market_24_actual_bars_used"] <= rows["market_24_max_bars"]).all())
    assert bool((rows["market_128_actual_bars_used"] <= rows["market_128_max_bars"]).all())
    for forbidden in ["trade_signal", "order", "position_size"]:
        assert forbidden not in rows.columns


def test_violation_blocks_report(tmp_path: Path) -> None:
    market_csv = tmp_path / "market.csv"
    raw_csv = tmp_path / "raw.csv"
    output_csv = tmp_path / "samples.csv"
    output_jsonl = tmp_path / "samples.jsonl"
    trial_json = tmp_path / "trial.json"
    _synthetic_market_state().to_csv(market_csv, index=False)
    _synthetic_market_state()[["timestamp", "open", "high", "low", "close"]].to_csv(raw_csv, index=False)
    trial_json.write_text(json.dumps({"status": "approved"}), encoding="utf-8")

    report = build_market_state_sample_export(
        market_state_csv=market_csv,
        raw_csv=raw_csv,
        output_csv=output_csv,
        output_jsonl=output_jsonl,
        trial_approval_json=trial_json,
        max_rows=8,
    )
    assert report["report_status"] == "blocked"
    assert report["trial_approval_status"] != "not_approved"


def test_markdown_mentions_fewer_bars_rule(tmp_path: Path) -> None:
    sample_csv = tmp_path / "sample.csv"
    pd.DataFrame([{"sample_id": "s1", "sample_type": "pattern_sample", "timestamp": "2025-01-01", "pattern_3_event": "micro_noise", "market_8_state": "range_chop", "market_24_state": "pullback_in_uptrend", "market_128_state": "high_level_consolidation"}]).to_csv(sample_csv, index=False)
    md = render_market_state_sample_export_markdown(
        {
            "report_status": "market_state_sample_export_ready",
            "sample_row_count": 1,
            "pattern_sample_count": 1,
            "market_state_sample_count": 0,
            "actual_bars_used_valid": True,
            "unavailable_requested_classes": [],
            "output_csv": str(sample_csv),
            "output_jsonl": "x.jsonl",
            "trial_approval_status": "not_approved",
        },
        sample_csv,
    )
    assert "may use fewer bars than max" in md
