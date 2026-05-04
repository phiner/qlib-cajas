"""EURUSD 15m pattern candidate pack report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


TREND_TYPES = {"short_trend_up_candidate", "short_trend_down_candidate"}


def build_validation_eurusd_pattern_candidate_pack(
    *,
    clean_view_csv: Path,
    candidates_df: pd.DataFrame,
    samples_df: pd.DataFrame,
    output_candidates_csv: Path,
    output_samples_csv: Path,
    output_samples_jsonl: Path,
) -> dict[str, Any]:
    if not clean_view_csv.exists():
        return {
            "schema_version": 1,
            "status": "blocked",
            "input_clean_view_path": str(clean_view_csv),
            "blocking_reasons": ["clean_view_missing"],
        }

    row_count = int(len(pd.read_csv(clean_view_csv)))
    candidate_count = int(len(candidates_df))
    sample_count = int(len(samples_df))

    by_type = candidates_df["candidate_type"].value_counts().to_dict() if candidate_count else {}
    sample_by_type = samples_df["candidate_type"].value_counts().to_dict() if sample_count else {}

    status = "ready"
    if candidate_count <= 0:
        status = "blocked"
    else:
        expected = {
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
        present = set(by_type.keys())
        if len(expected.intersection(present)) < 6:
            status = "watch"

    timestamps = pd.to_datetime(candidates_df["timestamp"], errors="coerce", utc=True) if candidate_count else pd.Series(dtype="datetime64[ns, UTC]")

    trend_df = candidates_df[candidates_df["candidate_type"].isin(TREND_TYPES)].copy() if candidate_count and "candidate_type" in candidates_df.columns else pd.DataFrame()
    raw_trend_trigger_count = int(trend_df["segment_raw_trigger_count"].sum()) if "segment_raw_trigger_count" in trend_df.columns else int(len(trend_df))
    segment_count = int(trend_df["segment_id"].nunique()) if "segment_id" in trend_df.columns else 0
    representative_candidate_count = int(trend_df["representative_anchor"].fillna(False).astype(bool).sum()) if "representative_anchor" in trend_df.columns else 0
    same_segment_duplicate_suppressed_count = int(trend_df["segment_duplicate_suppressed_count"].sum()) if "segment_duplicate_suppressed_count" in trend_df.columns else 0
    late_segment_filtered_count = int(trend_df["late_segment_anchor"].fillna(False).astype(bool).sum()) if "late_segment_anchor" in trend_df.columns else 0
    rebound_filtered_count = int(trend_df["rebound_after_anchor"].fillna(False).astype(bool).sum()) if "rebound_after_anchor" in trend_df.columns else 0
    excluded_late_reversal_anchor_count = int(trend_df["excluded_late_reversal_anchor"].fillna(False).astype(bool).sum()) if "excluded_late_reversal_anchor" in trend_df.columns else 0
    preferred_review_candidate_count = int(trend_df["preferred_review_candidate"].fillna(True).astype(bool).sum()) if "preferred_review_candidate" in trend_df.columns else int(len(trend_df))
    avg_candidates_per_segment = float(len(trend_df) / segment_count) if segment_count > 0 else 0.0

    segment_count_by_direction: dict[str, int] = {}
    if not trend_df.empty and "segment_direction" in trend_df.columns and "segment_id" in trend_df.columns:
        segment_count_by_direction = {
            str(k): int(v)
            for k, v in trend_df.drop_duplicates(subset=["segment_id"])["segment_direction"].value_counts().to_dict().items()
        }

    trend_candidate_quality_distribution = {
        "preferred_review_candidate_true": preferred_review_candidate_count,
        "preferred_review_candidate_false": int(len(trend_df) - preferred_review_candidate_count),
        "excluded_late_reversal_anchor_true": excluded_late_reversal_anchor_count,
        "late_segment_anchor_true": late_segment_filtered_count,
        "rebound_after_anchor_true": rebound_filtered_count,
    }

    return {
        "schema_version": 1,
        "status": status,
        "input_clean_view_path": str(clean_view_csv),
        "row_count": row_count,
        "candidate_count": candidate_count,
        "candidate_count_by_type": by_type,
        "sample_count_by_type": sample_by_type,
        "time_range": {
            "start": timestamps.min().isoformat() if len(timestamps.dropna()) else None,
            "end": timestamps.max().isoformat() if len(timestamps.dropna()) else None,
        },
        "horizons": [3, 5, 8, 13, 21, 34, 55],
        "pattern_candidate_count": candidate_count,
        "trend_segment_metrics": {
            "raw_trend_trigger_count": raw_trend_trigger_count,
            "segment_count": segment_count,
            "representative_candidate_count": representative_candidate_count,
            "same_segment_duplicate_suppressed_count": same_segment_duplicate_suppressed_count,
            "late_segment_filtered_count": late_segment_filtered_count,
            "rebound_filtered_count": rebound_filtered_count,
            "excluded_late_reversal_anchor_count": excluded_late_reversal_anchor_count,
            "preferred_review_candidate_count": preferred_review_candidate_count,
            "average_candidates_per_segment": round(avg_candidates_per_segment, 6),
            "segment_count_by_direction": segment_count_by_direction,
            "trend_candidate_quality_distribution": trend_candidate_quality_distribution,
            "late_rebound_filtered_count": int(late_segment_filtered_count + rebound_filtered_count),
        },
        "scope_boundary": {
            "candidate_review_only": True,
            "trading_signals": False,
            "order_generation": False,
            "aggregation": False,
        },
        "output_paths": {
            "candidates_csv": str(output_candidates_csv),
            "samples_csv": str(output_samples_csv),
            "samples_jsonl": str(output_samples_jsonl),
        },
        "recommendation": "review_candidate_samples",
    }


def render_validation_eurusd_pattern_candidate_pack_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation EURUSD Pattern Candidate Pack",
        "",
        f"- status: `{payload.get('status')}`",
        f"- candidate_count: `{payload.get('candidate_count')}`",
        f"- input_clean_view_path: `{payload.get('input_clean_view_path')}`",
        "",
        "## Candidate Count By Type",
        "",
    ]
    for k, v in sorted((payload.get("candidate_count_by_type") or {}).items()):
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(
        [
            "",
            "## Segment Metrics",
            "",
        ]
    )
    seg = payload.get("trend_segment_metrics", {}) or {}
    for key in [
        "raw_trend_trigger_count",
        "segment_count",
        "representative_candidate_count",
        "same_segment_duplicate_suppressed_count",
        "late_segment_filtered_count",
        "rebound_filtered_count",
        "excluded_late_reversal_anchor_count",
        "preferred_review_candidate_count",
        "late_rebound_filtered_count",
    ]:
        lines.append(f"- `{key}`: `{seg.get(key)}`")
    lines.extend(
        [
            "",
            "## Sample Count By Type",
            "",
        ]
    )
    for k, v in sorted((payload.get("sample_count_by_type") or {}).items()):
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Candidate samples are for review only.",
            "- Candidate tags are not trading signals and do not create orders.",
            "- Fixed EURUSD 15m Bid scope; no aggregation.",
            "",
        ]
    )
    return "\n".join(lines)
