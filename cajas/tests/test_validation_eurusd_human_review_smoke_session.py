"""Tests for EURUSD human review smoke-session report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_human_review_smoke_session import build_human_review_smoke_session_report


def _write_trial(path: Path, status: str = "not_approved") -> Path:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
    return path


def test_awaiting_when_no_completed_or_events(tmp_path: Path) -> None:
    report = build_human_review_smoke_session_report(
        completed_csv=tmp_path / "missing.csv",
        review_events_jsonl=tmp_path / "missing.jsonl",
        trial_approval_json=_write_trial(tmp_path / "trial.json"),
    )
    assert report["report_status"] == "awaiting_smoke_reviews"


def test_blocked_on_trial_approved(tmp_path: Path) -> None:
    report = build_human_review_smoke_session_report(
        completed_csv=tmp_path / "missing.csv",
        review_events_jsonl=tmp_path / "missing.jsonl",
        trial_approval_json=_write_trial(tmp_path / "trial.json", status="approved_for_limited_trial"),
    )
    assert report["report_status"] == "blocked"


def test_blocked_on_duplicates(tmp_path: Path) -> None:
    completed = tmp_path / "completed.csv"
    events = tmp_path / "events.jsonl"
    pd.DataFrame(
        {
            "sample_id": ["s1", "s1"],
            "human_label": ["valid_pattern", "valid_pattern"],
            "human_confidence": ["high", "high"],
            "human_rationale_zh": ["理由", "理由"],
            "human_counterexample_zh": ["", ""],
            "human_uncertainty_reason_zh": ["", ""],
            "human_context_notes_zh": ["", ""],
            "review_updated_at_utc": ["2026-05-01T00:00:00Z", "2026-05-01T01:00:00Z"],
        }
    ).to_csv(completed, index=False)
    events.write_text(json.dumps({"sample_id": "s1", "standard_version": "eurusd_15m_review_standard_v0"}) + "\n", encoding="utf-8")

    report = build_human_review_smoke_session_report(
        completed_csv=completed,
        review_events_jsonl=events,
        trial_approval_json=_write_trial(tmp_path / "trial.json"),
    )
    assert report["report_status"] == "blocked"


def test_ready_when_reviews_and_standard_present(tmp_path: Path) -> None:
    completed = tmp_path / "completed.csv"
    events = tmp_path / "events.jsonl"
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "human_label": ["valid_pattern", "unclear"],
            "human_confidence": ["high", "medium"],
            "human_rationale_zh": ["理由1", "理由2"],
            "human_counterexample_zh": ["", ""],
            "human_uncertainty_reason_zh": ["", "原因"],
            "human_context_notes_zh": ["", ""],
            "review_updated_at_utc": ["2026-05-01T00:00:00Z", "2026-05-01T01:00:00Z"],
        }
    ).to_csv(completed, index=False)
    rows = [
        {"sample_id": "s1", "standard_version": "eurusd_15m_review_standard_v0", "review": {"human_rationale_zh": "理由1"}},
        {"sample_id": "s2", "standard_version": "eurusd_15m_review_standard_v0", "review": {"human_rationale_zh": "理由2"}},
    ]
    events.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")

    report = build_human_review_smoke_session_report(
        completed_csv=completed,
        review_events_jsonl=events,
        trial_approval_json=_write_trial(tmp_path / "trial.json"),
    )
    assert report["report_status"] == "human_review_smoke_ready"
    assert report["zh_rationale_saved_count"] == 2
    assert report["standard_version_saved_count"] == 2
