import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_sampling_source_range import (
    build_validation_eurusd_sampling_source_range,
)


def _write_series_csv(path: Path, timestamps: list[str], ts_col: str = "timestamp") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({ts_col: timestamps, "open": [1.0] * len(timestamps)}).to_csv(path, index=False)


def test_sampling_source_range_full_ready(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    clean = tmp_path / "clean.csv"
    cand = tmp_path / "cand.csv"
    templ = tmp_path / "templ.csv"
    batch = tmp_path / "batch.csv"

    _write_series_csv(
        raw,
        [
            "2020-01-01T00:00:00Z",
            "2021-06-01T00:00:00Z",
            "2022-06-01T00:00:00Z",
            "2023-06-01T00:00:00Z",
            "2024-12-31T00:00:00Z",
        ],
        ts_col="Time (UTC)",
    )
    _write_series_csv(clean, ["2020-01-01T00:00:00Z", "2024-12-31T00:00:00Z"])
    _write_series_csv(cand, ["2020-02-01T00:00:00Z", "2024-10-01T00:00:00Z"])
    _write_series_csv(templ, ["2020-03-01T00:00:00Z", "2024-11-01T00:00:00Z"])
    _write_series_csv(batch, ["2020-04-01T00:00:00Z", "2024-09-01T00:00:00Z"])

    report = build_validation_eurusd_sampling_source_range(
        raw_source_path=raw,
        clean_view_path=clean,
        candidate_path=cand,
        template_path=templ,
        batch_path=batch,
    )
    assert report["status"] == "full_range_ready"
    assert report["likely_truncation_detected"] is False
    assert set(report["year_coverage"]) >= {2020, 2022, 2024}


def test_sampling_source_range_detects_truncation(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    clean = tmp_path / "clean.csv"
    cand = tmp_path / "cand.csv"
    templ = tmp_path / "templ.csv"
    batch = tmp_path / "batch.csv"

    _write_series_csv(raw, ["2020-01-01T00:00:00Z", "2022-06-01T00:00:00Z", "2024-12-31T00:00:00Z"], ts_col="Time (UTC)")
    _write_series_csv(clean, ["2020-01-01T00:00:00Z", "2024-12-31T00:00:00Z"])
    _write_series_csv(cand, ["2020-01-01T00:00:00Z", "2020-01-20T00:00:00Z"])
    _write_series_csv(templ, ["2020-01-01T00:00:00Z", "2020-01-15T00:00:00Z"])
    _write_series_csv(batch, ["2020-01-05T00:00:00Z", "2020-01-25T00:00:00Z"])

    report = build_validation_eurusd_sampling_source_range(
        raw_source_path=raw,
        clean_view_path=clean,
        candidate_path=cand,
        template_path=templ,
        batch_path=batch,
    )
    assert report["status"] == "derived_artifacts_truncated"
    assert report["likely_truncation_detected"] is True
    assert report["coverage_warnings"]


def test_sampling_source_range_missing_raw(tmp_path: Path) -> None:
    report = build_validation_eurusd_sampling_source_range(
        raw_source_path=tmp_path / "missing_raw.csv",
        clean_view_path=tmp_path / "missing_clean.csv",
        candidate_path=tmp_path / "missing_cand.csv",
        template_path=tmp_path / "missing_template.csv",
        batch_path=tmp_path / "missing_batch.csv",
    )
    assert report["status"] == "raw_source_missing"


def test_sampling_source_range_time_utc_format_supported(tmp_path: Path) -> None:
    raw = tmp_path / "raw_dukascopy.csv"
    raw.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "Time (UTC)": ["2020.01.01 00:00:00", "2024.12.31 23:45:00"],
            "Open": [1.1, 1.2],
            "High": [1.11, 1.21],
            "Low": [1.09, 1.19],
            "Close": [1.1, 1.2],
        }
    ).to_csv(raw, index=False)

    report = build_validation_eurusd_sampling_source_range(
        raw_source_path=raw,
        clean_view_path=tmp_path / "missing_clean.csv",
        candidate_path=tmp_path / "missing_cand.csv",
        template_path=tmp_path / "missing_template.csv",
        batch_path=tmp_path / "missing_batch.csv",
    )
    assert report["raw_exists"] is True
    assert report["raw_row_count"] == 2
    assert report["raw_min_timestamp"] is not None
    assert report["raw_max_timestamp"] is not None


def test_sampling_source_range_is_read_only(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    clean = tmp_path / "clean.csv"
    cand = tmp_path / "cand.csv"
    templ = tmp_path / "templ.csv"
    batch = tmp_path / "batch.csv"
    _write_series_csv(raw, ["2020-01-01T00:00:00Z", "2024-12-31T00:00:00Z"], ts_col="Time (UTC)")
    _write_series_csv(clean, ["2020-01-01T00:00:00Z", "2024-12-31T00:00:00Z"])
    _write_series_csv(cand, ["2021-01-01T00:00:00Z"])
    _write_series_csv(templ, ["2021-01-01T00:00:00Z"])
    _write_series_csv(batch, ["2021-01-01T00:00:00Z"])
    before = batch.read_text(encoding="utf-8")

    _ = build_validation_eurusd_sampling_source_range(
        raw_source_path=raw,
        clean_view_path=clean,
        candidate_path=cand,
        template_path=templ,
        batch_path=batch,
    )
    after = batch.read_text(encoding="utf-8")
    assert before == after
