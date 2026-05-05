"""Tests for EURUSD real LLM integration readiness checklist/report."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_real_llm_integration_readiness import (
    build_real_llm_integration_readiness_report,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_readiness_ready_for_explicit_approval(tmp_path: Path) -> None:
    lb = tmp_path / "lb.json"
    zh = tmp_path / "zh.json"
    art = tmp_path / "art.json"
    sec = tmp_path / "sec.json"
    std = tmp_path / "std.json"
    fixture = tmp_path / "fixture.json"
    _write_json(lb, {"status": "language_boundary_ready"})
    _write_json(zh, {"status": "zh_rationale_fields_ready"})
    _write_json(art, {"report_status": "llm_review_artifacts_ready"})
    _write_json(sec, {"report_status": "llm_second_review_protocol_ready"})
    _write_json(std, {"status": "review_standard_v0_ready"})
    _write_json(fixture, {"report_status": "llm_second_review_outputs_ready", "automation_readiness_status": "not_ready"})
    doc = tmp_path / "doc.md"
    doc.write_text(
        "no live llm api calls\ntrade_signal entry exit position_size\nhuman audit\nexplicit approval\noffline no live llm",
        encoding="utf-8",
    )
    scan = tmp_path / "scan.py"
    scan.write_text("def noop():\n    return 'offline only'\n", encoding="utf-8")
    report = build_real_llm_integration_readiness_report(
        language_boundary_json=lb,
        zh_rationale_json=zh,
        llm_artifacts_json=art,
        llm_second_review_json=sec,
        standard_v0_json=std,
        fixture_drill_json=fixture,
        docs_to_check=[doc],
        files_to_scan_for_live_llm=[scan],
    )
    assert report["status"] == "ready_for_explicit_approval"


def test_readiness_not_ready_when_prereq_missing(tmp_path: Path) -> None:
    lb = tmp_path / "lb.json"
    _write_json(lb, {"status": "language_boundary_ready"})
    doc = tmp_path / "doc.md"
    doc.write_text("trade_signal entry exit position_size human audit explicit approval no live llm api calls", encoding="utf-8")
    report = build_real_llm_integration_readiness_report(
        language_boundary_json=lb,
        zh_rationale_json=tmp_path / "missing_zh.json",
        llm_artifacts_json=tmp_path / "missing_art.json",
        llm_second_review_json=tmp_path / "missing_sec.json",
        standard_v0_json=tmp_path / "missing_std.json",
        fixture_drill_json=None,
        docs_to_check=[doc],
        files_to_scan_for_live_llm=[],
    )
    assert report["status"] == "not_ready"


def test_readiness_blocked_when_live_llm_detected(tmp_path: Path) -> None:
    lb = tmp_path / "lb.json"
    zh = tmp_path / "zh.json"
    art = tmp_path / "art.json"
    sec = tmp_path / "sec.json"
    std = tmp_path / "std.json"
    _write_json(lb, {"status": "language_boundary_ready"})
    _write_json(zh, {"status": "zh_rationale_fields_ready"})
    _write_json(art, {"report_status": "llm_review_artifacts_ready"})
    _write_json(sec, {"report_status": "llm_second_review_protocol_ready"})
    _write_json(std, {"status": "review_standard_v0_ready"})
    doc = tmp_path / "doc.md"
    doc.write_text("trade_signal entry exit position_size human audit explicit approval no live llm api calls", encoding="utf-8")
    scan = tmp_path / "live.py"
    scan.write_text("client = OpenAI(api_key='x')\n", encoding="utf-8")
    report = build_real_llm_integration_readiness_report(
        language_boundary_json=lb,
        zh_rationale_json=zh,
        llm_artifacts_json=art,
        llm_second_review_json=sec,
        standard_v0_json=std,
        fixture_drill_json=None,
        docs_to_check=[doc],
        files_to_scan_for_live_llm=[scan],
    )
    assert report["status"] == "blocked"
    assert report["live_llm_integration_scan"]["detected"] is True
