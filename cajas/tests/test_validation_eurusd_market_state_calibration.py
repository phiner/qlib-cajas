"""Tests for EURUSD market-state calibration report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_calibration import build_market_state_calibration_report


def _write_trial(path: Path, status: str = "not_approved") -> None:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")


def _write_state_report(path: Path) -> None:
    path.write_text(json.dumps({"report_status": "market_state_dataset_ready"}), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def _row(**kw: object) -> dict:
    base = {
        "micro_pattern_event_3": "micro_noise",
        "micro_pattern_direction_3": "mixed",
        "micro_pattern_strength_3": "weak",
        "short_term_state_8": "sideways",
        "mid_term_state_24": "sideways",
        "long_term_state_128": "sideways",
        "local_structure_state": "unknown",
        "structure_confidence": "low",
        "micro_event_reason_code": "micro_conflicting_sequence",
        "local_structure_reason_code": "structure_local_unknown",
        "confidence_reason_code": "confidence_conflicting_windows",
    }
    base.update(kw)
    return base


def test_calibration_report_builds(tmp_path: Path) -> None:
    csv_path = tmp_path / "state.csv"
    _write_csv(csv_path, [_row() for _ in range(12)])
    trial = tmp_path / "trial.json"
    state_report = tmp_path / "state_report.json"
    _write_trial(trial)
    _write_state_report(state_report)

    report = build_market_state_calibration_report(
        market_state_csv=csv_path,
        market_state_report_json=state_report,
        trial_approval_json=trial,
    )
    assert report["report_status"] == "market_state_calibration_ready"
    assert report["three_bar_logic_type"] == "pattern_event"
    assert report["structure_logic_type"] == "quantitative_8_24_128"


def test_dominant_and_catch_all_warnings_trigger(tmp_path: Path) -> None:
    csv_path = tmp_path / "state.csv"
    rows = [_row() for _ in range(90)] + [_row(micro_pattern_event_3="three_bar_reversal_up", local_structure_state="range_chop", structure_confidence="medium") for _ in range(10)]
    _write_csv(csv_path, rows)
    trial = tmp_path / "trial.json"
    state_report = tmp_path / "state_report.json"
    _write_trial(trial)
    _write_state_report(state_report)

    report = build_market_state_calibration_report(
        market_state_csv=csv_path,
        market_state_report_json=state_report,
        trial_approval_json=trial,
    )
    warnings = set(report["catch_all_state_warnings"])
    assert "dominant_micro_event_overconcentrated" in warnings
    assert "catch_all_micro_event_high" in warnings
    assert "dominant_structure_state_overconcentrated" in warnings or "unknown_local_structure_high" in warnings
    assert "low_confidence_dominant" in warnings


def test_reason_code_distribution_present(tmp_path: Path) -> None:
    csv_path = tmp_path / "state.csv"
    _write_csv(
        csv_path,
        [
            _row(micro_event_reason_code="micro_lower_sweep_reclaim", local_structure_reason_code="structure_local_rebound_in_downtrend", confidence_reason_code="confidence_partially_aligned_windows"),
            _row(micro_event_reason_code="micro_upper_sweep_reject", local_structure_reason_code="structure_local_pullback_in_uptrend", confidence_reason_code="confidence_aligned_windows"),
        ],
    )
    trial = tmp_path / "trial.json"
    state_report = tmp_path / "state_report.json"
    _write_trial(trial)
    _write_state_report(state_report)

    report = build_market_state_calibration_report(
        market_state_csv=csv_path,
        market_state_report_json=state_report,
        trial_approval_json=trial,
    )
    reason_dist = report["reason_code_distribution"]
    assert "micro_event_reason_code_distribution" in reason_dist
    assert "structure_reason_code_distribution" in reason_dist
    assert "confidence_reason_code_distribution" in reason_dist
    assert report["trial_approval_status"] == "not_approved"
