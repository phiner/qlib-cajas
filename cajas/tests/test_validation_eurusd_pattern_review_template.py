import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_review_template import build_validation_eurusd_pattern_review_template


def _prepare(tmp_path: Path) -> tuple[Path, Path]:
    samples = pd.DataFrame(
        [
            {
                "timestamp": "2025-01-01T00:00:00+00:00",
                "candidate_type": "compression_candidate",
                "confidence_score": 0.8,
                "review_priority": "high",
                "reason_codes": "x",
            },
            {
                "timestamp": "2025-01-01T00:15:00+00:00",
                "candidate_type": "expansion_candidate",
                "confidence_score": 0.7,
                "review_priority": "medium",
                "reason_codes": "y",
            },
        ]
    )
    schema = {
        "status": "ready",
        "schema_version": "eurusd_15m_pattern_review_v1",
        "defaults": {
            "human_pattern_label": "unclear",
            "market_context": "unclear",
            "direction_context": "unclear",
            "structure_quality": 3,
            "follow_through_quality": 3,
            "review_confidence": 3,
            "review_notes": "",
            "review_status": "pending",
        },
    }
    sp = tmp_path / "samples.csv"
    lp = tmp_path / "schema.json"
    samples.to_csv(sp, index=False)
    lp.write_text(json.dumps(schema), encoding="utf-8")
    return sp, lp


def test_template_ready_and_row_count(tmp_path: Path) -> None:
    sp, lp = _prepare(tmp_path)
    payload = build_validation_eurusd_pattern_review_template(
        samples_path=sp,
        label_schema_path=lp,
        output_template_csv=tmp_path / "template.csv",
        output_template_jsonl=tmp_path / "template.jsonl",
    )
    assert payload["status"] == "ready"
    assert payload["template_row_count"] == 2


def test_template_contains_schema_and_pending(tmp_path: Path) -> None:
    sp, lp = _prepare(tmp_path)
    out_csv = tmp_path / "template.csv"
    payload = build_validation_eurusd_pattern_review_template(
        samples_path=sp,
        label_schema_path=lp,
        output_template_csv=out_csv,
        output_template_jsonl=tmp_path / "template.jsonl",
    )
    df = pd.read_csv(out_csv)
    assert payload["schema_version_used"] == "eurusd_15m_pattern_review_v1"
    assert (df["review_status"] == "pending").all()


def test_template_excludes_forbidden_columns(tmp_path: Path) -> None:
    sp, lp = _prepare(tmp_path)
    payload = build_validation_eurusd_pattern_review_template(
        samples_path=sp,
        label_schema_path=lp,
        output_template_csv=tmp_path / "template.csv",
        output_template_jsonl=tmp_path / "template.jsonl",
    )
    assert payload["forbidden_trading_column_hits"] == []
