from pathlib import Path

from cajas.reports.validation_eurusd_ohlc_anomaly_triage import build_validation_eurusd_ohlc_anomaly_triage


def _write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_triage_clean_fixture(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path / "ok.csv",
        "\n".join(
            [
                "Time (UTC),Open,High,Low,Close",
                "2025.01.01 00:00:00,1.1000,1.1005,1.0995,1.1002",
                "2025.01.01 00:15:00,1.1002,1.1007,1.0997,1.1003",
            ]
        ),
    )
    payload = build_validation_eurusd_ohlc_anomaly_triage(input_paths=[p])
    assert payload["status"] == "clean"
    assert payload["total_anomaly_rows"] == 0


def test_triage_blocked_fixture_with_details(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path / "bad.csv",
        "\n".join(
            [
                "Time (UTC),Open,High,Low,Close",
                "2025.01.01 00:00:00,1.1000,1.0990,1.0980,1.1010",
            ]
        ),
    )
    payload = build_validation_eurusd_ohlc_anomaly_triage(input_paths=[p])
    assert payload["status"] == "blocked"
    assert payload["total_anomaly_rows"] >= 1
    row = payload["anomalies"][0]
    assert row["source_row_index"] == 0
    assert row["normalized_timestamp"] is not None
    assert "high_lt_close" in row["violated_constraints"]
