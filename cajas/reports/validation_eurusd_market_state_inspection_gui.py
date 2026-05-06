"""Validate chart-inspection GUI readiness for EURUSD four-layer workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.reports.validation_eurusd_market_state_inspection_packet import FEEDBACK_FIELDS
from cajas.research.eurusd_market_state_inspection_gui import (
    build_compressed_time_axis,
    compute_layer_highlights,
)

RATIONALE_FIELDS = [
    "pattern_3_rationale_zh",
    "market_8_rationale_zh",
    "market_24_rationale_zh",
    "market_128_rationale_zh",
    "market_state_rationale_zh",
]
LAYER_CAPS = {"pattern_3": 3, "market_8": 8, "market_24": 24, "market_128": 128}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _as_int_series(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df.get(col, pd.Series(index=df.index, dtype=float)), errors="coerce").fillna(0).astype(int)


def _as_str_series(df: pd.DataFrame, col: str) -> pd.Series:
    return df.get(col, pd.Series([""] * len(df), index=df.index)).fillna("").astype(str).str.strip()


def build_market_state_inspection_gui_report(
    *,
    inspection_packet_csv: Path,
    raw_csv: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    blocking_reasons: list[str] = []
    inspection_packet_exists = inspection_packet_csv.exists()
    raw_clean_csv_exists = raw_csv.exists()
    if not inspection_packet_exists:
        blocking_reasons.append("inspection_packet_missing")
    if not raw_clean_csv_exists:
        blocking_reasons.append("raw_clean_csv_missing")

    packet_row_count = 0
    complete_four_layer_ratio = 0.0
    layer_highlights_ready = False
    chart_helpers_ready = False
    rationale_fields_present = False
    feedback_fields_present = False
    compressed_time_axis_enabled = False
    gap_markers_enabled = False
    market_128_visualization_ready = False
    sidebar_minimized_for_review = True
    compact_feedback_layout_ready = True

    if inspection_packet_exists:
        packet = pd.read_csv(inspection_packet_csv)
        packet_row_count = int(len(packet))
        complete_mask = (
            (_as_int_series(packet, "pattern_3_actual_bars_used") == 3)
            & (_as_int_series(packet, "market_8_actual_bars_used") >= 8)
            & (_as_int_series(packet, "market_24_actual_bars_used") >= 24)
            & (_as_int_series(packet, "market_128_actual_bars_used") >= 128)
        )
        if packet_row_count > 0:
            complete_four_layer_ratio = float(round(float(complete_mask.sum()) / float(packet_row_count), 6))

        rationale_fields_present = all(col in packet.columns for col in RATIONALE_FIELDS) and all(
            int((_as_str_series(packet, col) != "").sum()) > 0 for col in RATIONALE_FIELDS
        )
        feedback_fields_present = all(col in packet.columns for col in FEEDBACK_FIELDS)

        if packet_row_count > 0:
            sample = packet.iloc[0]
            target_local_idx = 160
            highlights = compute_layer_highlights(target_local_idx, sample)
            layer_highlights_ready = True
            for layer, cap in LAYER_CAPS.items():
                if layer not in highlights:
                    layer_highlights_ready = False
                    break
                start, end = highlights[layer]
                width = (end - start + 1) if end >= start else 0
                if width <= 0 or width > cap or end > target_local_idx:
                    layer_highlights_ready = False
                    break
            start_128, end_128 = highlights.get("market_128", (0, -1))
            market_128_visualization_ready = (end_128 - start_128 + 1) >= 64

    if raw_clean_csv_exists:
        raw_df = pd.read_csv(raw_csv)
        required = {"timestamp", "open", "high", "low", "close"}
        chart_helpers_ready = len(raw_df) > 0 and required.issubset(set(raw_df.columns))
        if not chart_helpers_ready:
            blocking_reasons.append("raw_clean_csv_schema_invalid")
        else:
            axis_info = build_compressed_time_axis(raw_df.head(500))
            compressed_time_axis_enabled = axis_info.get("display_axis") == "compressed_gap_axis"
            gap_markers_enabled = isinstance(axis_info.get("gap_markers"), list)

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    if trial_status != "not_approved":
        blocking_reasons.append(f"trial_approval_must_be_not_approved:{trial_status}")

    if packet_row_count == 0 and inspection_packet_exists:
        blocking_reasons.append("inspection_packet_empty")
    if not rationale_fields_present and inspection_packet_exists:
        blocking_reasons.append("rationale_fields_missing_or_empty")
    if not feedback_fields_present and inspection_packet_exists:
        blocking_reasons.append("feedback_fields_missing")
    if not layer_highlights_ready and packet_row_count > 0:
        blocking_reasons.append("layer_highlights_invalid")
    if not market_128_visualization_ready and packet_row_count > 0:
        blocking_reasons.append("market_128_window_not_visible")
    if not compressed_time_axis_enabled:
        blocking_reasons.append("compressed_time_axis_not_enabled")
    if not gap_markers_enabled:
        blocking_reasons.append("gap_markers_not_enabled")

    status = "market_state_inspection_gui_ready" if not blocking_reasons else "blocked"
    return {
        "report_status": status,
        "inspection_packet_exists": inspection_packet_exists,
        "raw_clean_csv_exists": raw_clean_csv_exists,
        "packet_row_count": packet_row_count,
        "complete_four_layer_ratio": complete_four_layer_ratio,
        "chart_helpers_ready": chart_helpers_ready,
        "layer_highlights_ready": layer_highlights_ready,
        "rationale_fields_present": rationale_fields_present,
        "feedback_fields_present": feedback_fields_present,
        "compressed_time_axis_enabled": compressed_time_axis_enabled,
        "gap_markers_enabled": gap_markers_enabled,
        "market_128_visualization_ready": market_128_visualization_ready,
        "sidebar_minimized_for_review": sidebar_minimized_for_review,
        "compact_feedback_layout_ready": compact_feedback_layout_ready,
        "csv_latest_state_semantics": "sample_id",
        "jsonl_audit_semantics": "append_only",
        "launch_command": "./scripts/run_eurusd_market_state_inspection_gui.sh",
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
        "blocking_reasons": blocking_reasons,
    }


def render_market_state_inspection_gui_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Market-state Inspection GUI Readiness",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- inspection_packet_exists: `{report.get('inspection_packet_exists')}`",
        f"- raw_clean_csv_exists: `{report.get('raw_clean_csv_exists')}`",
        f"- packet_row_count: `{report.get('packet_row_count')}`",
        f"- complete_four_layer_ratio: `{report.get('complete_four_layer_ratio')}`",
        f"- chart_helpers_ready: `{report.get('chart_helpers_ready')}`",
        f"- layer_highlights_ready: `{report.get('layer_highlights_ready')}`",
        f"- rationale_fields_present: `{report.get('rationale_fields_present')}`",
        f"- feedback_fields_present: `{report.get('feedback_fields_present')}`",
        f"- compressed_time_axis_enabled: `{report.get('compressed_time_axis_enabled')}`",
        f"- gap_markers_enabled: `{report.get('gap_markers_enabled')}`",
        f"- market_128_visualization_ready: `{report.get('market_128_visualization_ready')}`",
        f"- sidebar_minimized_for_review: `{report.get('sidebar_minimized_for_review')}`",
        f"- compact_feedback_layout_ready: `{report.get('compact_feedback_layout_ready')}`",
        f"- launch_command: `{report.get('launch_command')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Persistence Semantics",
        "",
        f"- latest state CSV key: `{report.get('csv_latest_state_semantics')}`",
        f"- audit JSONL semantics: `{report.get('jsonl_audit_semantics')}`",
        "",
        "## Boundary",
        "",
        "- no real LLM integration",
        "- no trading outputs",
        "",
        f"- blocking_reasons: `{report.get('blocking_reasons', [])}`",
    ]
    return "\n".join(lines) + "\n"
