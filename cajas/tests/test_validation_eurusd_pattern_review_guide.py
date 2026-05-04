"""Test EURUSD pattern review guide."""
import json
from pathlib import Path

import pytest

from cajas.reports.validation_eurusd_pattern_review_guide import (
    build_review_guide_report,
    format_review_guide_markdown
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


def test_guide_report_ready(temp_dir, label_schema):
    report = build_review_guide_report(label_schema_json=label_schema)
    
    assert report["status"] == "ready"
    assert report["schema_version"] == "eurusd_15m_pattern_review_v1"
    assert "guide_sections" in report
    assert report["recommendation"] == "start_batch_review"


def test_guide_markdown_no_trading_signals(temp_dir, label_schema):
    report = build_review_guide_report(label_schema_json=label_schema)
    md = format_review_guide_markdown(report)
    
    assert "No trading signals" in md
    assert "No order generation" in md
    assert "NOT trading actions" in md


def test_guide_missing_schema(temp_dir):
    report = build_review_guide_report(label_schema_json=temp_dir / "missing.json")
    
    assert report["status"] == "blocked"
    assert "label_schema_missing" in report["reason"]
