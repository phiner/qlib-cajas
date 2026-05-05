"""Micro-noise profiling for EURUSD market-state outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _classify_noise_subtype(row: pd.Series) -> str:
    body = float(row.get("body_ratio_latest", 0.0) or 0.0)
    up = float(row.get("upper_wick_ratio_latest", 0.0) or 0.0)
    low = float(row.get("lower_wick_ratio_latest", 0.0) or 0.0)
    ret3 = float(row.get("return_3", 0.0) or 0.0)
    rng_ratio = float(row.get("range_ratio_3_8", 1.0) or 1.0)
    seq = str(row.get("micro_event_reason_code", ""))

    if body <= 0.12 and abs(ret3) <= 0.00025:
        return "tiny_range_flat"
    if up >= 0.35 and low >= 0.35 and body <= 0.35:
        return "upper_lower_wick_conflict"
    if body <= 0.20 and abs(ret3) <= 0.0006:
        return "small_body_mixed_wicks"
    if ret3 >= 0.0004 and ret3 <= 0.0022:
        return "weak_up_drift"
    if ret3 <= -0.0004 and ret3 >= -0.0022:
        return "weak_down_drift"
    if rng_ratio <= 0.45 and abs(ret3) <= 0.0005:
        return "inside_range_no_break"
    if abs(ret3) <= 0.0012 and "conflicting" in seq:
        return "alternating_direction_chop"
    return "unclassified_noise"


def build_micro_noise_profile_report(
    *,
    market_state_csv: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    if not market_state_csv.exists():
        return {"report_status": "blocked", "reason": "market_state_csv_missing", "market_state_csv": str(market_state_csv)}

    df = pd.read_csv(market_state_csv)
    if "micro_pattern_event_3" not in df.columns:
        return {"report_status": "blocked", "reason": "missing_micro_pattern_event_3"}

    total = int(len(df))
    noise = df[df["micro_pattern_event_3"].astype(str) == "micro_noise"].copy()
    noise_count = int(len(noise))
    noise_ratio = float(noise_count) / float(max(total, 1))

    if noise_count > 0:
        noise["noise_subtype"] = noise.apply(_classify_noise_subtype, axis=1)
        subtype_dist = {str(k): int(v) for k, v in noise["noise_subtype"].value_counts().items()}
    else:
        subtype_dist = {}

    dominant = sorted(subtype_dist.items(), key=lambda kv: kv[1], reverse=True)[:5]
    candidate_rule_suggestions = [k for k, _ in dominant if k not in {"unclassified_noise"}]
    recommended_rule_updates = [f"consider_rule_bucket:{k}" for k in candidate_rule_suggestions[:3]]
    manual_review_priority_subtypes = [k for k, _ in dominant]

    trial_status = "not_approved"
    if trial_approval_json.exists():
        trial_payload = _load_json(trial_approval_json) or {}
        trial_status = str(trial_payload.get("status", "not_approved"))

    rule_version = str(df.get("micro_pattern_rule_version", pd.Series(["unknown"])).dropna().astype(str).iloc[0]) if total > 0 else "unknown"

    report_status = "micro_noise_profile_ready"
    if trial_status != "not_approved":
        report_status = "blocked"

    return {
        "report_status": report_status,
        "input_row_count": total,
        "micro_noise_count": noise_count,
        "micro_noise_ratio": noise_ratio,
        "profile_sample_count": noise_count,
        "noise_subtype_distribution": subtype_dist,
        "candidate_rule_suggestions": candidate_rule_suggestions,
        "recommended_rule_updates": recommended_rule_updates,
        "manual_review_priority_subtypes": manual_review_priority_subtypes,
        "rule_version": rule_version,
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
    }


def render_micro_noise_profile_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EURUSD Micro Noise Profile",
            "",
            f"- report_status: `{report.get('report_status')}`",
            f"- micro_noise_count: `{report.get('micro_noise_count')}`",
            f"- micro_noise_ratio: `{report.get('micro_noise_ratio')}`",
            f"- rule_version: `{report.get('rule_version')}`",
            "",
            "## Noise Subtype Distribution",
            "",
            f"- {report.get('noise_subtype_distribution')}",
            "",
            "## Candidate Rule Suggestions",
            "",
            f"- {report.get('candidate_rule_suggestions')}",
        ]
    ) + "\n"
