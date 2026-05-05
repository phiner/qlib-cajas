import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_review_completion_closure import (
    build_review_completion_closure_report,
)
from cajas.research.eurusd_review_schema import default_review_values


def _schema(path: Path) -> Path:
    payload = {
        "schema_version": "eurusd_15m_pattern_review_v3",
        "compatible_schema_versions": [
            "eurusd_15m_pattern_review_v1",
            "eurusd_15m_pattern_review_v2",
            "eurusd_15m_pattern_review_v3",
        ],
        "allowed_values": {
            "human_label": ["valid_pattern", "weak_pattern", "false_positive", "not_enough_context", "unclear", "not_reviewed"],
            "human_confidence": ["high", "medium", "low", "unclear", "not_reviewed"],
            "market_context": ["uptrend", "downtrend", "range", "compression", "expansion", "transition", "choppy", "unclear", "not_reviewed"],
            "trend_direction": ["up", "down", "sideways", "mixed", "unclear", "not_reviewed"],
            "review_outcome": ["valid_pattern", "weak_pattern", "false_positive", "not_enough_context", "unclear", "not_reviewed"],
            "review_confidence": ["high", "medium", "low", "unclear", "not_reviewed"],
        },
        "legacy_allowed_values": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _batch(path: Path, ids: list[str]) -> Path:
    pd.DataFrame({"sample_id": ids, "timestamp": ["2020-01-01T00:00:00+00:00"] * len(ids)}).to_csv(path, index=False)
    return path


def _completed(path: Path, ids: list[str]) -> Path:
    rows = []
    defaults = default_review_values()
    for sid in ids:
        row = {"sample_id": sid, **defaults}
        row.update(
            {
                "human_label": "valid_pattern",
                "review_outcome": "valid_pattern",
                "human_confidence": "high",
                "review_confidence": "high",
                "review_updated_at_utc": "2026-05-04T00:00:00+00:00",
            }
        )
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_closure_awaiting_review_input(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1", "s2"])
    schema = _schema(tmp_path / "schema.json")
    report = build_review_completion_closure_report(
        batch_csv=batch,
        completed_csv=tmp_path / "missing_completed.csv",
        label_schema_json=schema,
        audit_jsonl=tmp_path / "events.jsonl",
    )
    assert report["status"] == "awaiting_review_input"
    assert report["pending_count"] == 2


def test_closure_in_progress(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1", "s2", "s3"])
    schema = _schema(tmp_path / "schema.json")
    completed = _completed(tmp_path / "completed.csv", ["s1"])
    report = build_review_completion_closure_report(
        batch_csv=batch,
        completed_csv=completed,
        label_schema_json=schema,
        audit_jsonl=tmp_path / "events.jsonl",
    )
    assert report["review_state"] == "in_progress"
    assert report["completed_count"] == 1
    assert report["pending_count"] == 2
    assert report["next_action"] == "continue_human_review"


def test_closure_ready_for_summary_with_valid_jsonl(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1", "s2"])
    schema = _schema(tmp_path / "schema.json")
    completed = _completed(tmp_path / "completed.csv", ["s1", "s2"])
    jsonl = tmp_path / "events.jsonl"
    jsonl.write_text(
        "\n".join(
            [
                json.dumps({"sample_id": "s1", "action_type": "save"}),
                json.dumps({"sample_id": "s2", "action_type": "save_and_next"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_review_completion_closure_report(
        batch_csv=batch, completed_csv=completed, label_schema_json=schema, audit_jsonl=jsonl
    )
    assert report["status"] == "ready_for_summary"
    assert report["next_action"] == "run_review_summary"


def test_closure_warning_when_jsonl_missing(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1"])
    schema = _schema(tmp_path / "schema.json")
    completed = _completed(tmp_path / "completed.csv", ["s1"])
    report = build_review_completion_closure_report(
        batch_csv=batch,
        completed_csv=completed,
        label_schema_json=schema,
        audit_jsonl=tmp_path / "missing_events.jsonl",
    )
    assert report["status"] == "warning"
    assert report["blocking"] is False


def test_closure_blocked_on_duplicate_sample_ids(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1"])
    schema = _schema(tmp_path / "schema.json")
    completed = _completed(tmp_path / "completed.csv", ["s1", "s1"])
    report = build_review_completion_closure_report(
        batch_csv=batch, completed_csv=completed, label_schema_json=schema
    )
    assert report["status"] == "blocked"
    assert report["duplicate_completed_sample_ids"] == ["s1"]


def test_closure_blocked_missing_required_field(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1"])
    schema = _schema(tmp_path / "schema.json")
    pd.DataFrame({"sample_id": ["s1"]}).to_csv(tmp_path / "completed.csv", index=False)
    report = build_review_completion_closure_report(
        batch_csv=batch, completed_csv=tmp_path / "completed.csv", label_schema_json=schema
    )
    assert report["status"] == "blocked"
    assert "review_updated_at_utc" in report["missing_required_review_fields"]


def test_closure_warning_malformed_jsonl_and_mismatch(tmp_path: Path) -> None:
    batch = _batch(tmp_path / "batch.csv", ["s1"])
    schema = _schema(tmp_path / "schema.json")
    completed = _completed(tmp_path / "completed.csv", ["s1"])
    jsonl = tmp_path / "events.jsonl"
    jsonl.write_text('{"sample_id":"s9"}\nnot-json\n', encoding="utf-8")
    report = build_review_completion_closure_report(
        batch_csv=batch, completed_csv=completed, label_schema_json=schema, audit_jsonl=jsonl
    )
    assert report["status"] == "warning"
    assert report["jsonl_malformed_lines"]
    assert report["completed_csv_samples_without_jsonl"] == ["s1"]
    assert report["jsonl_samples_without_completed_csv"] == ["s9"]
