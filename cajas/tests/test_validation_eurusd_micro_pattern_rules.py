"""Tests for external EURUSD micro-pattern rule library."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_pattern_rules import build_micro_pattern_rules_report, validate_rules_payload
from cajas.research.eurusd_market_state import classify_market_state_row


def _trial(path: Path, status: str = "not_approved") -> Path:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
    return path


def test_rules_file_loads_and_covers_required_events() -> None:
    report = build_micro_pattern_rules_report(
        Path("cajas/data_examples/eurusd_micro_pattern_rules_v0.json"),
        Path("tmp/validation-eurusd-llm-trial-approval.json"),
    )
    assert report["required_events_covered"] is True
    assert report["catch_all_rules_present"] is True


def test_invalid_rule_payload_blocks() -> None:
    payload = {"rule_version": "x", "rules": [{"pattern_id": "a"}]}
    errs = validate_rules_payload(payload)
    assert errs


def test_priority_order_prefers_high_priority_rule() -> None:
    row = {
        "open": 1.0010,
        "close": 1.0030,
        "high": 1.0035,
        "low": 0.9970,
        "prev_open_1": 1.0020,
        "prev_close_1": 1.0010,
        "prev_high_1": 1.0032,
        "prev_low_1": 0.9990,
        "prev_open_2": 1.0030,
        "prev_close_2": 1.0020,
        "prev_high_2": 1.0040,
        "prev_low_2": 0.9995,
        "body_ratio_latest": 0.5,
        "upper_wick_ratio_latest": 0.05,
        "lower_wick_ratio_latest": 0.55,
        "latest_close_position_in_candle": 0.7,
        "latest_bar_returns_inside_prior_3_range": True,
        "volatility_state_3": "compressed",
        "range_ratio_3_8": 0.2,
        "return_3": 0.0001,
        "range_width_3": 0.006,
        "return_8": 0.0,
        "return_24": 0.0,
        "return_128": 0.0,
        "range_position_128": 0.5,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": True,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "lower_sweep_reclaim"


def test_noise_only_after_higher_priority_fail() -> None:
    row = {
        "open": 1.001,
        "close": 1.0013,
        "high": 1.003,
        "low": 1.0010,
        "prev_open_1": 1.0015,
        "prev_close_1": 1.0010,
        "prev_high_1": 1.0032,
        "prev_low_1": 1.0008,
        "prev_open_2": 1.001,
        "prev_close_2": 1.0016,
        "prev_high_2": 1.0031,
        "prev_low_2": 1.0005,
        "body_ratio_latest": 0.5,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.1,
        "latest_close_position_in_candle": 0.55,
        "latest_bar_returns_inside_prior_3_range": False,
        "volatility_state_3": "normal",
        "range_ratio_3_8": 0.8,
        "return_3": 0.001,
        "range_width_3": 0.002,
        "return_8": 0.0,
        "return_24": 0.0,
        "return_128": 0.0,
        "range_position_128": 0.5,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": False,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "micro_noise"
