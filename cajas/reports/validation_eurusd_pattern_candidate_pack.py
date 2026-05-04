"""EURUSD 15m pattern candidate pack report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


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
