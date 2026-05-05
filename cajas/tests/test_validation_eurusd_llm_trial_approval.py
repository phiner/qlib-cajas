"""Tests for explicit approval record and minimal real LLM trial boundary."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_llm_trial_approval import build_llm_trial_approval_report


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_default_template_not_approved(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    _write(readiness, {"status": "ready_for_explicit_approval"})
    _write(
        approval,
        {
            "approval_status": "not_approved",
            "approved_scope": "eurusd_llm_second_review_trial",
            "allowed_input_artifact": "tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl",
            "allowed_output_artifact": "tmp/eurusd/EURUSD_15m_llm_second_review_trial.jsonl",
            "max_samples": 10,
            "provider": "",
            "model": "",
            "live_api_calls_allowed": False,
            "human_audit_required": True,
            "overwrite_human_labels_allowed": False,
            "trading_outputs_allowed": False,
            "rollback_plan_required": True,
        },
    )
    report = build_llm_trial_approval_report(readiness_json=readiness, approval_json=approval)
    assert report["status"] == "not_approved"


def test_approved_for_limited_trial_when_constraints_met(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    _write(readiness, {"status": "ready_for_explicit_approval"})
    _write(
        approval,
        {
            "approval_status": "approved",
            "approved_scope": "eurusd_llm_second_review_trial",
            "allowed_input_artifact": "tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl",
            "allowed_output_artifact": "tmp/eurusd/EURUSD_15m_llm_second_review_trial.jsonl",
            "max_samples": 5,
            "provider": "provider_x",
            "model": "model_y",
            "live_api_calls_allowed": True,
            "human_audit_required": True,
            "overwrite_human_labels_allowed": False,
            "trading_outputs_allowed": False,
            "rollback_plan_required": True,
        },
    )
    report = build_llm_trial_approval_report(readiness_json=readiness, approval_json=approval)
    assert report["status"] == "approved_for_limited_trial"


def test_blocked_on_dangerous_flags_or_mismatch(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    _write(readiness, {"status": "not_ready"})
    _write(
        approval,
        {
            "approval_status": "approved",
            "approved_scope": "eurusd_llm_second_review_trial",
            "allowed_input_artifact": "tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl",
            "allowed_output_artifact": "",
            "max_samples": 0,
            "provider": "",
            "model": "",
            "live_api_calls_allowed": False,
            "human_audit_required": False,
            "overwrite_human_labels_allowed": True,
            "trading_outputs_allowed": True,
            "rollback_plan_required": False,
        },
    )
    report = build_llm_trial_approval_report(readiness_json=readiness, approval_json=approval)
    assert report["status"] == "blocked"
    assert report["blocking_reasons"]
