"""Build reviewer-oriented four-layer inspection packet from sample export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

AGREEMENT_VALUES = {"", "agree", "disagree", "uncertain"}
FORBIDDEN_FIELDS = {"trade_signal", "entry", "exit", "order", "position_size", "target_position"}
FEEDBACK_FIELDS = [
    "human_pattern_3_agreement",
    "human_pattern_3_correct_label",
    "human_pattern_3_feedback_zh",
    "human_market_8_agreement",
    "human_market_8_correct_state",
    "human_market_8_feedback_zh",
    "human_market_24_agreement",
    "human_market_24_correct_state",
    "human_market_24_feedback_zh",
    "human_market_128_agreement",
    "human_market_128_correct_state",
    "human_market_128_feedback_zh",
    "human_local_structure_agreement",
    "human_local_structure_correct_state",
    "human_local_structure_feedback_zh",
    "human_definition_issue_zh",
    "human_rule_adjustment_suggestion_zh",
    "review_updated_at_utc",
]


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


def _complete_row_mask(df: pd.DataFrame) -> pd.Series:
    return (
        (_as_int_series(df, "pattern_3_actual_bars_used") == 3)
        & (_as_int_series(df, "market_8_actual_bars_used") >= 8)
        & (_as_int_series(df, "market_24_actual_bars_used") >= 24)
        & (_as_int_series(df, "market_128_actual_bars_used") >= 128)
        & (_as_str_series(df, "pattern_3_event") != "unknown")
        & (_as_str_series(df, "market_8_state") != "unknown")
        & (_as_str_series(df, "market_24_state") != "unknown")
        & (_as_str_series(df, "market_128_state") != "unknown")
        & (_as_str_series(df, "local_structure_state") != "unknown")
        & (_as_str_series(df, "micro_pattern_rule_version") == "eurusd_micro_pattern_rules_v0")
    )


def _cold_start_mask(df: pd.DataFrame) -> pd.Series:
    return (
        (_as_int_series(df, "pattern_3_actual_bars_used") < 3)
        | (_as_int_series(df, "market_8_actual_bars_used") < 8)
        | (_as_int_series(df, "market_24_actual_bars_used") < 24)
        | (_as_int_series(df, "market_128_actual_bars_used") < 128)
    )


def _fallback_rule_mask(df: pd.DataFrame) -> pd.Series:
    return _as_str_series(df, "micro_pattern_rule_version") != "eurusd_micro_pattern_rules_v0"


def _diverse_pick(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    if df.empty:
        return df
    base = df.copy()
    base["__k_local"] = _as_str_series(base, "local_structure_state")
    base["__k_m128"] = _as_str_series(base, "market_128_state")
    base["__k_m24"] = _as_str_series(base, "market_24_state")
    base["__k_p3"] = _as_str_series(base, "pattern_3_event")
    base["__k_conf"] = _as_str_series(base, "structure_confidence")
    base = base.sort_values("timestamp")
    groups = {}
    for key, g in base.groupby(["__k_local", "__k_m128", "__k_m24", "__k_p3", "__k_conf"], dropna=False):
        groups[key] = g.reset_index(drop=True)
    keys = sorted(groups.keys())
    offsets = {k: 0 for k in keys}
    rows: list[pd.Series] = []
    seen: set[str] = set()
    while len(rows) < max_rows and keys:
        progressed = False
        for key in keys:
            g = groups[key]
            off = offsets[key]
            if off >= len(g):
                continue
            r = g.iloc[off]
            sid = str(r.get("sample_id", ""))
            offsets[key] = off + 1
            if sid in seen:
                continue
            seen.add(sid)
            rows.append(r)
            progressed = True
            if len(rows) >= max_rows:
                break
        if not progressed:
            break
    out = pd.DataFrame(rows)
    return out.drop(columns=[c for c in out.columns if c.startswith("__k_")], errors="ignore")


def build_market_state_inspection_packet(
    *,
    sample_export_csv: Path,
    output_csv: Path,
    output_jsonl: Path,
    trial_approval_json: Path,
    max_rows: int = 40,
    include_cold_start: bool = False,
) -> dict[str, Any]:
    if not sample_export_csv.exists():
        return {"report_status": "blocked", "reason": "sample_export_csv_missing"}
    source = pd.read_csv(sample_export_csv)
    if source.empty:
        return {"report_status": "blocked", "reason": "sample_export_csv_empty"}

    complete_mask = _complete_row_mask(source)
    cold_mask = _cold_start_mask(source)
    fallback_mask = _fallback_rule_mask(source)
    eligible = source[complete_mask].copy()
    selected = _diverse_pick(eligible, max_rows=max_rows).copy()
    if include_cold_start and len(selected) < max_rows:
        diagnostics = source[~complete_mask].copy().sort_values("timestamp")
        used = set(selected.get("sample_id", pd.Series(dtype=str)).astype(str).tolist())
        diagnostics = diagnostics[~diagnostics["sample_id"].astype(str).isin(used)]
        selected = pd.concat([selected, diagnostics.head(max_rows - len(selected))], ignore_index=True)
    for col in FEEDBACK_FIELDS:
        if col not in selected.columns:
            selected[col] = ""

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(output_csv, index=False)
    with output_jsonl.open("w", encoding="utf-8") as fp:
        for row in selected.to_dict(orient="records"):
            fp.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    violations = 0
    for layer in ("pattern_3", "market_8", "market_24", "market_128"):
        violations += int(
            (
                pd.to_numeric(selected[f"{layer}_actual_bars_used"], errors="coerce")
                > pd.to_numeric(selected[f"{layer}_max_bars"], errors="coerce")
            ).sum()
        )
    forbidden = [c for c in selected.columns if c.lower() in FORBIDDEN_FIELDS]
    selected_complete_mask = _complete_row_mask(selected)
    selected_cold_mask = _cold_start_mask(selected)
    selected_fallback_mask = _fallback_rule_mask(selected)
    incomplete_128_row_count = int((_as_int_series(selected, "market_128_actual_bars_used") < 128).sum())
    unknown_market_128_count = int((_as_str_series(selected, "market_128_state") == "unknown").sum())
    unknown_local_structure_count = int((_as_str_series(selected, "local_structure_state") == "unknown").sum())
    complete_four_layer_row_count = int(selected_complete_mask.sum())
    packet_row_count = int(len(selected))
    complete_four_layer_ratio = (complete_four_layer_row_count / packet_row_count) if packet_row_count > 0 else 0.0
    cold_start_row_count = int(selected_cold_mask.sum())
    fallback_rule_row_count = int(selected_fallback_mask.sum())

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    report_status = "market_state_inspection_packet_ready"
    watch_reasons: list[str] = []
    blocking_reasons: list[str] = []
    if violations > 0:
        blocking_reasons.append("actual_bars_used_exceeds_max")
    if forbidden:
        blocking_reasons.append(f"forbidden_fields_present:{','.join(forbidden)}")
    if trial_status != "not_approved":
        blocking_reasons.append(f"trial_approval_must_be_not_approved:{trial_status}")
    if packet_row_count == 0:
        blocking_reasons.append("empty_packet")
    if int(eligible.shape[0]) == 0 and not include_cold_start:
        blocking_reasons.append("no_eligible_complete_rows")
    if not blocking_reasons:
        if complete_four_layer_ratio < 0.8:
            watch_reasons.append("complete_four_layer_ratio_below_0_8")
        if not include_cold_start and cold_start_row_count > 0:
            watch_reasons.append("cold_start_rows_present_without_opt_in")
        if incomplete_128_row_count > 0:
            watch_reasons.append("incomplete_128_rows_present")
        if unknown_market_128_count > 0:
            watch_reasons.append("unknown_market_128_present")
        if unknown_local_structure_count > 0:
            watch_reasons.append("unknown_local_structure_present")
        if fallback_rule_row_count > 0 and not include_cold_start:
            watch_reasons.append("fallback_rule_rows_present")
    if blocking_reasons:
        report_status = "blocked"
    elif watch_reasons:
        report_status = "market_state_inspection_packet_watch"

    return {
        "report_status": report_status,
        "source_sample_count": int(len(source)),
        "packet_row_count": packet_row_count,
        "complete_four_layer_row_count": complete_four_layer_row_count,
        "complete_four_layer_ratio": float(round(complete_four_layer_ratio, 6)),
        "cold_start_row_count": cold_start_row_count,
        "incomplete_128_row_count": incomplete_128_row_count,
        "fallback_rule_row_count": fallback_rule_row_count,
        "unknown_market_128_count": unknown_market_128_count,
        "unknown_local_structure_count": unknown_local_structure_count,
        "main_packet_eligible_row_count": int(eligible.shape[0]),
        "selection_policy": "complete_four_layer_first",
        "include_cold_start": bool(include_cold_start),
        "pattern_sample_count": int((selected["sample_type"] == "pattern_sample").sum()),
        "market_state_sample_count": int((selected["sample_type"] == "market_state_sample").sum()),
        "four_layers_present": all(
            c in selected.columns
            for c in ["pattern_3_event", "market_8_state", "market_24_state", "market_128_state"]
        ),
        "feedback_fields_present": all(c in selected.columns for c in FEEDBACK_FIELDS),
        "actual_bars_used_valid": violations == 0,
        "trading_outputs_excluded": len(forbidden) == 0,
        "watch_reasons": watch_reasons,
        "blocking_reasons": blocking_reasons,
        "cold_start_diagnostic": {
            "cold_start_row_count": int(cold_mask.sum()),
            "incomplete_8_count": int((_as_int_series(source, "market_8_actual_bars_used") < 8).sum()),
            "incomplete_24_count": int((_as_int_series(source, "market_24_actual_bars_used") < 24).sum()),
            "incomplete_128_count": int((_as_int_series(source, "market_128_actual_bars_used") < 128).sum()),
            "first_complete_128_timestamp": (
                str(source[_as_int_series(source, "market_128_actual_bars_used") >= 128].sort_values("timestamp").head(1)["timestamp"].iloc[0])
                if int((_as_int_series(source, "market_128_actual_bars_used") >= 128).sum()) > 0
                else ""
            ),
            "recommendation": "exclude_from_main_packet",
        },
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
        "recommended_next_phase": "manual_inspect_four_layer_samples",
        "output_csv": str(output_csv),
        "output_jsonl": str(output_jsonl),
    }


def render_market_state_inspection_packet_markdown(report: dict[str, Any], packet_csv: Path) -> str:
    preview = []
    if packet_csv.exists():
        try:
            preview = pd.read_csv(packet_csv).head(8).to_dict(orient="records")
        except Exception:
            preview = []
    lines = [
        "# EURUSD Four-layer Inspection Packet",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- packet_row_count: `{report.get('packet_row_count')}`",
        f"- complete_four_layer_ratio: `{report.get('complete_four_layer_ratio')}`",
        f"- cold_start_row_count: `{report.get('cold_start_row_count')}`",
        f"- include_cold_start: `{report.get('include_cold_start')}`",
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
        "",
        "## Workflow",
        "",
        "- main packet excludes cold-start rows by default (`--include-cold-start` opt-in only)",
        "- complete four-layer rows are prioritized (`complete_four_layer_first`)",
        "- cold-start/incomplete rows are diagnostic-only and not main review evidence",
        "- inspect system labels for pattern_3/market_8/market_24/market_128/local_structure_state",
        "- fill `_agreement` + correction + `_zh` rationale fields",
        "- do not change taxonomy/rules without feedback evidence",
        "",
        "## Preview",
        "",
    ]
    if preview:
        for r in preview:
            lines.append(
                f"- {r.get('sample_id')} | {r.get('sample_type')} | p3={r.get('pattern_3_event')} | "
                f"m8={r.get('market_8_state')} | m24={r.get('market_24_state')} | m128={r.get('market_128_state')}"
            )
    else:
        lines.append("- no preview rows")
    lines.extend(
        [
            "",
            "## Quality Signals",
            "",
            f"- watch_reasons: {report.get('watch_reasons')}",
            f"- blocking_reasons: {report.get('blocking_reasons')}",
            "",
            "## Boundary",
            "",
            "- research-only inspection",
            "- no LLM calls",
            "- no trading outputs",
            f"- trial approval: `{report.get('trial_approval_status')}`",
        ]
    )
    return "\n".join(lines) + "\n"
