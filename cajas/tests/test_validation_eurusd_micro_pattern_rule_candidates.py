from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_pattern_rule_candidates import build_micro_pattern_rule_candidates_report


def test_rule_candidates_awaiting_when_manual_missing(tmp_path: Path) -> None:
    manual = tmp_path / "manual.json"
    trial = tmp_path / "trial.json"
    trial.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    report = build_micro_pattern_rule_candidates_report(manual, trial)
    assert report["report_status"] in {"blocked", "awaiting_manual_labels"}
