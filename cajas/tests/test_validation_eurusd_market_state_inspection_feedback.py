from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_inspection_feedback import (
    build_market_state_inspection_feedback_report,
)


def _inspection_packet_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample_id": "s-001",
                "human_pattern_3_agreement": "",
                "human_pattern_3_correct_label": "",
                "human_pattern_3_feedback_zh": "",
                "human_market_8_agreement": "",
                "human_market_8_correct_state": "",
                "human_market_8_feedback_zh": "",
                "human_market_24_agreement": "",
                "human_market_24_correct_state": "",
                "human_market_24_feedback_zh": "",
                "human_market_128_agreement": "",
                "human_market_128_correct_state": "",
                "human_market_128_feedback_zh": "",
                "human_local_structure_agreement": "",
                "human_local_structure_correct_state": "",
                "human_local_structure_feedback_zh": "",
                "human_definition_issue_zh": "",
                "human_rule_adjustment_suggestion_zh": "",
                "review_updated_at_utc": "",
            }
        ]
    )


def test_feedback_missing_completed_is_awaiting(tmp_path: Path) -> None:
    inspection = tmp_path / "inspection.csv"
    _inspection_packet_df().to_csv(inspection, index=False)
    report = build_market_state_inspection_feedback_report(
        inspection_packet_csv=inspection,
        completed_feedback_csv=tmp_path / "missing.csv",
        trial_approval_json=tmp_path / "trial.json",
    )
    assert report["report_status"] == "awaiting_market_state_inspection_feedback"


def test_feedback_empty_completed_is_awaiting(tmp_path: Path) -> None:
    inspection = tmp_path / "inspection.csv"
    completed = tmp_path / "completed.csv"
    _inspection_packet_df().to_csv(inspection, index=False)
    _inspection_packet_df().to_csv(completed, index=False)
    report = build_market_state_inspection_feedback_report(
        inspection_packet_csv=inspection,
        completed_feedback_csv=completed,
        trial_approval_json=tmp_path / "trial.json",
    )
    assert report["report_status"] == "awaiting_market_state_inspection_feedback"


def test_feedback_watch_on_disagree_without_rationale(tmp_path: Path) -> None:
    inspection = tmp_path / "inspection.csv"
    completed = tmp_path / "completed.csv"
    trial = tmp_path / "trial.json"
    _inspection_packet_df().to_csv(inspection, index=False)
    df = _inspection_packet_df()
    df.loc[0, "human_pattern_3_agreement"] = "disagree"
    df.loc[0, "human_pattern_3_correct_label"] = "micro_noise"
    df.to_csv(completed, index=False)
    trial.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    report = build_market_state_inspection_feedback_report(
        inspection_packet_csv=inspection,
        completed_feedback_csv=completed,
        trial_approval_json=trial,
    )
    assert report["report_status"] == "market_state_inspection_feedback_watch"


def test_feedback_ready_when_valid_feedback_present(tmp_path: Path) -> None:
    inspection = tmp_path / "inspection.csv"
    completed = tmp_path / "completed.csv"
    trial = tmp_path / "trial.json"
    _inspection_packet_df().to_csv(inspection, index=False)
    df = _inspection_packet_df()
    df.loc[0, "human_pattern_3_agreement"] = "agree"
    df.loc[0, "human_market_8_agreement"] = "agree"
    df.loc[0, "human_market_24_agreement"] = "agree"
    df.loc[0, "human_market_128_agreement"] = "agree"
    df.loc[0, "human_local_structure_agreement"] = "agree"
    df.to_csv(completed, index=False)
    trial.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    report = build_market_state_inspection_feedback_report(
        inspection_packet_csv=inspection,
        completed_feedback_csv=completed,
        trial_approval_json=trial,
    )
    assert report["report_status"] == "market_state_inspection_feedback_ready"


def test_feedback_blocks_on_invalid_enum_and_trading_fields(tmp_path: Path) -> None:
    inspection = tmp_path / "inspection.csv"
    completed = tmp_path / "completed.csv"
    _inspection_packet_df().to_csv(inspection, index=False)
    df = _inspection_packet_df()
    df["trade_signal"] = ""
    df.loc[0, "human_pattern_3_agreement"] = "bad_enum"
    df.to_csv(completed, index=False)
    report = build_market_state_inspection_feedback_report(
        inspection_packet_csv=inspection,
        completed_feedback_csv=completed,
        trial_approval_json=tmp_path / "trial.json",
    )
    assert report["report_status"] == "blocked"
