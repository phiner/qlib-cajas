from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_qlib_adapter_contract import build_market_state_qlib_adapter_contract_report


def test_qlib_adapter_contract_ready(tmp_path: Path) -> None:
    csv = tmp_path / "state.csv"
    pd.DataFrame([{
        "timestamp": "2025-01-01T00:00:00+00:00",
        "symbol": "EURUSD",
        "micro_pattern_event_3": "micro_noise",
        "short_term_state_8": "sideways",
        "mid_term_state_24": "sideways",
        "long_term_state_128": "sideways",
        "return_8": 0.0,
        "return_24": 0.0,
        "return_128": 0.0,
        "local_structure_state": "range_chop",
        "structure_confidence": "low",
    }]).to_csv(csv, index=False)
    trial = tmp_path / "trial.json"
    trial.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    report = build_market_state_qlib_adapter_contract_report(csv, trial)
    assert report["report_status"] == "qlib_adapter_contract_ready"
