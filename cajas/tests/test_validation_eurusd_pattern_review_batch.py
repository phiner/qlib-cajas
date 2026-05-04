"""Test EURUSD pattern review batch builder."""
import json
from pathlib import Path

import pandas as pd
import pytest

from cajas.reports.validation_eurusd_pattern_review_batch import (
    build_review_batch_report,
    diversify_review_samples,
    summarize_sample_time_diversity,
)


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def label_schema(temp_dir):
    schema = {
        "schema_version": "eurusd_15m_pattern_review_v1",
        "status": "ready"
    }
    path = temp_dir / "schema.json"
    path.write_text(json.dumps(schema))
    return path


@pytest.fixture
def template_csv(temp_dir):
    rows = []
    base_ts = pd.Timestamp("2020-01-01T00:00:00+00:00")
    for i in range(100):
        ctype = f"type_{i % 10}"
        rows.append({
            "sample_id": f"s{i:03d}",
            "timestamp": (base_ts + pd.Timedelta(minutes=15 * i)).isoformat(),
            "candidate_type": ctype,
            "confidence_score": 0.5 + (i % 10) * 0.05,
            "review_priority": "low" if i % 2 == 0 else "high",
            "review_status": "pending"
        })
    df = pd.DataFrame(rows)
    path = temp_dir / "template.csv"
    df.to_csv(path, index=False)
    return path


def test_batch_builder_creates_balanced_batch(temp_dir, template_csv, label_schema):
    output_csv = temp_dir / "batch.csv"
    output_jsonl = temp_dir / "batch.jsonl"
    
    report = build_review_batch_report(
        template_csv=template_csv,
        label_schema_json=label_schema,
        batch_id="test_batch_001",
        batch_size=100,
        per_type_target=10,
        output_batch_csv=output_csv,
        output_batch_jsonl=output_jsonl
    )
    
    assert report["status"] in {"ready", "watch"}
    assert report["batch_row_count"] == 100
    assert report["candidate_type_count"] == 10
    assert "diversification_settings" in report
    assert report["diversification_settings"]["min_gap_bars_between_samples"] == 8
    assert "diversity_summary" in report
    assert output_csv.exists()
    assert output_jsonl.exists()


def test_batch_builder_blocks_on_forbidden_columns(temp_dir, label_schema):
    df = pd.DataFrame({
        "timestamp": ["2020-01-01T00:00:00+00:00"],
        "candidate_type": ["test"],
        "buy": [1],
        "sell": [0]
    })
    template_csv = temp_dir / "bad_template.csv"
    df.to_csv(template_csv, index=False)
    
    output_csv = temp_dir / "batch.csv"
    output_jsonl = temp_dir / "batch.jsonl"
    
    report = build_review_batch_report(
        template_csv=template_csv,
        label_schema_json=label_schema,
        batch_id="test_batch",
        batch_size=10,
        per_type_target=5,
        output_batch_csv=output_csv,
        output_batch_jsonl=output_jsonl
    )
    
    assert report["status"] == "blocked"
    assert "forbidden_trading_columns_detected" in report["reason"]


def test_batch_builder_missing_template(temp_dir, label_schema):
    output_csv = temp_dir / "batch.csv"
    output_jsonl = temp_dir / "batch.jsonl"
    
    report = build_review_batch_report(
        template_csv=temp_dir / "missing.csv",
        label_schema_json=label_schema,
        batch_id="test_batch",
        batch_size=10,
        per_type_target=5,
        output_batch_csv=output_csv,
        output_batch_jsonl=output_jsonl
    )
    
    assert report["status"] == "blocked"
    assert "template_csv_missing" in report["reason"]


def test_diversify_review_samples_gap_and_day_cap():
    rows = []
    base_ts = pd.Timestamp("2020-01-01 00:00:00+00:00")
    for i in range(40):
        rows.append(
            {
                "sample_id": f"s{i:03d}",
                "timestamp": base_ts + pd.Timedelta(minutes=120 * i),
                "candidate_type": "type_a" if i % 2 == 0 else "type_b",
                "confidence_score": 0.8,
                "review_priority": "high",
            }
        )
    df = pd.DataFrame(rows)
    out = diversify_review_samples(df, target_count=12, min_gap_bars=8, max_samples_per_day=8, balanced_by_candidate_type=True)
    assert len(out) == 12
    ts = pd.to_datetime(out["timestamp"], utc=True).sort_values().reset_index(drop=True)
    gaps = (ts.diff().dropna().dt.total_seconds() / 60.0).tolist()
    assert min(gaps) >= 120


def test_diversify_review_samples_graceful_fallback_and_determinism():
    rows = []
    for i in range(12):
        rows.append(
            {
                "sample_id": f"s{i:03d}",
                "timestamp": pd.Timestamp("2020-01-01 00:00:00+00:00") + pd.Timedelta(minutes=15 * i),
                "candidate_type": "type_a",
                "confidence_score": 0.5,
                "review_priority": "high",
            }
        )
    df = pd.DataFrame(rows)
    out1 = diversify_review_samples(df, target_count=10, min_gap_bars=8, max_samples_per_day=2, balanced_by_candidate_type=True)
    out2 = diversify_review_samples(df, target_count=10, min_gap_bars=8, max_samples_per_day=2, balanced_by_candidate_type=True)
    assert len(out1) == 10
    assert out1["sample_id"].tolist() == out2["sample_id"].tolist()


def test_summarize_sample_time_diversity_clusters():
    df = pd.DataFrame(
        {
            "sample_id": ["a", "b", "c"],
            "timestamp": [
                "2020-01-01T00:00:00+00:00",
                "2020-01-01T00:15:00+00:00",
                "2020-01-03T00:00:00+00:00",
            ],
        }
    )
    summary = summarize_sample_time_diversity(df)
    assert summary["sample_count"] == 3
    assert summary["unique_days"] == 2
    assert summary["cluster_warning_count"] >= 1
    assert summary["status"] == "warning"
