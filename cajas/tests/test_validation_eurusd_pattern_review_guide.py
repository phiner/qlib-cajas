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


def test_guide_contains_five_layer_and_candidate_type_clarification(temp_dir, label_schema):
    report = build_review_guide_report(label_schema_json=label_schema)
    md = format_review_guide_markdown(report)

    assert "先看背景，再看位置，再看局部行为，再看确认/失败，最后给人审结论。" in md
    assert "不要只按 candidate_type 判断。" in md
    assert "candidate_type 是系统把样本送进来的原因，不是最终形态名称。" in md
    assert "candidate_type is a system entry tag, not final label truth." in md
    assert "possible_false_breakout_candidate is a structure hypothesis and needs level/context validation." in md
    assert "market_context 保持宽背景，不要塞入冲高回落/触底回升等短期动作。" in md
    assert "recent_move_context" in md
    assert "spike_up_reversal" in md
    assert "spike_down_reversal" in md


def test_guide_does_not_assume_new_gui_fields(temp_dir, label_schema):
    report = build_review_guide_report(label_schema_json=label_schema)
    fields = set(report["guide_sections"]["fields_to_fill"])
    assert "structure_location" not in fields
    assert "local_behavior" not in fields
    assert "confirmation_result" not in fields
    assert "review_outcome" not in fields


def test_guide_missing_schema(temp_dir):
    report = build_review_guide_report(label_schema_json=temp_dir / "missing.json")
    
    assert report["status"] == "blocked"
    assert "label_schema_missing" in report["reason"]
