"""Tests for first unified EURUSD smoke baseline validator."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_first_unified_smoke_baseline import (
    build_first_unified_smoke_baseline_report,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
    return path


def _write_ready_completed(path: Path) -> list[str]:
    sample_ids = ["s1", "s2", "s3"]
    pd.DataFrame(
        {
            "sample_id": sample_ids,
            "human_label": ["unclear", "valid_pattern", "weak_pattern"],
            "human_confidence": ["medium", "high", "medium"],
            "human_rationale_zh": ["理由1", "理由2", "理由3"],
            "human_counterexample_zh": ["", "", ""],
            "human_uncertainty_reason_zh": ["原因1", "", ""],
            "human_context_notes_zh": ["备注1", "备注2", "备注3"],
            "human_pattern_3_feedback_zh": ["p31", "p32", "p33"],
            "human_market_8_feedback_zh": ["m81", "m82", "m83"],
            "human_market_24_feedback_zh": ["m241", "m242", "m243"],
            "human_market_128_feedback_zh": ["m1281", "m1282", "m1283"],
            "human_local_structure_feedback_zh": ["loc1", "loc2", "loc3"],
            "standard_version": ["eurusd_15m_review_standard_v0"] * 3,
            "review_updated_at_utc": ["2026-05-06T00:00:00Z", "2026-05-06T00:01:00Z", "2026-05-06T00:02:00Z"],
        }
    ).to_csv(path, index=False)
    return sample_ids


def _build_report(tmp_path: Path, **overrides) -> dict:
    completed = overrides.get("completed_csv", tmp_path / "completed.csv")
    events = overrides.get("events_jsonl", tmp_path / "events.jsonl")
    llm_jsonl = overrides.get("llm_jsonl", tmp_path / "llm.jsonl")
    smoke_json = overrides.get("smoke_json", tmp_path / "smoke.json")
    quality_json = overrides.get("quality_json", tmp_path / "quality.json")
    llm_report_json = overrides.get("llm_report_json", tmp_path / "llm_report.json")
    trial_json = overrides.get("trial_json", tmp_path / "trial.json")
    return build_first_unified_smoke_baseline_report(
        completed_csv=completed,
        review_events_jsonl=events,
        llm_artifact_jsonl=llm_jsonl,
        smoke_report_json=smoke_json,
        quality_report_json=quality_json,
        llm_artifact_report_json=llm_report_json,
        trial_approval_json=trial_json,
        minimum_reviewed_samples=3,
    )


def test_ready_with_minimum_three_samples_and_layer_evidence(tmp_path: Path) -> None:
    sample_ids = _write_ready_completed(tmp_path / "completed.csv")
    _write_jsonl(
        tmp_path / "events.jsonl",
        [
            {"sample_id": "s1", "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"},
            {"sample_id": "s2", "action_type": "save_and_next", "standard_version": "eurusd_15m_review_standard_v0"},
            {"sample_id": "s3", "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"},
        ],
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [
            {"sample_id": "s1", "human_review": {"human_label": "unclear"}, "multi_layer_evidence": {"x": "1"}},
            {"sample_id": "s2", "human_review": {"human_label": "valid_pattern"}, "multi_layer_evidence": {"x": "1"}},
            {"sample_id": "s3", "human_review": {"human_label": "weak_pattern"}, "multi_layer_evidence": {"x": "1"}},
        ],
    )
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "first_unified_smoke_baseline_ready"
    assert report["reviewed_sample_count"] == 3
    assert report["reviewed_sample_ids"] == sample_ids
    assert report["save_and_next_evidence_present"] is True
    assert report["llm_artifact_contains_human_review"] is True
    assert report["llm_artifact_contains_multi_layer_evidence"] is True
    assert report["trial_approval_status"] == "not_approved"


def test_awaiting_when_completed_csv_missing(tmp_path: Path) -> None:
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build_report(tmp_path)
    assert report["report_status"] == "awaiting_smoke_reviews"


def test_blocked_on_malformed_events_jsonl(tmp_path: Path) -> None:
    _write_ready_completed(tmp_path / "completed.csv")
    (tmp_path / "events.jsonl").write_text("{bad json\n", encoding="utf-8")
    _write_jsonl(tmp_path / "llm.jsonl", [{"sample_id": "s1", "human_review": {}, "multi_layer_evidence": {}}])
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert any(x.startswith("invalid_jsonl_line:") for x in report["blocking_reasons"])


def test_blocked_when_required_overall_fields_missing(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "human_label": ["valid_pattern", "valid_pattern", "valid_pattern"],
            "human_confidence": ["high", "high", "high"],
            "human_rationale_zh": ["", "", ""],
            "review_updated_at_utc": ["2026-05-06T00:00:00Z"] * 3,
            "standard_version": ["eurusd_15m_review_standard_v0"] * 3,
            "human_pattern_3_feedback_zh": ["p", "p", "p"],
        }
    ).to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(
        tmp_path / "events.jsonl",
        [{"sample_id": "s1", "standard_version": "eurusd_15m_review_standard_v0"}] * 3,
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [
            {"sample_id": "s1", "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}},
            {"sample_id": "s2", "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}},
            {"sample_id": "s3", "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}},
        ],
    )
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert "overall_fields_insufficient" in report["blocking_reasons"]


def test_blocked_when_standard_version_missing(tmp_path: Path) -> None:
    sample_ids = _write_ready_completed(tmp_path / "completed.csv")
    completed_df = pd.read_csv(tmp_path / "completed.csv")
    completed_df["standard_version"] = ""
    completed_df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(
        tmp_path / "events.jsonl",
        [{"sample_id": sid, "action_type": "save"} for sid in sample_ids],
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [{"sample_id": sid, "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}} for sid in sample_ids],
    )
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert "standard_version_insufficient" in report["blocking_reasons"]


def test_blocked_when_multi_layer_evidence_missing(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "human_label": ["valid_pattern", "valid_pattern", "valid_pattern"],
            "human_confidence": ["high", "high", "high"],
            "human_rationale_zh": ["理由1", "理由2", "理由3"],
            "review_updated_at_utc": ["2026-05-06T00:00:00Z"] * 3,
            "standard_version": ["eurusd_15m_review_standard_v0"] * 3,
            "human_pattern_3_feedback_zh": ["", "", ""],
            "human_market_8_feedback_zh": ["", "", ""],
            "human_market_24_feedback_zh": ["", "", ""],
            "human_market_128_feedback_zh": ["", "", ""],
            "human_local_structure_feedback_zh": ["", "", ""],
        }
    ).to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(
        tmp_path / "events.jsonl",
        [
            {"sample_id": "s1", "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"},
            {"sample_id": "s2", "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"},
            {"sample_id": "s3", "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"},
        ],
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [
            {"sample_id": "s1", "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}},
            {"sample_id": "s2", "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}},
            {"sample_id": "s3", "human_review": {"x": "1"}, "multi_layer_evidence": {"x": "1"}},
        ],
    )
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert "multi_layer_evidence_insufficient" in report["blocking_reasons"]


def test_blocked_when_llm_artifact_missing_sections(tmp_path: Path) -> None:
    sample_ids = _write_ready_completed(tmp_path / "completed.csv")
    _write_jsonl(
        tmp_path / "events.jsonl",
        [{"sample_id": sid, "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"} for sid in sample_ids],
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [{"sample_id": sid, "human_review": {}} for sid in sample_ids],
    )
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert "llm_artifact_missing_human_review" in report["blocking_reasons"]


def test_blocked_when_trial_approval_not_not_approved(tmp_path: Path) -> None:
    _write_ready_completed(tmp_path / "completed.csv")
    _write_jsonl(tmp_path / "events.jsonl", [])
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert report["real_llm_integration_approved"] is True
    assert "trial_approval_must_be_not_approved:approved" in report["blocking_reasons"]


def test_blocks_on_non_english_runtime_keys(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "sample_id": ["s1", "s2", "s3"],
            "human_label": ["valid_pattern", "valid_pattern", "valid_pattern"],
            "human_confidence": ["high", "high", "high"],
            "human_rationale_zh": ["理由1", "理由2", "理由3"],
            "review_updated_at_utc": ["2026-05-06T00:00:00Z"] * 3,
            "standard_version": ["eurusd_15m_review_standard_v0"] * 3,
            "中文字段": ["x", "x", "x"],
        }
    ).to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [])
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "smoke.json", {"report_status": "human_review_smoke_ready"})
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})

    report = _build_report(tmp_path)
    assert report["report_status"] == "blocked"
    assert "non_english_schema_keys_detected" in report["blocking_reasons"]
