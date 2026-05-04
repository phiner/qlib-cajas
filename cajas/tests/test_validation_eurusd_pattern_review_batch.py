"""Test EURUSD pattern review batch builder."""
import json
from pathlib import Path

import pandas as pd
import pytest

from cajas.reports.validation_eurusd_pattern_review_batch import build_review_batch_report


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
    for i in range(100):
        ctype = f"type_{i % 10}"
        rows.append({
            "timestamp": f"2020-01-{i+1:02d}T00:00:00+00:00",
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
    
    assert report["status"] == "ready"
    assert report["batch_row_count"] == 100
    assert report["candidate_type_count"] == 10
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
