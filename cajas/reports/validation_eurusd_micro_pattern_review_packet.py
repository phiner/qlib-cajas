"""Build a deterministic residual micro-pattern review packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.reports.validation_eurusd_micro_noise_profile import _classify_noise_subtype


def _sample_balanced(df: pd.DataFrame, subtype_col: str, max_rows: int) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df.copy()
    groups = [g.sort_values("timestamp") for _, g in df.groupby(subtype_col, sort=True)]
    selected = []
    i = 0
    while len(selected) < max_rows and groups:
        g = groups[i % len(groups)]
        idx = len([s for s in selected if s["_subtype"] == g.iloc[0][subtype_col]])
        if idx < len(g):
            row = g.iloc[idx].copy()
            row["_subtype"] = g.iloc[0][subtype_col]
            selected.append(row)
        i += 1
        if i > max_rows * 10:
            break
    out = pd.DataFrame(selected)
    return out.drop(columns=["_subtype"], errors="ignore")


def build_micro_pattern_review_packet(
    *,
    market_state_csv: Path,
    output_csv: Path,
    output_jsonl: Path,
    trial_approval_json: Path,
    max_rows: int = 200,
) -> dict[str, Any]:
    if not market_state_csv.exists():
        return {"report_status": "blocked", "reason": "market_state_csv_missing"}

    df = pd.read_csv(market_state_csv)
    if "micro_pattern_event_3" not in df.columns:
        return {"report_status": "blocked", "reason": "missing_micro_pattern_event_3"}

    df_noise = df[df["micro_pattern_event_3"].astype(str) == "micro_noise"].copy()
    if df_noise.empty:
        return {
            "report_status": "awaiting_residual_noise",
            "packet_row_count": 0,
            "subtype_distribution": {},
            "rule_version": str(df.get("micro_pattern_rule_version", pd.Series(["unknown"])).iloc[0]) if len(df) else "unknown",
            "trading_outputs_excluded": True,
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    df_noise["micro_noise_subtype"] = df_noise.apply(_classify_noise_subtype, axis=1)
    df_noise = df_noise.sort_values("timestamp")
    sampled = _sample_balanced(df_noise, "micro_noise_subtype", max_rows)

    packet = pd.DataFrame(
        {
            "sample_id": [f"micro-noise-{i+1:04d}" for i in range(len(sampled))],
            "timestamp": sampled["timestamp"].astype(str),
            "symbol": sampled.get("symbol", pd.Series(["EURUSD"] * len(sampled))).astype(str),
            "timeframe": sampled.get("timeframe", pd.Series(["15m"] * len(sampled))).astype(str),
            "micro_pattern_event_3": sampled["micro_pattern_event_3"].astype(str),
            "micro_noise_subtype": sampled["micro_noise_subtype"].astype(str),
            "micro_pattern_rule_version": sampled.get("micro_pattern_rule_version", pd.Series(["unknown"] * len(sampled))).astype(str),
            "bar_t_minus_2_open": sampled.get("prev_open_2", pd.Series([None] * len(sampled))),
            "bar_t_minus_2_high": sampled.get("prev_high_2", pd.Series([None] * len(sampled))),
            "bar_t_minus_2_low": sampled.get("prev_low_2", pd.Series([None] * len(sampled))),
            "bar_t_minus_2_close": sampled.get("prev_close_2", pd.Series([None] * len(sampled))),
            "bar_t_minus_1_open": sampled.get("prev_open_1", pd.Series([None] * len(sampled))),
            "bar_t_minus_1_high": sampled.get("prev_high_1", pd.Series([None] * len(sampled))),
            "bar_t_minus_1_low": sampled.get("prev_low_1", pd.Series([None] * len(sampled))),
            "bar_t_minus_1_close": sampled.get("prev_close_1", pd.Series([None] * len(sampled))),
            "bar_t_open": sampled.get("open", pd.Series([None] * len(sampled))),
            "bar_t_high": sampled.get("high", pd.Series([None] * len(sampled))),
            "bar_t_low": sampled.get("low", pd.Series([None] * len(sampled))),
            "bar_t_close": sampled.get("close", pd.Series([None] * len(sampled))),
            "three_bar_return": sampled.get("return_3", pd.Series([None] * len(sampled))),
            "latest_close_position_in_candle": sampled.get("latest_close_position_in_candle", pd.Series([None] * len(sampled))),
            "latest_close_position_in_three_bar_range": sampled.get("range_position_3", pd.Series([None] * len(sampled))),
            "human_micro_pattern_label": [""] * len(sampled),
            "human_micro_pattern_rationale_zh": [""] * len(sampled),
            "human_rule_suggestion_zh": [""] * len(sampled),
        }
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    packet.to_csv(output_csv, index=False)
    with output_jsonl.open("w", encoding="utf-8") as fp:
        for row in packet.to_dict(orient="records"):
            fp.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    subtype_dist = {str(k): int(v) for k, v in packet["micro_noise_subtype"].value_counts().items()}

    trial_status = "not_approved"
    if trial_approval_json.exists():
        trial_status = str(json.loads(trial_approval_json.read_text(encoding="utf-8")).get("status", "not_approved"))

    return {
        "report_status": "micro_pattern_review_packet_ready" if trial_status == "not_approved" else "blocked",
        "packet_row_count": int(len(packet)),
        "subtype_distribution": subtype_dist,
        "rule_version": str(packet["micro_pattern_rule_version"].mode().iloc[0]) if len(packet) else "unknown",
        "trading_outputs_excluded": True,
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
    }


def render_micro_pattern_review_packet_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Micro Pattern Review Packet",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- packet_row_count: `{report.get('packet_row_count')}`",
        f"- rule_version: `{report.get('rule_version')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Subtype Distribution",
        "",
        f"- {report.get('subtype_distribution')}",
    ]
    return "\n".join(lines) + "\n"
