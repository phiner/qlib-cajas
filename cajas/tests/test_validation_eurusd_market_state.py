"""Tests for EURUSD market-state validation report."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from cajas.reports.validation_eurusd_market_state import build_market_state_report


def _input_csv(path: Path, n: int = 220) -> Path:
    ts = pd.date_range("2025-01-01", periods=n, freq="15min", tz="UTC")
    rng = np.random.default_rng(11)
    close = 1.10 + np.cumsum(0.00015 + rng.normal(0.0, 0.00035, size=n))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.00025
    low = np.minimum(open_, close) - 0.00025
    pd.DataFrame({"timestamp": ts, "open": open_, "high": high, "low": low, "close": close}).to_csv(path, index=False)
    return path


def _trial(path: Path, status: str = "not_approved") -> Path:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
    return path


def test_report_ready_on_valid_input(tmp_path: Path) -> None:
    report = build_market_state_report(
        input_csv=_input_csv(tmp_path / "in.csv"),
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        trial_approval_json=_trial(tmp_path / "trial.json"),
    )
    assert report["report_status"] == "market_state_dataset_ready"
    assert report["feature_columns_present"] is True
    assert report["state_columns_present"] is True
    assert report["trading_outputs_excluded"] is True


def test_report_blocked_on_trial_approval_not_not_approved(tmp_path: Path) -> None:
    report = build_market_state_report(
        input_csv=_input_csv(tmp_path / "in.csv"),
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        trial_approval_json=_trial(tmp_path / "trial.json", status="approved_for_limited_trial"),
    )
    assert report["report_status"] == "blocked"
    assert report["trial_approval_status"] == "approved_for_limited_trial"
