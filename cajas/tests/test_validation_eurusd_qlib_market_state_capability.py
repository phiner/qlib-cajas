"""Tests for EURUSD Qlib market-state capability report."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_qlib_market_state_capability import build_qlib_market_state_capability_report


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_ready_report_with_not_approved_trial(tmp_path: Path) -> None:
    doc = tmp_path / "audit.md"
    doc.write_text("audit", encoding="utf-8")
    trial = _write_json(tmp_path / "trial.json", {"status": "not_approved"})

    report = build_qlib_market_state_capability_report(audit_doc=doc, trial_approval_json=trial)
    assert report["report_status"] == "qlib_market_state_capability_ready"
    assert report["qlib_can_support_market_state_research"] is True
    assert report["requires_cajas_adapter"] is True
    assert report["qlib_core_modification_required"] is False
    assert report["recommended_next_phase"] == "define_market_state_taxonomy_v0_and_feature_contract"


def test_blocked_when_trial_not_not_approved(tmp_path: Path) -> None:
    doc = tmp_path / "audit.md"
    doc.write_text("audit", encoding="utf-8")
    trial = _write_json(tmp_path / "trial.json", {"status": "approved_for_limited_trial"})

    report = build_qlib_market_state_capability_report(audit_doc=doc, trial_approval_json=trial)
    assert report["report_status"] == "blocked"
    assert report["trial_approval_status"] == "approved_for_limited_trial"


def test_blocked_when_doc_missing(tmp_path: Path) -> None:
    trial = _write_json(tmp_path / "trial.json", {"status": "not_approved"})
    report = build_qlib_market_state_capability_report(audit_doc=tmp_path / "missing.md", trial_approval_json=trial)
    assert report["report_status"] == "blocked"
