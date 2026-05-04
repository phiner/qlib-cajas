import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_review_feedback import build_validation_eurusd_pattern_review_feedback


def _write_schema(path: Path) -> Path:
    payload = {
        "schema_version": "eurusd_15m_pattern_review_v1",
        "allowed_values": {
            "human_pattern_label": ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
            "market_context": ["trend", "range", "transition", "high_volatility", "low_volatility", "unclear"],
            "direction_context": ["up", "down", "sideways", "mixed", "unclear"],
            "review_status": ["pending", "reviewed", "skipped"],
        },
        "numeric_ranges": {
            "structure_quality": {"min": 1, "max": 5},
            "follow_through_quality": {"min": 1, "max": 5},
            "review_confidence": {"min": 1, "max": 5},
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_template(path: Path) -> Path:
    df = pd.DataFrame(
        [
            {"sample_id": "s1", "timestamp": "2025-01-01T00:00:00+00:00", "candidate_type": "compression_candidate"},
            {"sample_id": "s2", "timestamp": "2025-01-01T00:15:00+00:00", "candidate_type": "expansion_candidate"},
        ]
    )
    df.to_csv(path, index=False)
    return path


def test_feedback_awaiting_input_when_completed_missing(tmp_path: Path) -> None:
    t = _write_template(tmp_path / "template.csv")
    s = _write_schema(tmp_path / "schema.json")
    payload = build_validation_eurusd_pattern_review_feedback(
        template_csv=t,
        completed_review_csv=tmp_path / "missing.csv",
        label_schema=s,
    )
    assert payload["status"] == "awaiting_review_input"
    assert payload["blocking"] is False
    assert payload["pending_count"] == 2


def test_feedback_ready_on_valid_completed_fixture(tmp_path: Path) -> None:
    t = _write_template(tmp_path / "template.csv")
    s = _write_schema(tmp_path / "schema.json")
    c = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "timestamp": "2025-01-01T00:00:00+00:00",
                "candidate_type": "compression_candidate",
                "schema_version": "eurusd_15m_pattern_review_v1",
                "human_pattern_label": "valid_pattern",
                "market_context": "range",
                "direction_context": "sideways",
                "structure_quality": 4,
                "follow_through_quality": 3,
                "review_confidence": 4,
                "review_status": "reviewed",
            }
        ]
    )
    cp = tmp_path / "completed.csv"
    c.to_csv(cp, index=False)
    payload = build_validation_eurusd_pattern_review_feedback(template_csv=t, completed_review_csv=cp, label_schema=s)
    assert payload["status"] in {"ready", "watch"}
    assert payload["reviewed_count"] == 1


def test_feedback_blocked_invalid_enum(tmp_path: Path) -> None:
    t = _write_template(tmp_path / "template.csv")
    s = _write_schema(tmp_path / "schema.json")
    c = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "timestamp": "2025-01-01T00:00:00+00:00",
                "candidate_type": "compression_candidate",
                "schema_version": "eurusd_15m_pattern_review_v1",
                "human_pattern_label": "bad_value",
                "market_context": "range",
                "direction_context": "sideways",
                "structure_quality": 4,
                "follow_through_quality": 3,
                "review_confidence": 4,
                "review_status": "reviewed",
            }
        ]
    )
    cp = tmp_path / "completed.csv"
    c.to_csv(cp, index=False)
    payload = build_validation_eurusd_pattern_review_feedback(template_csv=t, completed_review_csv=cp, label_schema=s)
    assert payload["status"] == "blocked"
    assert payload["invalid_row_count"] > 0


def test_feedback_duplicate_sample_id_reported(tmp_path: Path) -> None:
    t = _write_template(tmp_path / "template.csv")
    s = _write_schema(tmp_path / "schema.json")
    c = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "timestamp": "2025-01-01T00:00:00+00:00",
                "candidate_type": "compression_candidate",
                "schema_version": "eurusd_15m_pattern_review_v1",
                "human_pattern_label": "valid_pattern",
                "market_context": "range",
                "direction_context": "sideways",
                "structure_quality": 4,
                "follow_through_quality": 3,
                "review_confidence": 4,
                "review_status": "reviewed",
            },
            {
                "sample_id": "s1",
                "timestamp": "2025-01-01T00:15:00+00:00",
                "candidate_type": "expansion_candidate",
                "schema_version": "eurusd_15m_pattern_review_v1",
                "human_pattern_label": "weak_pattern",
                "market_context": "transition",
                "direction_context": "up",
                "structure_quality": 3,
                "follow_through_quality": 3,
                "review_confidence": 3,
                "review_status": "reviewed",
            },
        ]
    )
    cp = tmp_path / "completed.csv"
    c.to_csv(cp, index=False)
    payload = build_validation_eurusd_pattern_review_feedback(template_csv=t, completed_review_csv=cp, label_schema=s)
    assert payload["duplicate_sample_id_count"] >= 1


def test_feedback_blocked_forbidden_columns(tmp_path: Path) -> None:
    t = _write_template(tmp_path / "template.csv")
    s = _write_schema(tmp_path / "schema.json")
    c = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "timestamp": "2025-01-01T00:00:00+00:00",
                "candidate_type": "compression_candidate",
                "schema_version": "eurusd_15m_pattern_review_v1",
                "human_pattern_label": "valid_pattern",
                "market_context": "range",
                "direction_context": "sideways",
                "structure_quality": 4,
                "follow_through_quality": 3,
                "review_confidence": 4,
                "review_status": "reviewed",
                "signal": 1,
            }
        ]
    )
    cp = tmp_path / "completed.csv"
    c.to_csv(cp, index=False)
    payload = build_validation_eurusd_pattern_review_feedback(template_csv=t, completed_review_csv=cp, label_schema=s)
    assert payload["status"] == "blocked"
