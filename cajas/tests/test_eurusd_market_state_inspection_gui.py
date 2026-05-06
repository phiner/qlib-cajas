from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.research.eurusd_market_state_inspection_gui import (
    build_inspection_chart,
    compute_chart_window,
    compute_layer_highlights,
    load_completed_feedback,
    load_inspection_packet,
    load_raw_clean_csv,
    merge_packet_with_completed,
    persist_feedback,
)


def _packet_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample_id": "s-001",
                "timestamp": "2025-01-01T06:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "pattern_3_event": "lower_sweep_reclaim",
                "market_8_state": "sideways",
                "market_24_state": "consolidation",
                "market_128_state": "high_level_consolidation",
                "local_structure_state": "high_level_consolidation",
                "structure_confidence": "medium",
                "pattern_3_actual_bars_used": 3,
                "market_8_actual_bars_used": 8,
                "market_24_actual_bars_used": 24,
                "market_128_actual_bars_used": 128,
                "pattern_3_rationale_zh": "r1",
                "market_8_rationale_zh": "r2",
                "market_24_rationale_zh": "r3",
                "market_128_rationale_zh": "r4",
                "market_state_rationale_zh": "r5",
            }
        ]
    )


def _raw_df(n: int = 220) -> pd.DataFrame:
    ts = pd.date_range("2024-12-30", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": [1.10 + i * 0.0001 for i in range(n)],
            "high": [1.101 + i * 0.0001 for i in range(n)],
            "low": [1.099 + i * 0.0001 for i in range(n)],
            "close": [1.1005 + i * 0.0001 for i in range(n)],
        }
    )


def test_loaders_and_chart_helpers(tmp_path: Path) -> None:
    packet_csv = tmp_path / "packet.csv"
    raw_csv = tmp_path / "raw.csv"
    _packet_df().to_csv(packet_csv, index=False)
    _raw_df().to_csv(raw_csv, index=False)

    packet = load_inspection_packet(packet_csv)
    raw = load_raw_clean_csv(raw_csv)
    assert len(packet) == 1
    assert len(raw) > 100

    window, target_idx = compute_chart_window(raw, packet.loc[0, "timestamp"], total_bars=176)
    assert len(window) >= 128
    highlights = compute_layer_highlights(target_idx, packet.loc[0])
    assert highlights["pattern_3"][1] - highlights["pattern_3"][0] + 1 == 3
    fig = build_inspection_chart(window, target_idx, highlights)
    assert len(fig.data) == 1


def test_feedback_persistence_latest_state_and_jsonl_append(tmp_path: Path) -> None:
    packet_csv = tmp_path / "packet.csv"
    completed_csv = tmp_path / "completed.csv"
    audit_jsonl = tmp_path / "events.jsonl"
    _packet_df().to_csv(packet_csv, index=False)
    packet = load_inspection_packet(packet_csv)

    first = persist_feedback(
        {
            **packet.iloc[0].to_dict(),
            "human_pattern_3_agreement": "agree",
            "human_market_8_agreement": "uncertain",
            "human_market_24_agreement": "agree",
            "human_market_128_agreement": "disagree",
            "human_local_structure_agreement": "agree",
        },
        completed_csv=completed_csv,
        audit_jsonl=audit_jsonl,
    )
    assert first["status"] == "ok"
    second = persist_feedback(
        {
            **packet.iloc[0].to_dict(),
            "human_pattern_3_agreement": "disagree",
            "human_market_8_agreement": "agree",
            "human_market_24_agreement": "agree",
            "human_market_128_agreement": "agree",
            "human_local_structure_agreement": "agree",
        },
        completed_csv=completed_csv,
        audit_jsonl=audit_jsonl,
    )
    assert second["status"] == "ok"

    completed = load_completed_feedback(completed_csv)
    merged = merge_packet_with_completed(packet, completed)
    assert merged.loc[0, "human_pattern_3_agreement"] == "disagree"

    events = [json.loads(x) for x in audit_jsonl.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(events) == 2


def test_feedback_rejects_forbidden_fields() -> None:
    result = persist_feedback(
        {"sample_id": "s-001", "order": "buy"},
        completed_csv=Path("/tmp/never_written.csv"),
        audit_jsonl=Path("/tmp/never_written.jsonl"),
    )
    assert result["status"] == "blocked"
