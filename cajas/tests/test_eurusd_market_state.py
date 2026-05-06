"""Tests for deterministic EURUSD market-state prototype."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cajas.research.eurusd_market_state import (
    build_market_state_dataset,
    classify_market_state_row,
    compute_market_state_features,
)


def _synthetic_df(n: int = 220, drift: float = 0.0002, vol: float = 0.0004) -> pd.DataFrame:
    ts = pd.date_range("2025-01-01", periods=n, freq="15min", tz="UTC")
    base = 1.10
    steps = drift + np.random.default_rng(7).normal(0.0, vol, size=n)
    close = base + np.cumsum(steps)
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.0003
    low = np.minimum(open_, close) - 0.0003
    return pd.DataFrame({"timestamp": ts, "open": open_, "high": high, "low": low, "close": close})


def _base_row() -> dict:
    return {
        "return_8": 0.0004,
        "return_24": 0.0004,
        "return_128": 0.0002,
        "range_position_128": 0.5,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": True,
        "volatility_state_3": "compressed",
    }


def test_feature_columns_exist() -> None:
    out = compute_market_state_features(_synthetic_df())
    for col in [
        "return_3", "return_8", "return_24", "return_128",
        "slope_3", "slope_8", "slope_24", "slope_128",
        "range_position_3", "range_position_8", "range_position_24", "range_position_128",
        "prev_close_1", "prev_close_2", "gap_count_128",
    ]:
        assert col in out.columns


def test_lower_sweep_reclaim_detection() -> None:
    row = {
        **_base_row(),
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
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "lower_sweep_reclaim"
    assert out["micro_sweep_detected_3"] is True


def test_upper_sweep_reject_detection() -> None:
    row = {
        **_base_row(),
        "open": 1.0028,
        "close": 1.0012,
        "high": 1.0060,
        "low": 1.0008,
        "prev_open_1": 1.0020,
        "prev_close_1": 1.0025,
        "prev_high_1": 1.0042,
        "prev_low_1": 1.0009,
        "prev_open_2": 1.0010,
        "prev_close_2": 1.0015,
        "prev_high_2": 1.0040,
        "prev_low_2": 1.0007,
        "body_ratio_latest": 0.35,
        "upper_wick_ratio_latest": 0.55,
        "lower_wick_ratio_latest": 0.1,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "upper_sweep_reject"
    assert out["micro_rejection_detected_3"] is True


def test_three_bar_reversal_up_detection() -> None:
    row = {
        **_base_row(),
        "return_128": 0.02,
        "return_24": -0.004,
        "open": 0.998,
        "close": 1.006,
        "high": 1.0063,
        "low": 0.9975,
        "prev_open_1": 1.003,
        "prev_close_1": 1.000,
        "prev_high_1": 1.002,
        "prev_low_1": 0.999,
        "prev_open_2": 1.006,
        "prev_close_2": 1.003,
        "prev_high_2": 1.0062,
        "prev_low_2": 1.002,
        "body_ratio_latest": 0.62,
        "upper_wick_ratio_latest": 0.05,
        "lower_wick_ratio_latest": 0.1,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "three_bar_reversal_up"
    assert out["micro_reversal_detected_3"] is True


def test_three_bar_reversal_down_detection() -> None:
    row = {
        **_base_row(),
        "return_128": -0.02,
        "return_24": 0.004,
        "open": 1.006,
        "close": 0.998,
        "high": 1.0065,
        "low": 0.9978,
        "prev_open_1": 1.002,
        "prev_close_1": 1.005,
        "prev_high_1": 1.0062,
        "prev_low_1": 1.000,
        "prev_open_2": 0.999,
        "prev_close_2": 1.002,
        "prev_high_2": 1.0022,
        "prev_low_2": 0.9988,
        "body_ratio_latest": 0.62,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.05,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "three_bar_reversal_down"


def test_micro_noise_on_contradictory_three_bars() -> None:
    row = {
        **_base_row(),
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
        "body_ratio_latest": 0.22,
        "upper_wick_ratio_latest": 0.22,
        "lower_wick_ratio_latest": 0.2,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] in {"micro_noise", "micro_pause", "micro_compression"}


def test_three_bar_not_slope_only() -> None:
    row = {
        **_base_row(),
        "return_3": -0.002,
        "open": 0.998,
        "close": 1.006,
        "high": 1.0063,
        "low": 0.9975,
        "prev_open_1": 1.003,
        "prev_close_1": 1.000,
        "prev_high_1": 1.002,
        "prev_low_1": 0.999,
        "prev_open_2": 1.006,
        "prev_close_2": 1.003,
        "prev_high_2": 1.0062,
        "prev_low_2": 1.002,
        "body_ratio_latest": 0.62,
        "upper_wick_ratio_latest": 0.05,
        "lower_wick_ratio_latest": 0.1,
    }
    out = classify_market_state_row(row)
    assert out["micro_pattern_event_3"] == "three_bar_reversal_up"


def test_combiner_long_uptrend_pullback_with_reversal_up() -> None:
    row = {
        **_base_row(),
        "return_8": 0.0015,
        "return_24": -0.0035,
        "return_128": 0.018,
        "range_position_128": 0.65,
        "open": 0.998,
        "close": 1.006,
        "high": 1.0063,
        "low": 0.9975,
        "prev_open_1": 1.003,
        "prev_close_1": 1.000,
        "prev_high_1": 1.002,
        "prev_low_1": 0.999,
        "prev_open_2": 1.006,
        "prev_close_2": 1.003,
        "prev_high_2": 1.0062,
        "prev_low_2": 1.002,
        "body_ratio_latest": 0.62,
        "upper_wick_ratio_latest": 0.05,
        "lower_wick_ratio_latest": 0.1,
    }
    out = classify_market_state_row(row)
    assert out["local_structure_state"] == "pullback_in_uptrend"


def test_combiner_long_downtrend_rebound_with_lower_sweep() -> None:
    row = {
        **_base_row(),
        "return_8": -0.0012,
        "return_24": 0.0035,
        "return_128": -0.02,
        "range_position_128": 0.35,
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
    }
    out = classify_market_state_row(row)
    assert out["local_structure_state"] == "rebound_in_downtrend"
    assert "微事件=" not in out["market_state_rationale_zh"]
    assert ";" not in out["market_state_rationale_zh"]


def test_dataset_has_required_micro_and_no_trading_fields() -> None:
    ds = build_market_state_dataset(_synthetic_df())
    for col in [
        "micro_pattern_event_3",
        "micro_pattern_direction_3",
        "micro_pattern_strength_3",
        "micro_reversal_detected_3",
        "micro_rejection_detected_3",
        "micro_sweep_detected_3",
        "short_term_state_8",
        "mid_term_state_24",
        "long_term_state_128",
        "micro_pattern_rule_version",
    ]:
        assert col in ds.columns
    for col in ["trade_signal", "entry", "exit", "order", "position_size"]:
        assert col not in ds.columns
