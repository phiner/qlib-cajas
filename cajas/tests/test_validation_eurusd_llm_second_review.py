"""Tests for offline EURUSD LLM second-review protocol/output validation."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_llm_second_review import build_llm_second_review_report


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")


def _sample_rows() -> list[dict]:
    return [
        {
            "artifact_version": "eurusd_llm_review_sample_v0",
            "sample_id": "sample_001",
            "human_review": {"human_label": "valid_pattern", "human_confidence": "high"},
        },
        {
            "artifact_version": "eurusd_llm_review_sample_v0",
            "sample_id": "sample_002",
            "human_review": {"human_label": "false_positive", "human_confidence": "high"},
        },
        {
            "artifact_version": "eurusd_llm_review_sample_v0",
            "sample_id": "sample_003",
            "human_review": {"human_label": "valid_pattern", "human_confidence": "high"},
        },
    ]


def test_protocol_ready_when_outputs_absent(tmp_path: Path) -> None:
    sample_jsonl = tmp_path / "samples.jsonl"
    _write_jsonl(sample_jsonl, _sample_rows())
    report = build_llm_second_review_report(sample_artifacts_jsonl=sample_jsonl, llm_outputs_jsonl=tmp_path / "missing.jsonl")
    assert report["report_status"] == "llm_second_review_protocol_ready"
    assert report["automation_readiness_status"] == "not_evaluated"
    assert report["llm_review_row_count"] == 0


def test_outputs_ready_with_fixture_metrics(tmp_path: Path) -> None:
    sample_jsonl = tmp_path / "samples.jsonl"
    out_jsonl = tmp_path / "outputs.jsonl"
    _write_jsonl(sample_jsonl, _sample_rows())
    _write_jsonl(
        out_jsonl,
        [
            {
                "artifact_version": "eurusd_llm_second_review_v0",
                "source_artifact_version": "eurusd_llm_review_sample_v0",
                "sample_id": "sample_001",
                "standard_version": "eurusd_15m_review_standard_v0",
                "llm_reviewer_role": "second_reviewer",
                "llm_pattern_validity": "valid",
                "llm_confidence": "medium",
                "supporting_observations_zh": ["结构与确认一致"],
                "counter_observations_zh": [],
                "uncertainty_reason_zh": "",
                "requires_human_review": False,
                "possible_standard_gap_zh": "",
                "forbidden_trade_output_present": False,
                "raw_model_name": "offline-fixture",
                "review_created_at_utc": "2026-05-05T00:00:00Z",
            },
            {
                "artifact_version": "eurusd_llm_second_review_v0",
                "source_artifact_version": "eurusd_llm_review_sample_v0",
                "sample_id": "sample_002",
                "standard_version": "eurusd_15m_review_standard_v0",
                "llm_reviewer_role": "second_reviewer",
                "llm_pattern_validity": "uncertain",
                "llm_confidence": "high",
                "supporting_observations_zh": ["缺少连续确认"],
                "counter_observations_zh": ["反向扫流动性后回收"],
                "uncertainty_reason_zh": "上下文不足",
                "requires_human_review": True,
                "possible_standard_gap_zh": "弱形态与不确定边界定义不足",
                "forbidden_trade_output_present": False,
                "raw_model_name": "offline-fixture",
                "review_created_at_utc": "2026-05-05T00:01:00Z",
            },
        ],
    )
    report = build_llm_second_review_report(sample_artifacts_jsonl=sample_jsonl, llm_outputs_jsonl=out_jsonl)
    assert report["report_status"] == "llm_second_review_outputs_ready"
    assert report["agreement_count"] == 1
    assert report["disagreement_count"] == 1
    assert report["high_confidence_disagreement_count"] == 1
    assert report["requires_human_review_count"] == 1
    assert report["possible_standard_gap_count"] == 1


def test_blocked_on_invalid_or_forbidden_output(tmp_path: Path) -> None:
    sample_jsonl = tmp_path / "samples.jsonl"
    out_jsonl = tmp_path / "outputs.jsonl"
    _write_jsonl(sample_jsonl, _sample_rows())
    _write_jsonl(
        out_jsonl,
        [
            {
                "artifact_version": "eurusd_llm_second_review_v0",
                "source_artifact_version": "eurusd_llm_review_sample_v0",
                "sample_id": "sample_099",
                "standard_version": "eurusd_15m_review_standard_v0",
                "llm_reviewer_role": "second_reviewer",
                "llm_pattern_validity": "valid",
                "llm_confidence": "high",
                "supporting_observations_zh": [],
                "counter_observations_zh": [],
                "uncertainty_reason_zh": "",
                "requires_human_review": False,
                "possible_standard_gap_zh": "",
                "forbidden_trade_output_present": True,
                "raw_model_name": "offline-fixture",
                "review_created_at_utc": "2026-05-05T00:00:00Z",
            }
        ],
    )
    report = build_llm_second_review_report(sample_artifacts_jsonl=sample_jsonl, llm_outputs_jsonl=out_jsonl)
    assert report["report_status"] == "blocked"
    assert report["unknown_sample_id_count"] == 1
    assert report["forbidden_output_violation_count"] == 1
    assert report["automation_readiness_status"] == "not_ready"


def test_example_fixture_file_is_valid_drill_input(tmp_path: Path) -> None:
    sample_jsonl = tmp_path / "samples.jsonl"
    fixture_path = Path("cajas/data_examples/eurusd_llm_second_review.example.jsonl")
    _write_jsonl(sample_jsonl, _sample_rows())
    report = build_llm_second_review_report(sample_artifacts_jsonl=sample_jsonl, llm_outputs_jsonl=fixture_path)
    assert report["report_status"] == "llm_second_review_outputs_ready"
    assert report["llm_review_row_count"] == 3
    assert report["agreement_count"] == 1
    assert report["disagreement_count"] == 2
    assert report["high_confidence_disagreement_count"] == 2
    assert report["requires_human_review_count"] == 1
    assert report["possible_standard_gap_count"] == 1
