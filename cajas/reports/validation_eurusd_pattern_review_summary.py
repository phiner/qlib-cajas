"""EURUSD pattern review feedback summary report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_validation_eurusd_pattern_review_summary(
    *,
    feedback_report: Path,
    completed_review_csv: Path,
    candidate_pack_report: Path | None = None,
    minimum_review_threshold: int = 100,
) -> dict[str, Any]:
    feedback = json.loads(feedback_report.read_text(encoding="utf-8"))
    feedback_status = feedback.get("status")

    if feedback_status == "awaiting_review_input":
        return {
            "schema_version": 1,
            "status": "awaiting_review_input",
            "reviewed_count": 0,
            "minimum_review_threshold": minimum_review_threshold,
            "candidate_type_summary": {},
            "top_valid_pattern_types": [],
            "top_false_positive_types": [],
            "high_confidence_examples": [],
            "needs_more_review": [],
            "recommendation": "complete_review_template_first",
            "scope_boundary": {
                "review_feedback_only": True,
                "trading_signals": False,
                "order_generation": False,
                "model_training": False,
            },
        }

    if feedback_status == "blocked":
        return {
            "schema_version": 1,
            "status": "blocked",
            "reviewed_count": int(feedback.get("reviewed_count", 0)),
            "minimum_review_threshold": minimum_review_threshold,
            "recommendation": "fix_review_feedback_file",
            "scope_boundary": {
                "review_feedback_only": True,
                "trading_signals": False,
                "order_generation": False,
                "model_training": False,
            },
        }

    if not completed_review_csv.exists():
        return {
            "schema_version": 1,
            "status": "awaiting_review_input",
            "reviewed_count": 0,
            "minimum_review_threshold": minimum_review_threshold,
            "recommendation": "complete_review_template_first",
            "scope_boundary": {
                "review_feedback_only": True,
                "trading_signals": False,
                "order_generation": False,
                "model_training": False,
            },
        }

    df = pd.read_csv(completed_review_csv)
    if "review_status" in df.columns:
        df = df[df["review_status"].astype(str) == "reviewed"].copy()

    reviewed_count = int(len(df))

    csum: dict[str, Any] = {}
    if not df.empty and {"candidate_type", "human_pattern_label"}.issubset(df.columns):
        for ctype, g in df.groupby("candidate_type"):
            total = len(g)
            valid_rate = float((g["human_pattern_label"] == "valid_pattern").mean())
            false_rate = float((g["human_pattern_label"] == "false_positive").mean())
            csum[str(ctype)] = {
                "reviewed": int(total),
                "valid_pattern_rate": valid_rate,
                "false_positive_rate": false_rate,
                "avg_structure_quality": float(pd.to_numeric(g.get("structure_quality"), errors="coerce").mean()),
                "avg_follow_through_quality": float(pd.to_numeric(g.get("follow_through_quality"), errors="coerce").mean()),
                "avg_review_confidence": float(pd.to_numeric(g.get("review_confidence"), errors="coerce").mean()),
            }

    top_valid = sorted(csum.items(), key=lambda kv: kv[1].get("valid_pattern_rate", 0.0), reverse=True)[:3]
    top_false = sorted(csum.items(), key=lambda kv: kv[1].get("false_positive_rate", 0.0), reverse=True)[:3]

    examples = []
    if not df.empty and {"sample_id", "candidate_type", "human_pattern_label", "review_confidence"}.issubset(df.columns):
        h = df[pd.to_numeric(df["review_confidence"], errors="coerce") >= 4].head(20)
        for _, r in h.iterrows():
            examples.append(
                {
                    "sample_id": str(r.get("sample_id")),
                    "candidate_type": str(r.get("candidate_type")),
                    "human_pattern_label": str(r.get("human_pattern_label")),
                    "review_confidence": int(r.get("review_confidence")) if pd.notna(r.get("review_confidence")) else None,
                }
            )

    needs_more = [k for k, v in csum.items() if int(v.get("reviewed", 0)) < max(10, minimum_review_threshold // max(1, max(len(csum), 1)))]

    if reviewed_count < minimum_review_threshold:
        rec = "continue_manual_review"
        status = "watch"
    elif any(v.get("false_positive_rate", 0) >= 0.5 for v in csum.values()):
        rec = "refine_candidate_rules"
        status = "watch"
    elif any(v.get("valid_pattern_rate", 0) >= 0.5 for v in csum.values()):
        rec = "analyze_valid_pattern_outcomes"
        status = "ready"
    else:
        rec = "expand_review_samples"
        status = "watch"

    return {
        "schema_version": 1,
        "status": status,
        "reviewed_count": reviewed_count,
        "minimum_review_threshold": minimum_review_threshold,
        "candidate_type_summary": csum,
        "top_valid_pattern_types": [{"candidate_type": k, **v} for k, v in top_valid],
        "top_false_positive_types": [{"candidate_type": k, **v} for k, v in top_false],
        "high_confidence_examples": examples,
        "needs_more_review": needs_more,
        "recommendation": rec,
        "scope_boundary": {
            "review_feedback_only": True,
            "trading_signals": False,
            "order_generation": False,
            "model_training": False,
        },
    }


def render_validation_eurusd_pattern_review_summary_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation EURUSD Pattern Review Summary",
            "",
            f"- status: `{payload.get('status')}`",
            f"- reviewed_count: `{payload.get('reviewed_count')}`",
            f"- minimum_review_threshold: `{payload.get('minimum_review_threshold')}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "",
            "## Policy",
            "",
            "- Review feedback summary only; non-trading.",
            "- No order generation or model training in this phase.",
            "",
        ]
    )
