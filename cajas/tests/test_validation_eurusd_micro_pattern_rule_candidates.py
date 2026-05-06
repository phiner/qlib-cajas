from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_micro_pattern_rule_candidates import build_micro_pattern_rule_candidates_report


def test_rule_candidates_awaiting_when_manual_missing(tmp_path: Path) -> None:
    manual = tmp_path / "manual.json"
    trial = tmp_path / "trial.json"
    trial.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    report = build_micro_pattern_rule_candidates_report(manual, trial)
    assert report["report_status"] in {"blocked", "awaiting_manual_labels"}


def test_rule_candidates_reads_completed_labels(tmp_path: Path) -> None:
    manual = tmp_path / "manual.json"
    trial = tmp_path / "trial.json"
    completed = tmp_path / "completed.csv"
    manual.write_text(
        json.dumps({"report_status": "manual_micro_pattern_labels_ready", "labeled_row_count": 2}),
        encoding="utf-8",
    )
    trial.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    pd.DataFrame(
        [
            {
                "sample_id": "a",
                "human_micro_pattern_label": "possible_new_rule",
                "human_should_create_rule": "yes",
                "suggested_event_key": "event_a",
            },
            {
                "sample_id": "b",
                "human_micro_pattern_label": "possible_new_rule",
                "human_should_create_rule": "yes",
                "suggested_event_key": "event_a",
            },
        ]
    ).to_csv(completed, index=False)
    report = build_micro_pattern_rule_candidates_report(manual, trial, completed)
    assert report["candidate_rule_count"] == 1
    assert report["create_rule_yes_count"] == 2
    assert report["trial_approval_status"] == "not_approved"
