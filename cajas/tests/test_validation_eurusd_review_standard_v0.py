"""Tests for EURUSD human-governed review standard v0 validation."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_review_standard_v0 import build_review_standard_v0_report


def _write_examples(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")


def test_review_standard_v0_ready(tmp_path: Path) -> None:
    standard = tmp_path / "standard.md"
    examples = tmp_path / "examples.jsonl"
    policy = tmp_path / "policy.md"
    policy.write_text("ok", encoding="utf-8")
    standard.write_text(
        "refer: eurusd_review_language_policy.md\nforbidden: trade_signal entry exit position_size",
        encoding="utf-8",
    )
    _write_examples(
        examples,
        [
            {
                "example_id": "e1",
                "standard_version": "eurusd_15m_review_standard_v0",
                "candidate_type": "lower_wick_rejection_candidate",
                "decision": "valid",
                "confidence": "medium",
                "scenario_tags": ["wick", "trend_context"],
                "rationale_zh": "理由",
                "counter_observation_zh": "反证",
                "uncertainty_reason_zh": "",
                "context_notes_zh": "备注",
                "forbidden_trade_output_present": False,
            },
            {
                "example_id": "e2",
                "standard_version": "eurusd_15m_review_standard_v0",
                "candidate_type": "upper_wick_rejection_candidate",
                "decision": "invalid",
                "confidence": "high",
                "scenario_tags": ["false_positive"],
                "rationale_zh": "理由",
                "counter_observation_zh": "反证",
                "uncertainty_reason_zh": "",
                "context_notes_zh": "备注",
                "forbidden_trade_output_present": False,
            },
            {
                "example_id": "e3",
                "standard_version": "eurusd_15m_review_standard_v0",
                "candidate_type": "compression_cluster_candidate",
                "decision": "uncertain",
                "confidence": "high",
                "scenario_tags": ["gap_caveat"],
                "rationale_zh": "理由",
                "counter_observation_zh": "反证",
                "uncertainty_reason_zh": "不确定",
                "context_notes_zh": "备注",
                "forbidden_trade_output_present": False,
            },
        ],
    )
    report = build_review_standard_v0_report(standard_doc=standard, example_jsonl=examples, language_policy_doc=policy)
    assert report["status"] == "review_standard_v0_ready"
    assert report["all_keys_english"] is True
    assert report["missing_decisions"] == []


def test_review_standard_v0_blocked_on_forbidden_or_missing(tmp_path: Path) -> None:
    standard = tmp_path / "standard.md"
    examples = tmp_path / "examples.jsonl"
    policy = tmp_path / "policy.md"
    policy.write_text("ok", encoding="utf-8")
    standard.write_text("eurusd_review_language_policy.md", encoding="utf-8")
    _write_examples(
        examples,
        [
            {
                "example_id": "bad",
                "standard_version": "eurusd_15m_review_standard_v0",
                "candidate_type": "x",
                "decision": "valid",
                "confidence": "low",
                "scenario_tags": ["wick"],
                "rationale_zh": "理由",
                "counter_observation_zh": "反证",
                "uncertainty_reason_zh": "",
                "context_notes_zh": "备注",
                "forbidden_trade_output_present": True,
            }
        ],
    )
    report = build_review_standard_v0_report(standard_doc=standard, example_jsonl=examples, language_policy_doc=policy)
    assert report["status"] == "blocked"
    assert report["forbidden_output_violation_count"] > 0
