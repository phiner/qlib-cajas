"""Tests for deterministic EURUSD LLM-ready review artifact export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_llm_review_artifacts import (
    build_llm_review_artifacts_report,
    write_artifacts_jsonl,
)


def _clean_view(path: Path) -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2020-01-01", periods=300, freq="15min", tz="UTC"),
            "open": [1.10 + i * 0.0001 for i in range(300)],
            "high": [1.11 + i * 0.0001 for i in range(300)],
            "low": [1.09 + i * 0.0001 for i in range(300)],
            "close": [1.105 + i * 0.0001 for i in range(300)],
        }
    )
    df.to_csv(path, index=False)


def _batch(path: Path) -> None:
    df = pd.DataFrame(
        {
            "sample_id": ["s1", "s2"],
            "timestamp": ["2020-01-01T10:00:00+00:00", "2020-01-01T11:00:00+00:00"],
            "candidate_type": ["lower_wick_rejection_candidate", "short_trend_up_candidate"],
        }
    )
    df.to_csv(path, index=False)


def _completed(path: Path) -> None:
    df = pd.DataFrame(
        {
            "sample_id": ["s1"],
            "timestamp": ["2020-01-01T10:00:00+00:00"],
            "review_outcome": ["valid_pattern"],
            "review_confidence": ["high"],
            "human_rationale_zh": ["下影线拒绝明显"],
            "human_counterexample_zh": ["若无结构支撑则无效"],
            "human_uncertainty_reason_zh": [""],
            "human_context_notes_zh": ["伦敦时段波动增强"],
            "human_pattern_3_feedback_zh": ["P3 形态支持"],
            "human_market_8_feedback_zh": ["M8 节奏支持"],
            "human_market_24_feedback_zh": ["M24 小波段支持"],
            "human_market_128_feedback_zh": ["M128 大背景中性偏支持"],
            "human_local_structure_feedback_zh": ["Local 结构支撑明确"],
        }
    )
    df.to_csv(path, index=False)


def test_llm_artifacts_ready_and_review_merge(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    clean = tmp_path / "clean.csv"
    comp = tmp_path / "completed.csv"
    policy = tmp_path / "policy.md"
    _batch(batch)
    _clean_view(clean)
    _completed(comp)
    policy.write_text("language policy", encoding="utf-8")

    artifacts, report = build_llm_review_artifacts_report(
        batch_csv=batch,
        clean_view_csv=clean,
        completed_csv=comp,
        policy_doc=policy,
    )
    assert report["report_status"] == "llm_review_artifacts_ready"
    assert report["artifact_row_count"] == 2
    assert report["reviewed_row_count"] == 1
    assert report["schema_key_language_check"] == "pass"
    row = artifacts[0]
    assert row["language_policy"]["runtime_language"] == "en"
    assert row["language_policy"]["semantic_language"] == "zh"
    assert "trade_signal" in row["future_llm_boundary"]["forbidden_outputs"]
    assert row["human_review"]["human_rationale_zh"] == "下影线拒绝明显"
    assert row["multi_layer_evidence"]["human_pattern_3_feedback_zh"] == "P3 形态支持"
    assert row["multi_layer_evidence"]["human_local_structure_feedback_zh"] == "Local 结构支撑明确"


def test_llm_artifacts_work_when_completed_missing(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    clean = tmp_path / "clean.csv"
    policy = tmp_path / "policy.md"
    _batch(batch)
    _clean_view(clean)
    policy.write_text("language policy", encoding="utf-8")

    artifacts, report = build_llm_review_artifacts_report(
        batch_csv=batch,
        clean_view_csv=clean,
        completed_csv=tmp_path / "missing.csv",
        policy_doc=policy,
    )
    assert report["report_status"] == "llm_review_artifacts_ready"
    assert report["reviewed_row_count"] == 0
    assert artifacts[0]["human_review"]["human_label"] == "not_reviewed"


def test_llm_artifacts_jsonl_output(tmp_path: Path) -> None:
    batch = tmp_path / "batch.csv"
    clean = tmp_path / "clean.csv"
    comp = tmp_path / "completed.csv"
    policy = tmp_path / "policy.md"
    out_jsonl = tmp_path / "artifacts.jsonl"
    _batch(batch)
    _clean_view(clean)
    _completed(comp)
    policy.write_text("language policy", encoding="utf-8")
    artifacts, _ = build_llm_review_artifacts_report(
        batch_csv=batch,
        clean_view_csv=clean,
        completed_csv=comp,
        policy_doc=policy,
    )
    write_artifacts_jsonl(out_jsonl, artifacts)
    lines = [line for line in out_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert "human_rationale_zh" in row["human_review"]
    assert "human_counterexample_zh" in row["human_review"]
    assert "multi_layer_evidence" in row
    assert "human_market_8_feedback_zh" in row["multi_layer_evidence"]
