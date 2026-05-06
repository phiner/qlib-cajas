from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_inspection_gui import build_market_state_inspection_gui_report
from cajas.reports.validation_eurusd_market_state_inspection_packet import FEEDBACK_FIELDS


def _packet_df() -> pd.DataFrame:
    row = {
        "sample_id": "s-001",
        "timestamp": "2025-01-01T06:00:00Z",
        "symbol": "EURUSD",
        "timeframe": "15m",
        "pattern_3_event": "lower_sweep_reclaim",
        "market_8_state": "sideways",
        "market_24_state": "consolidation",
        "market_128_state": "high_level_consolidation",
        "local_structure_state": "high_level_consolidation",
        "pattern_3_actual_bars_used": 3,
        "market_8_actual_bars_used": 8,
        "market_24_actual_bars_used": 24,
        "market_128_actual_bars_used": 128,
        "pattern_3_rationale_zh": "3-bar rationale",
        "market_8_rationale_zh": "8-bar rationale",
        "market_24_rationale_zh": "24-bar rationale",
        "market_128_rationale_zh": "128-bar rationale",
        "market_state_rationale_zh": "combined rationale",
    }
    for col in FEEDBACK_FIELDS:
        row[col] = ""
    return pd.DataFrame([row])


def _raw_df(n: int = 300) -> pd.DataFrame:
    ts = pd.date_range("2024-12-30", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": [1.10 + i * 0.0001 for i in range(n)],
            "high": [1.101 + i * 0.0001 for i in range(n)],
            "low": [1.099 + i * 0.0001 for i in range(n)],
            "close": [1.1005 + i * 0.0001 for i in range(n)],
        }
    )


def test_gui_report_ready(tmp_path: Path) -> None:
    packet_csv = tmp_path / "packet.csv"
    raw_csv = tmp_path / "raw.csv"
    trial_json = tmp_path / "trial.json"
    _packet_df().to_csv(packet_csv, index=False)
    _raw_df().to_csv(raw_csv, index=False)
    trial_json.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")

    report = build_market_state_inspection_gui_report(
        inspection_packet_csv=packet_csv,
        raw_csv=raw_csv,
        trial_approval_json=trial_json,
    )
    assert report["report_status"] == "market_state_inspection_gui_ready"
    assert report["layer_highlights_ready"] is True
    assert report["chart_helpers_ready"] is True
    assert report["rationale_fields_present"] is True
    assert report["feedback_fields_present"] is True
    assert report["compressed_time_axis_enabled"] is True
    assert report["gap_markers_enabled"] is True
    assert report["market_128_visualization_ready"] is True
    assert report["sidebar_minimized_for_review"] is True
    assert report["review_layout_mode"] == "side_by_side_chart_feedback"
    assert report["chart_feedback_simultaneous_view_ready"] is True
    assert report["chart_width_priority_ready"] is True
    assert report["feedback_panel_compact_width_ready"] is True
    assert report["font_size_readability_ready"] is True
    assert report["compact_feedback_layout_ready"] is True
    assert report["advanced_debug_collapsed_by_default"] is True
    assert report["packet_row_count"] == 1
    assert report["trial_approval_status"] == "not_approved"


def test_gui_report_blocked_missing_inputs(tmp_path: Path) -> None:
    report = build_market_state_inspection_gui_report(
        inspection_packet_csv=tmp_path / "missing-packet.csv",
        raw_csv=tmp_path / "missing-raw.csv",
        trial_approval_json=tmp_path / "trial.json",
    )
    assert report["report_status"] == "blocked"
    assert "inspection_packet_missing" in report["blocking_reasons"]
    assert "raw_clean_csv_missing" in report["blocking_reasons"]
