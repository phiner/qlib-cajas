"""Export inspectable four-layer EURUSD market-state samples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

MAX_BARS = {
    "pattern_3": 3,
    "market_8": 8,
    "market_24": 24,
    "market_128": 128,
}

REQUESTED_PATTERN_EVENTS = [
    "lower_sweep_reclaim",
    "upper_sweep_reject",
    "three_bar_reversal_up",
    "three_bar_reversal_down",
    "failed_followthrough_up",
    "failed_followthrough_down",
    "inside_range_chop",
    "micro_noise",
]
REQUESTED_MARKET_STATES = [
    "high_level_consolidation",
    "low_level_base",
    "range_chop",
    "rebound_in_downtrend",
    "pullback_in_uptrend",
    "trend_continuation",
    "exhaustion_risk",
    "unknown",
]
FORBIDDEN_FIELDS = {"trade_signal", "entry", "exit", "order", "position_size", "target_position"}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_col(df: pd.DataFrame, col: str, default: Any = "") -> pd.Series:
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def _build_single_sample_row(row: pd.Series, sample_id: str, sample_type: str, available_history_bars: int) -> dict[str, Any]:
    pattern_used = min(MAX_BARS["pattern_3"], available_history_bars)
    market8_used = min(MAX_BARS["market_8"], available_history_bars)
    market24_used = min(MAX_BARS["market_24"], available_history_bars)
    market128_used = min(MAX_BARS["market_128"], available_history_bars)

    return {
        "sample_id": sample_id,
        "sample_type": sample_type,
        "timestamp": str(row.get("timestamp", "")),
        "symbol": str(row.get("symbol", "EURUSD")),
        "timeframe": str(row.get("timeframe", "15m")),
        "local_structure_state": str(row.get("local_structure_state", "")),
        "structure_confidence": str(row.get("structure_confidence", "")),
        "market_state_rule_version": str(row.get("market_state_rule_version", "")),
        "micro_pattern_rule_version": str(row.get("micro_pattern_rule_version", "")),
        "trading_outputs_excluded": True,
        "pattern_3_layer_type": "pattern_event",
        "pattern_3_max_bars": MAX_BARS["pattern_3"],
        "pattern_3_actual_bars_used": pattern_used,
        "pattern_3_actual_bars_used_reason": "fixed_v0_window_or_available_history",
        "pattern_3_event": str(row.get("micro_pattern_event_3", "")),
        "pattern_3_direction": str(row.get("micro_pattern_direction_3", "")),
        "pattern_3_strength": str(row.get("micro_pattern_strength_3", "")),
        "pattern_3_evidence_summary_zh": str(row.get("micro_event_reason_code", "")),
        "pattern_3_rationale_zh": str(row.get("micro_event_rationale_zh", "")),
        "market_8_layer_type": "market_state",
        "market_8_max_bars": MAX_BARS["market_8"],
        "market_8_actual_bars_used": market8_used,
        "market_8_actual_bars_used_reason": "fixed_v0_window_or_available_history",
        "market_8_state": str(row.get("short_term_state_8", "")),
        "market_8_evidence_summary_zh": str(row.get("short_structure_reason_code", "")),
        "market_8_rationale_zh": str(row.get("market_state_rationale_zh", "")),
        "market_24_layer_type": "market_state",
        "market_24_max_bars": MAX_BARS["market_24"],
        "market_24_actual_bars_used": market24_used,
        "market_24_actual_bars_used_reason": "fixed_v0_window_or_available_history",
        "market_24_state": str(row.get("mid_term_state_24", "")),
        "market_24_evidence_summary_zh": str(row.get("mid_structure_reason_code", "")),
        "market_24_rationale_zh": str(row.get("market_state_rationale_zh", "")),
        "market_128_layer_type": "market_state",
        "market_128_max_bars": MAX_BARS["market_128"],
        "market_128_actual_bars_used": market128_used,
        "market_128_actual_bars_used_reason": "fixed_v0_window_or_available_history",
        "market_128_state": str(row.get("long_term_state_128", "")),
        "market_128_evidence_summary_zh": str(row.get("long_structure_reason_code", "")),
        "market_128_rationale_zh": str(row.get("market_state_rationale_zh", "")),
        "bar_t_minus_2_open": row.get("prev_open_2"),
        "bar_t_minus_2_high": row.get("prev_high_2"),
        "bar_t_minus_2_low": row.get("prev_low_2"),
        "bar_t_minus_2_close": row.get("prev_close_2"),
        "bar_t_minus_1_open": row.get("prev_open_1"),
        "bar_t_minus_1_high": row.get("prev_high_1"),
        "bar_t_minus_1_low": row.get("prev_low_1"),
        "bar_t_minus_1_close": row.get("prev_close_1"),
        "bar_t_open": row.get("open"),
        "bar_t_high": row.get("high"),
        "bar_t_low": row.get("low"),
        "bar_t_close": row.get("close"),
        "market_8_return": row.get("return_8"),
        "market_8_range_position": row.get("range_position_8"),
        "market_8_range_width": row.get("range_width_8"),
        "market_24_return": row.get("return_24"),
        "market_24_range_position": row.get("range_position_24"),
        "market_24_range_width": row.get("range_width_24"),
        "market_128_return": row.get("return_128"),
        "market_128_range_position": row.get("range_position_128"),
        "market_128_range_width": row.get("range_width_128"),
        "market_8_slope": row.get("slope_8"),
        "market_24_slope": row.get("slope_24"),
        "market_128_slope": row.get("slope_128"),
        "market_8_normalized_slope": row.get("normalized_slope_8"),
        "market_24_normalized_slope": row.get("normalized_slope_24"),
        "market_128_normalized_slope": row.get("normalized_slope_128"),
        "market_8_volatility_state": str(row.get("volatility_state_8", "")),
        "market_24_volatility_state": str(row.get("volatility_state_24", "")),
        "market_128_volatility_state": str(row.get("volatility_state_128", "")),
        "market_128_gap_count": row.get("gap_count_128"),
        "market_128_largest_gap_hours": row.get("largest_gap_hours_128"),
    }


def _round_robin_take(df: pd.DataFrame, key_col: str, wanted_values: list[str], limit: int) -> tuple[pd.DataFrame, list[str]]:
    if df.empty:
        return df, wanted_values
    groups = {k: g.sort_values("timestamp") for k, g in df.groupby(key_col, dropna=False)}
    missing = [x for x in wanted_values if x not in groups]
    order = [x for x in wanted_values if x in groups] + sorted([x for x in groups if x not in wanted_values])
    picks: list[pd.Series] = []
    offsets = {k: 0 for k in order}
    while len(picks) < limit and order:
        progressed = False
        for key in order:
            g = groups.get(key)
            if g is None:
                continue
            off = offsets[key]
            if off < len(g):
                picks.append(g.iloc[off])
                offsets[key] = off + 1
                progressed = True
                if len(picks) >= limit:
                    break
        if not progressed:
            break
    if not picks:
        return df.head(limit), missing
    return pd.DataFrame(picks).reset_index(drop=True), missing


def _validate_actual_bars_used(df: pd.DataFrame) -> int:
    violations = 0
    for layer in ("pattern_3", "market_8", "market_24", "market_128"):
        max_col = f"{layer}_max_bars"
        used_col = f"{layer}_actual_bars_used"
        if max_col not in df.columns or used_col not in df.columns:
            violations += len(df)
            continue
        violations += int((pd.to_numeric(df[used_col], errors="coerce") > pd.to_numeric(df[max_col], errors="coerce")).sum())
    return violations


def build_market_state_sample_export(
    *,
    market_state_csv: Path,
    raw_csv: Path,
    output_csv: Path,
    output_jsonl: Path,
    trial_approval_json: Path,
    max_rows: int = 100,
) -> dict[str, Any]:
    if not market_state_csv.exists():
        return {"report_status": "blocked", "reason": "market_state_csv_missing"}
    df = pd.read_csv(market_state_csv)
    if df.empty:
        return {"report_status": "blocked", "reason": "market_state_csv_empty"}

    df = df.copy()
    df["timestamp"] = _safe_col(df, "timestamp", "").astype(str)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["available_history_bars"] = df.index + 1

    half = max(1, max_rows // 2)
    pattern_samples, missing_patterns = _round_robin_take(df, "micro_pattern_event_3", REQUESTED_PATTERN_EVENTS, half)
    market_samples, missing_markets = _round_robin_take(df, "local_structure_state", REQUESTED_MARKET_STATES, max_rows - len(pattern_samples))

    rows: list[dict[str, Any]] = []
    for i, r in pattern_samples.iterrows():
        rows.append(
            _build_single_sample_row(
                r,
                sample_id=f"pattern-sample-{i + 1:04d}",
                sample_type="pattern_sample",
                available_history_bars=int(r["available_history_bars"]),
            )
        )
    for i, r in market_samples.iterrows():
        rows.append(
            _build_single_sample_row(
                r,
                sample_id=f"market-state-sample-{i + 1:04d}",
                sample_type="market_state_sample",
                available_history_bars=int(r["available_history_bars"]),
            )
        )

    out_df = pd.DataFrame(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv, index=False)
    with output_jsonl.open("w", encoding="utf-8") as fp:
        for row in out_df.to_dict(orient="records"):
            fp.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    violations = _validate_actual_bars_used(out_df)
    forbidden_cols = [c for c in out_df.columns if c.lower() in FORBIDDEN_FIELDS]
    bars_3_ohlc_context_present = all(
        c in out_df.columns
        for c in [
            "bar_t_minus_2_open",
            "bar_t_minus_2_high",
            "bar_t_minus_2_low",
            "bar_t_minus_2_close",
            "bar_t_minus_1_open",
            "bar_t_minus_1_high",
            "bar_t_minus_1_low",
            "bar_t_minus_1_close",
            "bar_t_open",
            "bar_t_high",
            "bar_t_low",
            "bar_t_close",
        ]
    )
    market_layer_summaries_present = all(
        c in out_df.columns
        for c in [
            "market_8_return",
            "market_8_range_position",
            "market_8_range_width",
            "market_24_return",
            "market_24_range_position",
            "market_24_range_width",
            "market_128_return",
            "market_128_range_position",
            "market_128_range_width",
        ]
    )

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    report_status = "market_state_sample_export_ready"
    if violations > 0 or forbidden_cols or trial_status != "not_approved":
        report_status = "blocked"

    return {
        "report_status": report_status,
        "input_row_count": int(len(df)),
        "sample_row_count": int(len(out_df)),
        "pattern_sample_count": int((out_df["sample_type"] == "pattern_sample").sum()) if "sample_type" in out_df.columns else 0,
        "market_state_sample_count": int((out_df["sample_type"] == "market_state_sample").sum()) if "sample_type" in out_df.columns else 0,
        "four_layers_present": all(c in out_df.columns for c in ["pattern_3_layer_type", "market_8_layer_type", "market_24_layer_type", "market_128_layer_type"]),
        "pattern_layer_present": "pattern_3_layer_type" in out_df.columns,
        "market_layers_present": all(c in out_df.columns for c in ["market_8_layer_type", "market_24_layer_type", "market_128_layer_type"]),
        "actual_bars_used_valid": violations == 0,
        "max_bars_constraints": MAX_BARS,
        "actual_bars_used_violation_count": int(violations),
        "unavailable_requested_classes": sorted(set(missing_patterns + missing_markets)),
        "bars_3_ohlc_context_present": bars_3_ohlc_context_present,
        "market_layer_summaries_present": market_layer_summaries_present,
        "micro_pattern_rule_version": str(out_df.get("micro_pattern_rule_version", pd.Series(dtype=str)).astype(str).mode().iloc[0]) if len(out_df) else "",
        "market_state_rule_version": str(out_df.get("market_state_rule_version", pd.Series(dtype=str)).astype(str).mode().iloc[0]) if len(out_df) else "",
        "trading_outputs_excluded": len(forbidden_cols) == 0,
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
        "recommended_next_phase": "inspect_market_state_samples_before_rule_changes",
        "output_csv": str(output_csv),
        "output_jsonl": str(output_jsonl),
        "raw_csv_reference": str(raw_csv),
    }


def render_market_state_sample_export_markdown(report: dict[str, Any], sample_csv: Path) -> str:
    preview_rows = []
    if sample_csv.exists():
        try:
            preview = pd.read_csv(sample_csv).head(8)
            preview_rows = preview.to_dict(orient="records")
        except Exception:
            preview_rows = []
    lines = [
        "# EURUSD Market-state Four-layer Sample Export",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- sample_row_count: `{report.get('sample_row_count')}`",
        f"- pattern_sample_count: `{report.get('pattern_sample_count')}`",
        f"- market_state_sample_count: `{report.get('market_state_sample_count')}`",
        f"- actual_bars_used_valid: `{report.get('actual_bars_used_valid')}`",
        "",
        "## Four-layer Definition",
        "",
        "| layer | type | max bars |",
        "|---|---|---|",
        "| pattern_3 | pattern_event | 3 |",
        "| market_8 | market_state | 8 |",
        "| market_24 | market_state | 24 |",
        "| market_128 | market_state | 128 |",
        "",
        "Market layers may use fewer bars than max. No layer may exceed its max.",
        "",
        "## Compact Sample Preview",
        "",
    ]
    if preview_rows:
        for row in preview_rows:
            lines.append(
                f"- {row.get('sample_id')} | {row.get('sample_type')} | {row.get('timestamp')} | "
                f"p3={row.get('pattern_3_event')} | m8={row.get('market_8_state')} | "
                f"m24={row.get('market_24_state')} | m128={row.get('market_128_state')}"
            )
    else:
        lines.append("- no preview rows")
    lines.extend(
        [
            "",
            "## Distribution Summary",
            "",
            f"- unavailable_requested_classes: {report.get('unavailable_requested_classes')}",
            "",
            "## Output Paths",
            "",
            f"- csv: `{report.get('output_csv')}`",
            f"- jsonl: `{report.get('output_jsonl')}`",
            "",
            "## Boundary",
            "",
            "- research labels only",
            "- no trading signals/orders/positions",
            "- no real LLM calls",
            f"- trial approval: `{report.get('trial_approval_status')}`",
        ]
    )
    return "\n".join(lines) + "\n"
