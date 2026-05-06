from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_inspection_packet import (
    FEEDBACK_FIELDS,
    build_market_state_inspection_packet,
)


def _sample_export_df() -> pd.DataFrame:
    rows = []
    for i in range(12):
        rows.append(
            {
                "sample_id": f"s-{i:03d}",
                "sample_type": "pattern_sample" if i % 2 == 0 else "market_state_sample",
                "timestamp": f"2025-01-01T00:{i:02d}:00Z",
                "pattern_3_event": "micro_noise" if i % 3 == 0 else "lower_sweep_reclaim",
                "market_8_state": "range_chop",
                "market_24_state": "pullback_in_uptrend",
                "market_128_state": "high_level_consolidation",
                "local_structure_state": "range_chop",
                "structure_confidence": "high" if i % 4 == 0 else "low",
                "pattern_3_max_bars": 3,
                "pattern_3_actual_bars_used": 3,
                "market_8_max_bars": 8,
                "market_8_actual_bars_used": 8,
                "market_24_max_bars": 24,
                "market_24_actual_bars_used": 24,
                "market_128_max_bars": 128,
                "market_128_actual_bars_used": 128,
            }
        )
    return pd.DataFrame(rows)


def test_inspection_packet_builds_and_has_feedback_fields(tmp_path: Path) -> None:
    sample_csv = tmp_path / "sample.csv"
    output_csv = tmp_path / "packet.csv"
    output_jsonl = tmp_path / "packet.jsonl"
    trial_json = tmp_path / "trial.json"
    _sample_export_df().to_csv(sample_csv, index=False)
    trial_json.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")

    report = build_market_state_inspection_packet(
        sample_export_csv=sample_csv,
        output_csv=output_csv,
        output_jsonl=output_jsonl,
        trial_approval_json=trial_json,
        max_rows=8,
    )
    assert report["report_status"] == "market_state_inspection_packet_ready"
    assert report["packet_row_count"] <= 8
    packet = pd.read_csv(output_csv)
    assert all(c in packet.columns for c in FEEDBACK_FIELDS)
    assert report["pattern_sample_count"] > 0
    assert report["market_state_sample_count"] > 0
    assert report["actual_bars_used_valid"] is True
    assert report["trial_approval_status"] == "not_approved"


def test_inspection_packet_blocks_on_trial_approved(tmp_path: Path) -> None:
    sample_csv = tmp_path / "sample.csv"
    output_csv = tmp_path / "packet.csv"
    output_jsonl = tmp_path / "packet.jsonl"
    trial_json = tmp_path / "trial.json"
    _sample_export_df().to_csv(sample_csv, index=False)
    trial_json.write_text(json.dumps({"status": "approved"}), encoding="utf-8")
    report = build_market_state_inspection_packet(
        sample_export_csv=sample_csv,
        output_csv=output_csv,
        output_jsonl=output_jsonl,
        trial_approval_json=trial_json,
        max_rows=8,
    )
    assert report["report_status"] == "blocked"
