"""Tests for fail-closed EURUSD LLM trial runner skeleton."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.research.eurusd_llm_trial_runner import build_eurusd_llm_trial_run_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")


def _sample_rows(count: int = 12) -> list[dict]:
    return [{"artifact_version": "eurusd_llm_review_sample_v0", "sample_id": f"sample_{i:03d}"} for i in range(count)]


def _base_readiness() -> dict:
    return {"status": "ready_for_explicit_approval"}


def _base_approval(**overrides: object) -> dict:
    payload = {
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
    }
    payload.update(overrides)
    return payload


def test_default_template_returns_not_approved(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    output_jsonl = tmp_path / "out.jsonl"
    _write_json(readiness, _base_readiness())
    _write_json(approval, _base_approval())
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=output_jsonl,
    )
    assert report["run_status"] == "not_approved"
    assert report["live_api_calls_attempted"] is False


def test_missing_readiness_blocks(tmp_path: Path) -> None:
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(approval, _base_approval())
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=tmp_path / "missing.json",
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["run_status"] == "blocked"
    assert "missing_readiness_report" in report["blocking_reasons"]


def test_readiness_not_ready_blocks(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(readiness, {"status": "not_ready"})
    _write_json(approval, _base_approval())
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["run_status"] == "blocked"
    assert any(x.startswith("readiness_not_ready_for_explicit_approval") for x in report["blocking_reasons"])


def test_trading_outputs_allowed_blocks(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(readiness, _base_readiness())
    _write_json(approval, _base_approval(trading_outputs_allowed=True))
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["run_status"] == "blocked"
    assert "trading_outputs_must_be_false" in report["blocking_reasons"]


def test_overwrite_human_labels_allowed_blocks(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(readiness, _base_readiness())
    _write_json(approval, _base_approval(overwrite_human_labels_allowed=True))
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["run_status"] == "blocked"
    assert "overwrite_human_labels_must_be_false" in report["blocking_reasons"]


def test_approved_path_reaches_ready_but_no_provider_adapter(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(readiness, _base_readiness())
    _write_json(
        approval,
        _base_approval(
            approval_status="approved",
            provider="provider_x",
            model="model_y",
            live_api_calls_allowed=True,
            max_samples=5,
        ),
    )
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["run_status"] == "ready_but_no_provider_adapter"
    assert report["provider_adapter_available"] is False


def test_sample_cap_is_enforced(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(readiness, _base_readiness())
    _write_json(
        approval,
        _base_approval(
            approval_status="approved",
            provider="provider_x",
            model="model_y",
            live_api_calls_allowed=True,
            max_samples=3,
        ),
    )
    _write_jsonl(samples, _sample_rows(12))

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["selected_sample_count"] == 3


def test_no_live_calls_no_human_mutation_and_no_trading_execution_fields(tmp_path: Path) -> None:
    readiness = tmp_path / "readiness.json"
    approval = tmp_path / "approval.json"
    samples = tmp_path / "samples.jsonl"
    _write_json(readiness, _base_readiness())
    _write_json(approval, _base_approval())
    _write_jsonl(samples, _sample_rows())

    report = build_eurusd_llm_trial_run_report(
        readiness_json=readiness,
        approval_json=approval,
        sample_artifacts_jsonl=samples,
        output_jsonl=tmp_path / "out.jsonl",
    )
    assert report["live_api_calls_attempted"] is False
    assert report["human_labels_mutated"] is False
    assert "trade_signal" not in report
    assert "order" not in report
    assert "position_size" not in report
