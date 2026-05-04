"""EURUSD pattern review template generation report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

FORBIDDEN = {"buy", "sell", "long", "short", "order", "position", "target_position", "signal", "entry", "exit"}


def build_validation_eurusd_pattern_review_template(
    *,
    samples_path: Path,
    label_schema_path: Path,
    output_template_csv: Path,
    output_template_jsonl: Path,
) -> dict[str, Any]:
    if not samples_path.exists() or not label_schema_path.exists():
        return {"schema_version": 1, "status": "blocked", "blocking_reasons": ["missing_input"]}

    samples = pd.read_csv(samples_path) if samples_path.suffix.lower() != ".jsonl" else pd.DataFrame(
        [json.loads(x) for x in samples_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    )
    schema = json.loads(label_schema_path.read_text(encoding="utf-8"))
    if schema.get("status") != "ready":
        return {"schema_version": 1, "status": "blocked", "blocking_reasons": ["schema_not_ready"]}

    forbidden_hits = [c for c in samples.columns if c.lower() in FORBIDDEN]
    if forbidden_hits:
        return {
            "schema_version": 1,
            "status": "blocked",
            "forbidden_trading_column_hits": forbidden_hits,
            "blocking_reasons": ["forbidden_trading_columns"],
        }

    out = samples.copy()
    if "sample_id" not in out.columns:
        out["sample_id"] = [f"eurusd15m_{i+1:06d}" for i in range(len(out))]

    defaults = schema.get("defaults", {})
    out["schema_version"] = schema.get("schema_version")
    out["review_status"] = defaults.get("review_status", "pending")

    for field in [
        "human_pattern_label",
        "market_context",
        "direction_context",
        "structure_quality",
        "follow_through_quality",
        "review_confidence",
        "review_notes",
    ]:
        out[field] = defaults.get(field)

    prio_rank = {"high": 0, "medium": 1, "low": 2}
    out["_prio"] = out["review_priority"].map(prio_rank).fillna(9)
    out = out.sort_values(["candidate_type", "_prio", "confidence_score", "timestamp"], ascending=[True, True, False, True]).drop(columns=["_prio"]) \
        .reset_index(drop=True)

    output_template_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_template_csv, index=False)
    with output_template_jsonl.open("w", encoding="utf-8") as f:
        for row in out.to_dict(orient="records"):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {
        "schema_version": 1,
        "status": "ready",
        "template_row_count": int(len(out)),
        "schema_version_used": schema.get("schema_version"),
        "candidate_types": sorted(out["candidate_type"].dropna().unique().tolist()) if "candidate_type" in out.columns else [],
        "output_paths": {
            "template_csv": str(output_template_csv),
            "template_jsonl": str(output_template_jsonl),
        },
        "forbidden_trading_column_hits": [],
        "recommendation": "begin_human_review",
    }


def render_validation_eurusd_pattern_review_template_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation EURUSD Pattern Review Template",
            "",
            f"- status: `{payload.get('status')}`",
            f"- template_row_count: `{payload.get('template_row_count')}`",
            f"- schema_version: `{payload.get('schema_version_used')}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "",
            "## Policy",
            "",
            "- Template is for manual review only.",
            "- No trading signals or orders are emitted.",
            "",
        ]
    )
