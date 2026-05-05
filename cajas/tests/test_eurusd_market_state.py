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


def test_feature_columns_exist() -> None:
    out = compute_market_state_features(_synthetic_df())
    for col in [
        "return_3", "return_8", "return_24", "return_128",
        "slope_3", "slope_8", "slope_24", "slope_128",
        "range_position_3", "range_position_8", "range_position_24", "range_position_128",
        "three_bar_reversal_score", "higher_high_count_24", "gap_count_128",
    ]:
        assert col in out.columns


def test_range_positions_bounded_when_computable() -> None:
    out = compute_market_state_features(_synthetic_df())
    for col in ["range_position_3", "range_position_8", "range_position_24", "range_position_128"]:
        s = out[col].dropna()
        assert ((s >= 0.0) & (s <= 1.0)).all()


def test_uptrend_classification_case() -> None:
    row = {
        "return_3": 0.002,
        "return_8": 0.004,
        "return_24": 0.01,
        "return_128": 0.03,
        "range_position_128": 0.7,
        "directional_body_latest": 1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.1,
        "three_bar_reversal_score": 0,
        "three_bar_rejection_score": 0,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["long_term_state_128"] in {"uptrend", "weakening_uptrend"}


def test_downtrend_classification_case() -> None:
    row = {
        "return_3": -0.002,
        "return_8": -0.004,
        "return_24": -0.01,
        "return_128": -0.03,
        "range_position_128": 0.3,
        "directional_body_latest": -1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.1,
        "three_bar_reversal_score": 0,
        "three_bar_rejection_score": 0,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["long_term_state_128"] in {"downtrend", "weakening_downtrend"}


def test_sideways_classification_case() -> None:
    row = {
        "return_3": 0.0,
        "return_8": 0.0001,
        "return_24": 0.0003,
        "return_128": 0.0005,
        "range_position_128": 0.5,
        "directional_body_latest": 0,
        "upper_wick_ratio_latest": 0.2,
        "lower_wick_ratio_latest": 0.2,
        "three_bar_reversal_score": 0,
        "three_bar_rejection_score": 1,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["long_term_state_128"] in {"sideways", "transition"}


def test_weakening_uptrend_pullback_case() -> None:
    row = {
        "return_3": -0.001,
        "return_8": -0.002,
        "return_24": -0.004,
        "return_128": 0.02,
        "range_position_128": 0.65,
        "directional_body_latest": -1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.2,
        "three_bar_reversal_score": 1,
        "three_bar_rejection_score": 1,
        "latest_bar_breaks_prior_3_high": False,
        "latest_bar_breaks_prior_3_low": True,
        "latest_bar_returns_inside_prior_3_range": True,
    }
    out = classify_market_state_row(row)
    assert out["long_term_state_128"] == "weakening_uptrend"
    assert out["mid_term_state_24"] == "pullback"


def test_weakening_downtrend_rebound_case() -> None:
    row = {
        "return_3": 0.001,
        "return_8": 0.002,
        "return_24": 0.004,
        "return_128": -0.02,
        "range_position_128": 0.35,
        "directional_body_latest": 1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.2,
        "three_bar_reversal_score": 1,
        "three_bar_rejection_score": 1,
        "latest_bar_breaks_prior_3_high": True,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["long_term_state_128"] == "weakening_downtrend"
    assert out["mid_term_state_24"] == "rebound"


def test_micro_reversal_case() -> None:
    row = {
        "return_3": 0.0015,
        "return_8": -0.0025,
        "return_24": -0.001,
        "return_128": -0.015,
        "range_position_128": 0.4,
        "directional_body_latest": 1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.35,
        "three_bar_reversal_score": 3,
        "three_bar_rejection_score": 1,
        "latest_bar_breaks_prior_3_high": True,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["ultra_short_state_3"] in {"micro_reversal_up", "micro_impulse_up"}


def test_short_term_impulse_case() -> None:
    row = {
        "return_3": 0.001,
        "return_8": 0.004,
        "return_24": 0.002,
        "return_128": 0.008,
        "range_position_128": 0.6,
        "directional_body_latest": 1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.1,
        "three_bar_reversal_score": 0,
        "three_bar_rejection_score": 0,
        "latest_bar_breaks_prior_3_high": True,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["short_term_state_8"] == "impulse_up"


def test_wick_rejection_case() -> None:
    row = {
        "return_3": -0.0005,
        "return_8": -0.0007,
        "return_24": -0.001,
        "return_128": -0.003,
        "range_position_128": 0.45,
        "directional_body_latest": -1,
        "upper_wick_ratio_latest": 0.7,
        "lower_wick_ratio_latest": 0.05,
        "three_bar_reversal_score": 1,
        "three_bar_rejection_score": 3,
        "latest_bar_breaks_prior_3_high": True,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": True,
    }
    out = classify_market_state_row(row)
    assert out["ultra_short_state_3"] in {"micro_rejection_up", "micro_noise"}


def test_local_structure_combination_case() -> None:
    row = {
        "return_3": 0.001,
        "return_8": 0.0015,
        "return_24": -0.003,
        "return_128": 0.02,
        "range_position_128": 0.6,
        "directional_body_latest": 1,
        "upper_wick_ratio_latest": 0.1,
        "lower_wick_ratio_latest": 0.25,
        "three_bar_reversal_score": 2,
        "three_bar_rejection_score": 1,
        "latest_bar_breaks_prior_3_high": True,
        "latest_bar_breaks_prior_3_low": False,
        "latest_bar_returns_inside_prior_3_range": False,
    }
    out = classify_market_state_row(row)
    assert out["local_structure_state"] in {"pullback_in_uptrend", "micro_reversal_inside_trend", "trend_continuation"}


def test_dataset_has_no_trading_fields() -> None:
    ds = build_market_state_dataset(_synthetic_df())
    for col in ["trade_signal", "entry", "exit", "order", "position_size"]:
        assert col not in ds.columns
