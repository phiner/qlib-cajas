import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_clean_dataset_view import build_validation_eurusd_clean_dataset_view


def _write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_clean_view_removes_quarantined_rows(tmp_path: Path) -> None:
    raw = _write_csv(
        tmp_path / "raw.csv",
        "\n".join(
            [
                "Time (UTC),Open,High,Low,Close",
                "2025.01.01 00:00:00,1.1000,1.1005,1.0995,1.1002",
                "2025.01.01 00:15:00,1.1002,1.0990,1.0997,1.1003",
                "2025.01.01 00:30:00,1.1003,1.1008,1.0998,1.1004",
            ]
        ),
    )
    triage = _write_json(
        tmp_path / "triage.json",
        {
            "anomalies": [
                {
                    "source_file": str(raw),
                    "source_row_index": 1,
                    "violated_constraints": ["high_lt_close"],
                }
            ]
        },
    )

    clean_csv = tmp_path / "clean.csv"
    quarantine_csv = tmp_path / "quarantine.csv"
    payload = build_validation_eurusd_clean_dataset_view(
        input_paths=[raw],
        anomaly_triage_report=triage,
        output_clean_csv=clean_csv,
        output_quarantine_csv=quarantine_csv,
        min_rows=1,
    )
    assert payload["quarantined_row_count"] == 1
    assert payload["clean_row_count"] == 2
    assert payload["status"] in {"ready", "watch"}

    q_df = pd.read_csv(quarantine_csv)
    c_df = pd.read_csv(clean_csv)
    assert len(q_df) == 1
    assert len(c_df) == 2


def test_clean_view_does_not_mutate_raw_input(tmp_path: Path) -> None:
    raw = _write_csv(
        tmp_path / "raw.csv",
        "\n".join(
            [
                "Time (UTC),Open,High,Low,Close",
                "2025.01.01 00:00:00,1.1000,1.1005,1.0995,1.1002",
            ]
        ),
    )
    before = raw.read_text(encoding="utf-8")
    triage = _write_json(tmp_path / "triage.json", {"anomalies": []})
    _ = build_validation_eurusd_clean_dataset_view(
        input_paths=[raw],
        anomaly_triage_report=triage,
        output_clean_csv=tmp_path / "clean.csv",
        output_quarantine_csv=tmp_path / "quarantine.csv",
        min_rows=1,
    )
    after = raw.read_text(encoding="utf-8")
    assert before == after
