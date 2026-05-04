import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_review_summary import build_validation_eurusd_pattern_review_summary


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_summary_awaiting_input(tmp_path: Path) -> None:
    feedback = _write(tmp_path / "feedback.json", {"status": "awaiting_review_input", "reviewed_count": 0})
    payload = build_validation_eurusd_pattern_review_summary(
        feedback_report=feedback,
        completed_review_csv=tmp_path / "missing.csv",
    )
    assert payload["status"] == "awaiting_review_input"
    assert payload["recommendation"] == "complete_review_template_first"


def test_summary_with_reviewed_rows(tmp_path: Path) -> None:
    feedback = _write(tmp_path / "feedback.json", {"status": "ready", "reviewed_count": 2})
    c = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "candidate_type": "compression_candidate",
                "human_pattern_label": "valid_pattern",
                "review_confidence": 5,
                "structure_quality": 4,
                "follow_through_quality": 4,
                "review_status": "reviewed",
            },
            {
                "sample_id": "s2",
                "candidate_type": "compression_candidate",
                "human_pattern_label": "false_positive",
                "review_confidence": 4,
                "structure_quality": 2,
                "follow_through_quality": 2,
                "review_status": "reviewed",
            },
        ]
    )
    cp = tmp_path / "completed.csv"
    c.to_csv(cp, index=False)

    payload = build_validation_eurusd_pattern_review_summary(
        feedback_report=feedback,
        completed_review_csv=cp,
        minimum_review_threshold=1,
    )
    assert payload["status"] in {"ready", "watch"}
    assert "compression_candidate" in payload["candidate_type_summary"]
