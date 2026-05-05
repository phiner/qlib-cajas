"""Tests for EURUSD micro-noise profiling report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_micro_noise_profile import build_micro_noise_profile_report


def _trial(path: Path, status: str = "not_approved") -> None:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")


def test_micro_noise_profile_builds(tmp_path: Path) -> None:
    csv = tmp_path / "state.csv"
    rows = [
        {"micro_pattern_event_3": "micro_noise", "body_ratio_latest": 0.1, "upper_wick_ratio_latest": 0.2, "lower_wick_ratio_latest": 0.2, "return_3": 0.0, "range_ratio_3_8": 0.4, "micro_event_reason_code": "x", "micro_pattern_rule_version": "eurusd_micro_pattern_rules_v0"},
        {"micro_pattern_event_3": "micro_noise", "body_ratio_latest": 0.3, "upper_wick_ratio_latest": 0.4, "lower_wick_ratio_latest": 0.4, "return_3": 0.0005, "range_ratio_3_8": 0.8, "micro_event_reason_code": "micro_conflicting_sequence", "micro_pattern_rule_version": "eurusd_micro_pattern_rules_v0"},
        {"micro_pattern_event_3": "three_bar_reversal_up", "body_ratio_latest": 0.6, "upper_wick_ratio_latest": 0.1, "lower_wick_ratio_latest": 0.1, "return_3": 0.002, "range_ratio_3_8": 1.0, "micro_event_reason_code": "r", "micro_pattern_rule_version": "eurusd_micro_pattern_rules_v0"},
    ]
    pd.DataFrame(rows).to_csv(csv, index=False)
    trial = tmp_path / "trial.json"
    _trial(trial)

    report = build_micro_noise_profile_report(market_state_csv=csv, trial_approval_json=trial)
    assert report["report_status"] == "micro_noise_profile_ready"
    assert report["micro_noise_count"] == 2
    assert isinstance(report["noise_subtype_distribution"], dict)
    assert report["trial_approval_status"] == "not_approved"


def test_micro_noise_profile_blocks_on_missing_column(tmp_path: Path) -> None:
    csv = tmp_path / "state.csv"
    pd.DataFrame([{"x": 1}]).to_csv(csv, index=False)
    trial = tmp_path / "trial.json"
    _trial(trial)
    report = build_micro_noise_profile_report(market_state_csv=csv, trial_approval_json=trial)
    assert report["report_status"] == "blocked"
