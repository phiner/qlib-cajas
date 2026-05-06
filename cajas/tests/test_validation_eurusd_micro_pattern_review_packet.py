"""Tests for EURUSD micro-pattern review packet generation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_micro_pattern_review_packet import build_micro_pattern_review_packet


def _trial(path: Path, status: str = "not_approved") -> None:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")


def test_review_packet_builds_and_has_context(tmp_path: Path) -> None:
    csv = tmp_path / "state.csv"
    rows = []
    for i in range(10):
        rows.append(
            {
                "timestamp": f"2025-01-01 00:{i:02d}:00+00:00",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "micro_pattern_event_3": "micro_noise",
                "micro_pattern_rule_version": "eurusd_micro_pattern_rules_v0",
                "open": 1.1,
                "high": 1.1002,
                "low": 1.0998,
                "close": 1.1001,
                "prev_open_1": 1.1,
                "prev_high_1": 1.1002,
                "prev_low_1": 1.0998,
                "prev_close_1": 1.1001,
                "prev_open_2": 1.1,
                "prev_high_2": 1.1002,
                "prev_low_2": 1.0998,
                "prev_close_2": 1.1001,
                "return_3": 0.0001,
                "latest_close_position_in_candle": 0.5,
                "range_position_3": 0.5,
                "body_ratio_latest": 0.2,
                "upper_wick_ratio_latest": 0.2,
                "lower_wick_ratio_latest": 0.2,
                "range_ratio_3_8": 0.6,
                "micro_event_reason_code": "micro_conflicting_sequence",
            }
        )
    pd.DataFrame(rows).to_csv(csv, index=False)
    trial = tmp_path / "trial.json"
    _trial(trial)

    out_csv = tmp_path / "packet.csv"
    out_jsonl = tmp_path / "packet.jsonl"
    report = build_micro_pattern_review_packet(
        market_state_csv=csv,
        output_csv=out_csv,
        output_jsonl=out_jsonl,
        trial_approval_json=trial,
        max_rows=5,
    )
    assert report["report_status"] == "micro_pattern_review_packet_ready"
    assert report["packet_row_count"] == 5
    packet = pd.read_csv(out_csv)
    assert "bar_t_minus_2_open" in packet.columns
    assert "human_micro_pattern_label" in packet.columns


def test_review_packet_deterministic_sampling(tmp_path: Path) -> None:
    csv = tmp_path / "state.csv"
    rows = []
    for i in range(20):
        rows.append(
            {
                "timestamp": f"2025-01-01 00:{i:02d}:00+00:00",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "micro_pattern_event_3": "micro_noise",
                "micro_pattern_rule_version": "eurusd_micro_pattern_rules_v0",
                "open": 1.1,
                "high": 1.1002,
                "low": 1.0998,
                "close": 1.1001,
                "prev_open_1": 1.1,
                "prev_high_1": 1.1002,
                "prev_low_1": 1.0998,
                "prev_close_1": 1.1001,
                "prev_open_2": 1.1,
                "prev_high_2": 1.1002,
                "prev_low_2": 1.0998,
                "prev_close_2": 1.1001,
                "return_3": 0.0001,
                "latest_close_position_in_candle": 0.5,
                "range_position_3": 0.5,
                "body_ratio_latest": 0.2,
                "upper_wick_ratio_latest": 0.2,
                "lower_wick_ratio_latest": 0.2,
                "range_ratio_3_8": 0.6,
                "micro_event_reason_code": "micro_conflicting_sequence",
            }
        )
    pd.DataFrame(rows).to_csv(csv, index=False)
    trial = tmp_path / "trial.json"
    _trial(trial)

    out_csv_1 = tmp_path / "packet1.csv"
    out_jsonl_1 = tmp_path / "packet1.jsonl"
    out_csv_2 = tmp_path / "packet2.csv"
    out_jsonl_2 = tmp_path / "packet2.jsonl"

    build_micro_pattern_review_packet(
        market_state_csv=csv,
        output_csv=out_csv_1,
        output_jsonl=out_jsonl_1,
        trial_approval_json=trial,
        max_rows=7,
    )
    build_micro_pattern_review_packet(
        market_state_csv=csv,
        output_csv=out_csv_2,
        output_jsonl=out_jsonl_2,
        trial_approval_json=trial,
        max_rows=7,
    )

    assert out_csv_1.read_text(encoding="utf-8") == out_csv_2.read_text(encoding="utf-8")
