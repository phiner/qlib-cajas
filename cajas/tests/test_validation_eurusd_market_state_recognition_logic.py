"""Targeted tests for market-state recognition split logic."""

from __future__ import annotations

import pandas as pd

from cajas.research.eurusd_market_state import build_market_state_dataset


def test_market_state_schema_includes_micro_and_structure_fields() -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=140, freq="15min", tz="UTC"),
            "open": [1.1 + i * 0.0001 for i in range(140)],
            "high": [1.1003 + i * 0.0001 for i in range(140)],
            "low": [1.0997 + i * 0.0001 for i in range(140)],
            "close": [1.1001 + i * 0.0001 for i in range(140)],
        }
    )
    out = build_market_state_dataset(df)
    required = [
        "micro_pattern_event_3",
        "micro_pattern_direction_3",
        "micro_pattern_strength_3",
        "micro_reversal_detected_3",
        "micro_rejection_detected_3",
        "micro_sweep_detected_3",
        "micro_event_rationale_zh",
        "short_term_state_8",
        "mid_term_state_24",
        "long_term_state_128",
        "local_structure_state",
        "structure_confidence",
    ]
    for col in required:
        assert col in out.columns
    assert "trade_signal" not in out.columns
    assert "order" not in out.columns
