from __future__ import annotations

from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_dataset_quality import build_market_state_dataset_quality_report


def test_dataset_quality_ready_or_watch(tmp_path: Path) -> None:
    csv = tmp_path / "state.csv"
    jsonl = tmp_path / "state.jsonl"
    row = {
        "timestamp": "2025-01-01T00:00:00+00:00",
        "market_state_rule_version": "eurusd_market_state_rules_v0",
        "micro_pattern_rule_version": "eurusd_micro_pattern_rules_v0",
        "micro_pattern_event_3": "micro_noise",
        "micro_pattern_direction_3": "mixed",
        "micro_pattern_strength_3": "weak",
        "short_term_state_8": "sideways",
        "mid_term_state_24": "sideways",
        "long_term_state_128": "sideways",
        "local_structure_state": "range_chop",
        "structure_confidence": "low",
        "micro_event_rationale_zh": "x",
        "market_state_rationale_zh": "x",
        "range_position_3": 0.5,
        "range_position_8": 0.5,
        "range_position_24": 0.5,
        "range_position_128": 0.5,
        "return_3": 0.0,
        "return_8": 0.0,
        "return_24": 0.0,
        "return_128": 0.0,
        "gap_count_128": 0,
        "largest_gap_hours_128": 0.25,
    }
    pd.DataFrame([row]).to_csv(csv, index=False)
    jsonl.write_text('{"a":1}\n', encoding="utf-8")
    report = build_market_state_dataset_quality_report(csv, jsonl)
    assert report["report_status"] in {"market_state_dataset_quality_ready", "market_state_dataset_quality_watch"}
