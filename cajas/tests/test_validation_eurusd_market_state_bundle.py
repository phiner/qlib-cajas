from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state_bundle import build_market_state_bundle_report


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_bundle_watch_when_manual_labels_awaiting(tmp_path: Path) -> None:
    _write(tmp_path / "validation-eurusd-market-state.json", {"report_status": "market_state_dataset_ready"})
    _write(tmp_path / "validation-eurusd-market-state-calibration.json", {"report_status": "market_state_calibration_ready"})
    _write(tmp_path / "validation-eurusd-micro-pattern-rules.json", {"report_status": "micro_pattern_rules_ready"})
    _write(tmp_path / "validation-eurusd-micro-noise-profile.json", {"report_status": "micro_noise_profile_ready"})
    _write(tmp_path / "validation-eurusd-micro-pattern-review-packet.json", {"report_status": "micro_pattern_review_packet_ready"})
    _write(tmp_path / "validation-eurusd-micro-pattern-manual-labels.json", {"report_status": "awaiting_manual_micro_pattern_labels"})
    _write(tmp_path / "validation-eurusd-micro-pattern-rule-candidates.json", {"report_status": "awaiting_manual_labels"})
    _write(tmp_path / "validation-eurusd-market-state-inspection-packet.json", {"report_status": "market_state_inspection_packet_ready"})
    _write(tmp_path / "validation-tmp-artifact-cleanup-plan.json", {"report_status": "tmp_cleanup_plan_ready"})
    _write(tmp_path / "validation-eurusd-market-state-qlib-adapter-contract.json", {"report_status": "qlib_adapter_contract_ready"})
    _write(tmp_path / "validation-eurusd-market-state-dataset-quality.json", {"report_status": "market_state_dataset_quality_ready"})
    _write(tmp_path / "validation-eurusd-real-llm-integration-readiness.json", {"status": "ready_for_explicit_approval"})
    _write(tmp_path / "validation-eurusd-llm-trial-approval.json", {"approval_status": "not_approved"})

    report = build_market_state_bundle_report(tmp_path / "validation-eurusd-market-state-bundle.json")
    assert report["report_status"] == "market_state_bundle_watch"
    assert report["recommended_next_phase"] == "manual_label_micro_pattern_packet"
