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


def _pick_rows(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    # deterministic prioritization: high confidence, low confidence, micro_noise, key structures, then remainder
    ordered_parts: list[pd.DataFrame] = []
    high = df[df.get("structure_confidence", "").astype(str) == "high"]
    low = df[df.get("structure_confidence", "").astype(str).isin(["low", "uncertain"])]
    noise = df[df.get("pattern_3_event", "").astype(str) == "micro_noise"]
    key_structures = df[
        df.get("local_structure_state", "").astype(str).isin(
            ["high_level_consolidation", "low_level_base", "range_chop", "pullback_in_uptrend", "rebound_in_downtrend"]
        )
    ]
    ordered_parts.extend([high, low, noise, key_structures, df])
    seen: set[str] = set()
    rows: list[pd.Series] = []
    for part in ordered_parts:
        for _, r in part.sort_values("timestamp").iterrows():
            sid = str(r.get("sample_id", ""))
            if sid in seen:
                continue
            seen.add(sid)
            rows.append(r)
            if len(rows) >= max_rows:
                return pd.DataFrame(rows)
    return pd.DataFrame(rows)


def build_market_state_inspection_packet(
    *,
    sample_export_csv: Path,
    output_csv: Path,
    output_jsonl: Path,
    trial_approval_json: Path,
    max_rows: int = 40,
) -> dict[str, Any]:
    if not sample_export_csv.exists():
        return {"report_status": "blocked", "reason": "sample_export_csv_missing"}
    source = pd.read_csv(sample_export_csv)
    if source.empty:
        return {"report_status": "blocked", "reason": "sample_export_csv_empty"}

    selected = _pick_rows(source, max_rows=max_rows).copy()
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

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    report_status = "market_state_inspection_packet_ready"
    if violations > 0 or forbidden or trial_status != "not_approved":
        report_status = "blocked"

    return {
        "report_status": report_status,
        "source_sample_count": int(len(source)),
        "packet_row_count": int(len(selected)),
        "pattern_sample_count": int((selected["sample_type"] == "pattern_sample").sum()),
        "market_state_sample_count": int((selected["sample_type"] == "market_state_sample").sum()),
        "four_layers_present": all(
            c in selected.columns
            for c in ["pattern_3_event", "market_8_state", "market_24_state", "market_128_state"]
        ),
        "feedback_fields_present": all(c in selected.columns for c in FEEDBACK_FIELDS),
        "actual_bars_used_valid": violations == 0,
        "trading_outputs_excluded": len(forbidden) == 0,
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
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
        "",
        "## Workflow",
        "",
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
            "## Boundary",
            "",
            "- research-only inspection",
            "- no LLM calls",
            "- no trading outputs",
            f"- trial approval: `{report.get('trial_approval_status')}`",
        ]
    )
    return "\n".join(lines) + "\n"
