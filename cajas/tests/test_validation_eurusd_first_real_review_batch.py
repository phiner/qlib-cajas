"""Tests for first real EURUSD review batch report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_first_real_review_batch import (
    build_first_real_review_batch_report,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def _build(tmp_path: Path, **kwargs) -> dict:
    return build_first_real_review_batch_report(
        completed_csv=kwargs.get("completed_csv", tmp_path / "completed.csv"),
        review_events_jsonl=kwargs.get("events_jsonl", tmp_path / "events.jsonl"),
        llm_artifact_jsonl=kwargs.get("llm_jsonl", tmp_path / "llm.jsonl"),
        human_review_quality_json=kwargs.get("quality_json", tmp_path / "quality.json"),
        llm_artifact_report_json=kwargs.get("llm_report_json", tmp_path / "llm_report.json"),
        trial_approval_json=kwargs.get("trial_json", tmp_path / "trial.json"),
        minimum_total_reviewed=10,
        minimum_new_since_smoke=7,
        minimum_layer_feedback_ratio=0.8,
    )


def _reviewed_rows(count: int, layer_blank_ratio: float = 0.0) -> pd.DataFrame:
    ids = [f"s{i:02d}" for i in range(count)]
    smoke = {"s00", "s01", "s02"}
    rows = []
    for i, sid in enumerate(ids):
        layer_blank = (i / max(1, count)) < layer_blank_ratio
        rows.append(
            {
                "sample_id": sid if sid not in {"s00", "s01", "s02"} else ["eurusd15m_000028", "eurusd15m_000068", "eurusd15m_000124"][i],
                "candidate_type": "type_a" if i % 2 == 0 else "type_b",
                "human_label": "valid_pattern" if i % 3 else "unclear",
                "human_confidence": "high" if i % 2 else "medium",
                "human_rationale_zh": f"理由{i}",
                "human_counterexample_zh": "" if i % 2 else f"反例{i}",
                "human_uncertainty_reason_zh": f"不确定{i}" if i % 3 == 0 else "",
                "human_context_notes_zh": f"备注{i}",
                "human_pattern_3_feedback_zh": "" if layer_blank else f"p3{i}",
                "human_market_8_feedback_zh": "" if layer_blank else f"m8{i}",
                "human_market_24_feedback_zh": "" if layer_blank else f"m24{i}",
                "human_market_128_feedback_zh": "" if layer_blank else f"m128{i}",
                "human_local_structure_feedback_zh": "" if layer_blank else f"loc{i}",
                "standard_version": "eurusd_15m_review_standard_v0",
                "review_updated_at_utc": f"2026-05-06T00:{i:02d}:00Z",
            }
        )
    return pd.DataFrame(rows)


def test_awaiting_when_fewer_than_ten_reviewed(tmp_path: Path) -> None:
    _reviewed_rows(9).to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [])
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "awaiting_real_review_batch"


def test_ready_when_thresholds_met(tmp_path: Path) -> None:
    df = _reviewed_rows(10, layer_blank_ratio=0.0)
    df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(
        tmp_path / "events.jsonl",
        [{"sample_id": str(x), "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"} for x in df["sample_id"].tolist()],
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [
            {"sample_id": str(x), "human_review": {"ok": "1"}, "multi_layer_evidence": {"ok": "1"}}
            for x in df["sample_id"].tolist()
        ],
    )
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "first_real_review_batch_ready"
    assert report["new_reviewed_sample_count_since_smoke"] >= 7


def test_watch_when_layer_coverage_low(tmp_path: Path) -> None:
    df = _reviewed_rows(10, layer_blank_ratio=0.4)
    df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(
        tmp_path / "events.jsonl",
        [{"sample_id": str(x), "action_type": "save", "standard_version": "eurusd_15m_review_standard_v0"} for x in df["sample_id"].tolist()],
    )
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [{"sample_id": str(x), "human_review": {"ok": "1"}, "multi_layer_evidence": {"ok": "1"}} for x in df["sample_id"].tolist()],
    )
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "first_real_review_batch_watch"


def test_blocked_on_malformed_jsonl(tmp_path: Path) -> None:
    _reviewed_rows(10).to_csv(tmp_path / "completed.csv", index=False)
    (tmp_path / "events.jsonl").write_text("{bad\n", encoding="utf-8")
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "blocked"


def test_smoke_ids_excluded_from_new_count(tmp_path: Path) -> None:
    df = _reviewed_rows(10)
    df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [{"sample_id": str(x), "action_type": "save"} for x in df["sample_id"].tolist()])
    _write_jsonl(
        tmp_path / "llm.jsonl",
        [{"sample_id": str(x), "human_review": {"ok": "1"}, "multi_layer_evidence": {"ok": "1"}} for x in df["sample_id"].tolist()],
    )
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["new_reviewed_sample_count_since_smoke"] == 7


def test_blocked_when_multi_layer_evidence_missing_in_artifacts(tmp_path: Path) -> None:
    df = _reviewed_rows(10)
    df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [{"sample_id": str(x), "action_type": "save"} for x in df["sample_id"].tolist()])
    _write_jsonl(tmp_path / "llm.jsonl", [{"sample_id": str(x), "human_review": {"ok": "1"}} for x in df["sample_id"].tolist()])
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "blocked"
    assert "llm_artifact_missing_multi_layer_evidence" in report["blocking_reasons"]


def test_blocked_when_trial_approved(tmp_path: Path) -> None:
    _reviewed_rows(10).to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [])
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "blocked"
    assert report["trial_approval_status"] == "approved"


def test_blocked_on_non_english_runtime_keys(tmp_path: Path) -> None:
    df = _reviewed_rows(10)
    df["中文字段"] = "x"
    df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [])
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "blocked"
    assert "non_english_schema_keys_detected" in report["blocking_reasons"]


def test_blocked_on_live_provider_markers(tmp_path: Path) -> None:
    df = _reviewed_rows(10)
    df["openai_provider"] = "x"
    df.to_csv(tmp_path / "completed.csv", index=False)
    _write_jsonl(tmp_path / "events.jsonl", [])
    _write_jsonl(tmp_path / "llm.jsonl", [])
    _write_json(tmp_path / "quality.json", {"report_status": "human_review_quality_watch"})
    _write_json(tmp_path / "llm_report.json", {"report_status": "llm_review_artifacts_ready"})
    _write_json(tmp_path / "trial.json", {"approval_status": "not_approved"})
    report = _build(tmp_path)
    assert report["report_status"] == "blocked"
    assert "live_llm_provider_markers_detected" in report["blocking_reasons"]
