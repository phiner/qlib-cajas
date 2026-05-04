"""EURUSD pattern review sample QA report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

KNOWN_TYPES = {
    "compression_candidate",
    "expansion_candidate",
    "short_trend_up_candidate",
    "short_trend_down_candidate",
    "mid_trend_up_candidate",
    "mid_trend_down_candidate",
    "upper_wick_rejection_candidate",
    "lower_wick_rejection_candidate",
    "doji_indecision_candidate",
    "possible_false_breakout_candidate",
}
REQUIRED_SAMPLE_COLUMNS = {"timestamp", "candidate_type", "confidence_score", "reason_codes", "review_priority"}
FORBIDDEN = {"buy", "sell", "long", "short", "order", "position", "target_position", "signal", "entry", "exit"}


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        return pd.DataFrame(rows)
    return pd.read_csv(path)


def build_validation_eurusd_pattern_review_qa(
    *,
    candidates_csv: Path,
    samples_path: Path,
    candidate_pack_report: Path,
    clean_view_csv: Path | None = None,
    expected_max_samples_per_type: int = 50,
) -> dict[str, Any]:
    if not candidates_csv.exists() or not samples_path.exists() or not candidate_pack_report.exists():
        return {
            "schema_version": 1,
            "status": "blocked",
            "blocking_reasons": ["missing_required_input"],
        }

    candidates = pd.read_csv(candidates_csv)
    samples = _read_table(samples_path)
    _ = json.loads(candidate_pack_report.read_text(encoding="utf-8"))

    missing_cols = sorted(REQUIRED_SAMPLE_COLUMNS.difference(samples.columns))
    forbidden_hits = [c for c in samples.columns if c.lower() in FORBIDDEN]

    sample_count = int(len(samples))
    candidate_count = int(len(candidates))

    sample_by_type = samples["candidate_type"].value_counts().to_dict() if "candidate_type" in samples.columns else {}
    candidate_by_type = candidates["candidate_type"].value_counts().to_dict() if "candidate_type" in candidates.columns else {}

    duplicate_count = 0
    if {"timestamp", "candidate_type", "source_row_index"}.issubset(samples.columns):
        duplicate_count = int(samples.duplicated(subset=["timestamp", "candidate_type", "source_row_index"]).sum())
    elif {"timestamp", "candidate_type"}.issubset(samples.columns):
        duplicate_count = int(samples.duplicated(subset=["timestamp", "candidate_type"]).sum())

    conf_invalid = 0
    if "confidence_score" in samples.columns:
        conf = pd.to_numeric(samples["confidence_score"], errors="coerce")
        conf_invalid = int(((conf < 0) | (conf > 1) | conf.isna()).sum())

    unknown_types = sorted(set(samples.get("candidate_type", pd.Series(dtype=str)).dropna().astype(str)) - KNOWN_TYPES)

    missing_clean_ts = 0
    if clean_view_csv is not None and clean_view_csv.exists() and "timestamp" in samples.columns:
        clean = pd.read_csv(clean_view_csv, usecols=["timestamp"]) if clean_view_csv.exists() else pd.DataFrame(columns=["timestamp"])
        clean_ts = set(pd.to_datetime(clean["timestamp"], errors="coerce", utc=True).dropna().astype(str))
        s_ts = pd.to_datetime(samples["timestamp"], errors="coerce", utc=True)
        missing_clean_ts = int((~s_ts.astype(str).isin(clean_ts)).sum())

    reason_cov: dict[str, int] = {}
    if "reason_codes" in samples.columns:
        for val in samples["reason_codes"].fillna(""):
            for r in [x for x in str(val).split("|") if x]:
                reason_cov[r] = reason_cov.get(r, 0) + 1

    prio_dist = samples["review_priority"].fillna("missing").astype(str).value_counts().to_dict() if "review_priority" in samples.columns else {}

    balance_warn = any(v > expected_max_samples_per_type for v in sample_by_type.values())

    blockers: list[str] = []
    warnings: list[str] = []
    if missing_cols:
        blockers.append("missing_required_columns")
    if forbidden_hits:
        blockers.append("forbidden_trading_columns")
    if conf_invalid > 0:
        blockers.append("invalid_confidence_scores")
    if duplicate_count > 0:
        warnings.append("duplicate_samples_detected")
    if unknown_types:
        warnings.append("unknown_candidate_types")
    if balance_warn:
        warnings.append("sample_balance_exceeds_expected_max")

    status = "ready"
    if blockers:
        status = "blocked"
    elif warnings:
        status = "watch"

    return {
        "schema_version": 1,
        "status": status,
        "sample_count": sample_count,
        "candidate_count": candidate_count,
        "sample_count_by_type": sample_by_type,
        "candidate_count_by_type": candidate_by_type,
        "known_candidate_types": sorted(KNOWN_TYPES),
        "unknown_candidate_types": unknown_types,
        "duplicate_sample_count": duplicate_count,
        "forbidden_trading_column_hits": forbidden_hits,
        "confidence_invalid_count": conf_invalid,
        "missing_clean_view_timestamp_count": missing_clean_ts,
        "reason_code_coverage": reason_cov,
        "review_priority_distribution": prio_dist,
        "blocking_reasons": blockers,
        "warnings": warnings,
        "recommendation": "start_manual_review" if status in {"ready", "watch"} else "fix_review_pack_qa",
    }


def render_validation_eurusd_pattern_review_qa_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation EURUSD Pattern Review QA",
        "",
        f"- status: `{payload.get('status')}`",
        f"- sample_count: `{payload.get('sample_count')}`",
        f"- candidate_count: `{payload.get('candidate_count')}`",
        f"- duplicate_sample_count: `{payload.get('duplicate_sample_count')}`",
        f"- confidence_invalid_count: `{payload.get('confidence_invalid_count')}`",
        f"- missing_clean_view_timestamp_count: `{payload.get('missing_clean_view_timestamp_count')}`",
        f"- recommendation: `{payload.get('recommendation')}`",
        "",
        "## Policy",
        "",
        "- Candidate samples are for human review only.",
        "- No trading signal/order columns are allowed.",
        "",
    ]
    return "\n".join(lines)
