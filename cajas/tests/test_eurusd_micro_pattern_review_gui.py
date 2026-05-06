from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.research.eurusd_micro_pattern_review_gui import (
    default_micro_pattern_label_values,
    load_completed_micro_pattern_labels,
    load_micro_pattern_packet,
    merge_packet_with_completed_labels,
    persist_micro_pattern_label,
    validate_micro_pattern_label_update,
)
from cajas.reports.validation_eurusd_micro_pattern_manual_labels import (
    build_micro_pattern_manual_labels_report,
)
from cajas.reports.validation_eurusd_micro_pattern_rule_candidates import (
    build_micro_pattern_rule_candidates_report,
)


def _packet_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample_id": "micro-noise-0001",
                "timestamp": "2025-01-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "micro_pattern_event_3": "micro_noise",
                "micro_noise_subtype": "inside_range_pause",
                "micro_pattern_rule_version": "v0",
                "bar_t_minus_2_open": 1.1,
                "bar_t_minus_2_high": 1.2,
                "bar_t_minus_2_low": 1.0,
                "bar_t_minus_2_close": 1.15,
                "bar_t_minus_1_open": 1.15,
                "bar_t_minus_1_high": 1.16,
                "bar_t_minus_1_low": 1.11,
                "bar_t_minus_1_close": 1.12,
                "bar_t_open": 1.12,
                "bar_t_high": 1.13,
                "bar_t_low": 1.09,
                "bar_t_close": 1.1,
                "three_bar_return": -0.01,
                "latest_close_position_in_candle": 0.2,
                "latest_close_position_in_three_bar_range": 0.3,
            }
        ]
    )


def test_packet_loader_reads_expected_columns(tmp_path: Path) -> None:
    packet_csv = tmp_path / "packet.csv"
    _packet_df().to_csv(packet_csv, index=False)
    loaded = load_micro_pattern_packet(packet_csv)
    assert "sample_id" in loaded.columns
    assert "human_micro_pattern_label" in loaded.columns


def test_completed_loader_missing_file_returns_empty(tmp_path: Path) -> None:
    loaded = load_completed_micro_pattern_labels(tmp_path / "missing.csv")
    assert loaded.empty
    assert "sample_id" in loaded.columns


def test_default_values_blank_and_valid() -> None:
    defaults = default_micro_pattern_label_values({})
    assert defaults["human_micro_pattern_label"] == ""
    assert defaults["human_should_create_rule"] == ""


def test_validation_accepts_valid_update() -> None:
    errors = validate_micro_pattern_label_update(
        {
            "sample_id": "micro-noise-0001",
            "human_micro_pattern_label": "true_noise",
            "human_micro_pattern_confidence": "medium",
            "human_should_create_rule": "uncertain",
            "suggested_event_key": "possible_new_rule_key",
        }
    )
    assert errors == []


def test_validation_rejects_invalid_confidence_and_create_rule() -> None:
    errors = validate_micro_pattern_label_update(
        {
            "sample_id": "micro-noise-0001",
            "human_micro_pattern_confidence": "5",
            "human_should_create_rule": "watch",
        }
    )
    assert "invalid_human_micro_pattern_confidence" in errors
    assert "invalid_human_should_create_rule" in errors


def test_validation_rejects_forbidden_fields() -> None:
    errors = validate_micro_pattern_label_update({"sample_id": "x", "order": "buy"})
    assert any(e.startswith("forbidden_fields_present:") for e in errors)


def test_persist_latest_state_and_audit_append_and_merge_reload(tmp_path: Path) -> None:
    packet_csv = tmp_path / "packet.csv"
    completed_csv = tmp_path / "completed.csv"
    audit_jsonl = tmp_path / "events.jsonl"
    _packet_df().to_csv(packet_csv, index=False)
    packet = load_micro_pattern_packet(packet_csv)
    row = packet.iloc[0].to_dict()

    first = persist_micro_pattern_label(
        {
            **row,
            "human_micro_pattern_label": "possible_new_rule",
            "human_micro_pattern_confidence": "low",
            "human_micro_pattern_rationale_zh": "第一次标注",
            "human_rule_suggestion_zh": "建议观察",
            "human_should_create_rule": "yes",
            "suggested_event_key": "micro_pattern_candidate_a",
        },
        completed_csv,
        audit_jsonl,
    )
    assert first["status"] == "ok"

    second = persist_micro_pattern_label(
        {
            **row,
            "human_micro_pattern_label": "inside_range_pause",
            "human_micro_pattern_confidence": "high",
            "human_micro_pattern_rationale_zh": "二次修正",
            "human_rule_suggestion_zh": "不新建规则",
            "human_should_create_rule": "no",
            "suggested_event_key": "",
        },
        completed_csv,
        audit_jsonl,
    )
    assert second["status"] == "ok"

    completed = pd.read_csv(completed_csv)
    assert len(completed) == 1
    assert completed.loc[0, "human_micro_pattern_label"] == "inside_range_pause"

    events = [json.loads(line) for line in audit_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) == 2

    merged = merge_packet_with_completed_labels(packet, completed)
    assert merged.loc[0, "human_micro_pattern_confidence"] == "high"


def test_manual_and_rule_reports_move_to_watch_with_saved_labels(tmp_path: Path) -> None:
    packet_csv = tmp_path / "packet.csv"
    completed_csv = tmp_path / "completed.csv"
    manual_json = tmp_path / "manual.json"
    trial_json = tmp_path / "trial.json"
    _packet_df().to_csv(packet_csv, index=False)

    persist_micro_pattern_label(
        {
            **_packet_df().iloc[0].to_dict(),
            "human_micro_pattern_label": "possible_new_rule",
            "human_micro_pattern_confidence": "medium",
            "human_micro_pattern_rationale_zh": "可继续观察",
            "human_rule_suggestion_zh": "建议新事件",
            "human_should_create_rule": "yes",
            "suggested_event_key": "micro_pattern_candidate_b",
        },
        completed_csv,
        tmp_path / "events.jsonl",
    )

    manual = build_micro_pattern_manual_labels_report(
        packet_csv=packet_csv,
        completed_labels_csv=completed_csv,
        output_template_csv=tmp_path / "template.csv",
    )
    manual_json.write_text(json.dumps(manual), encoding="utf-8")
    trial_json.write_text(json.dumps({"status": "not_approved"}), encoding="utf-8")
    assert manual["report_status"] in {"manual_micro_pattern_labels_watch", "manual_micro_pattern_labels_ready"}

    candidates = build_micro_pattern_rule_candidates_report(manual_json, trial_json, completed_csv)
    assert candidates["report_status"] in {"rule_candidates_watch", "rule_candidates_ready"}
    assert candidates["trial_approval_status"] == "not_approved"
