"""EURUSD sampling source-range audit report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


RAW_DEFAULT = Path("/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv")


@dataclass
class TableSpan:
    exists: bool
    row_count: int
    min_ts: str | None
    max_ts: str | None
    years: list[int]
    error: str | None = None


def _pick_timestamp_column(df: pd.DataFrame) -> str | None:
    if "timestamp" in df.columns:
        return "timestamp"
    if "Time (UTC)" in df.columns:
        return "Time (UTC)"
    if "time" in df.columns:
        return "time"
    return df.columns[0] if len(df.columns) > 0 else None


def _read_span(path: Path) -> TableSpan:
    if not path.exists():
        return TableSpan(False, 0, None, None, [])
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return TableSpan(True, 0, None, None, [], error=str(exc))
    ts_col = _pick_timestamp_column(df)
    if ts_col is None:
        return TableSpan(True, int(len(df)), None, None, [], error="no_columns")
    ts = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    ts_valid = ts.dropna()
    years = sorted({int(x) for x in ts_valid.dt.year.tolist()})
    min_ts = ts_valid.min().isoformat() if not ts_valid.empty else None
    max_ts = ts_valid.max().isoformat() if not ts_valid.empty else None
    return TableSpan(True, int(len(df)), min_ts, max_ts, years)


def _span_days(start_iso: str | None, end_iso: str | None) -> float | None:
    if not start_iso or not end_iso:
        return None
    start = pd.to_datetime(start_iso, utc=True, errors="coerce")
    end = pd.to_datetime(end_iso, utc=True, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        return None
    return float((end - start).total_seconds() / 86400.0)


def build_validation_eurusd_sampling_source_range(
    *,
    raw_source_path: Path = RAW_DEFAULT,
    clean_view_path: Path = Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"),
    candidate_path: Path = Path("tmp/eurusd/EURUSD_15m_pattern_candidates.csv"),
    template_path: Path = Path("tmp/eurusd/EURUSD_15m_pattern_review_template.csv"),
    batch_path: Path = Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"),
    expected_start_year: int = 2020,
    expected_end_year: int = 2024,
) -> dict[str, Any]:
    raw = _read_span(raw_source_path)
    clean = _read_span(clean_view_path)
    cand = _read_span(candidate_path)
    templ = _read_span(template_path)
    batch = _read_span(batch_path)

    warnings: list[str] = []
    truncation = False

    expected_years = set(range(expected_start_year, expected_end_year + 1))
    raw_years = set(raw.years)
    raw_full = expected_years.issubset(raw_years)

    if not raw.exists:
        status = "raw_source_missing"
    elif raw.error:
        status = "blocked"
        warnings.append("raw_source_unreadable")
    else:
        status = "full_range_ready"

        for name, span in [("clean_view", clean), ("candidate", cand), ("template", templ), ("batch", batch)]:
            if span.exists and span.error:
                status = "blocked"
                warnings.append(f"{name}_unreadable")

        if not raw_full:
            status = "watch"
            warnings.append("raw_source_missing_expected_years")

        raw_days = _span_days(raw.min_ts, raw.max_ts)
        for name, span in [("candidate", cand), ("template", templ), ("batch", batch)]:
            if not span.exists or span.error or not span.min_ts or not span.max_ts:
                continue
            derived_days = _span_days(span.min_ts, span.max_ts)
            if raw_days and derived_days is not None and raw_days > 365 and derived_days < 180:
                truncation = True
                warnings.append(f"{name}_span_lt_180_days")
            if span.max_ts and raw.max_ts:
                if pd.to_datetime(span.max_ts, utc=True) < (pd.to_datetime(raw.max_ts, utc=True) - pd.Timedelta(days=365)):
                    truncation = True
                    warnings.append(f"{name}_max_far_before_raw_max")

        if truncation:
            status = "derived_artifacts_truncated"
        elif warnings and status != "blocked":
            status = "watch"

    next_action = {
        "raw_source_missing": "provide_expected_raw_source",
        "blocked": "fix_unreadable_inputs",
        "derived_artifacts_truncated": "rebuild_candidates_template_batch_from_full_clean_view",
        "watch": "review_sampling_coverage_warnings",
        "full_range_ready": "continue_manual_review_without_reset",
    }[status]

    return {
        "status": status,
        "raw_source_path": str(raw_source_path),
        "raw_exists": raw.exists,
        "raw_row_count": raw.row_count,
        "raw_min_timestamp": raw.min_ts,
        "raw_max_timestamp": raw.max_ts,
        "clean_view_path": str(clean_view_path),
        "clean_view_row_count": clean.row_count,
        "clean_view_min_timestamp": clean.min_ts,
        "clean_view_max_timestamp": clean.max_ts,
        "candidate_path": str(candidate_path),
        "candidate_count": cand.row_count,
        "candidate_min_timestamp": cand.min_ts,
        "candidate_max_timestamp": cand.max_ts,
        "template_path": str(template_path),
        "template_count": templ.row_count,
        "template_min_timestamp": templ.min_ts,
        "template_max_timestamp": templ.max_ts,
        "batch_path": str(batch_path),
        "batch_count": batch.row_count,
        "batch_min_timestamp": batch.min_ts,
        "batch_max_timestamp": batch.max_ts,
        "year_coverage": raw.years,
        "candidate_year_coverage": cand.years,
        "template_year_coverage": templ.years,
        "batch_year_coverage": batch.years,
        "coverage_warnings": sorted(set(warnings)),
        "likely_truncation_detected": truncation,
        "next_action": next_action,
        "scope_boundary": {
            "review_sampling_audit_only": True,
            "reset_or_regenerate_performed": False,
            "trading_signal": False,
            "order_generation": False,
        },
    }


def render_validation_eurusd_sampling_source_range_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation EURUSD Sampling Source Range",
            "",
            f"- status: `{payload.get('status')}`",
            f"- raw_source_path: `{payload.get('raw_source_path')}`",
            f"- raw_row_count: `{payload.get('raw_row_count')}`",
            f"- raw_min_timestamp: `{payload.get('raw_min_timestamp')}`",
            f"- raw_max_timestamp: `{payload.get('raw_max_timestamp')}`",
            f"- clean_view_row_count: `{payload.get('clean_view_row_count')}`",
            f"- candidate_count: `{payload.get('candidate_count')}`",
            f"- template_count: `{payload.get('template_count')}`",
            f"- batch_count: `{payload.get('batch_count')}`",
            f"- likely_truncation_detected: `{payload.get('likely_truncation_detected')}`",
            f"- coverage_warnings: `{payload.get('coverage_warnings')}`",
            f"- next_action: `{payload.get('next_action')}`",
            "",
            "## Policy",
            "",
            "- Read-only sampling audit.",
            "- No batch reset/regeneration is performed by this report.",
            "- No trading signal or order logic.",
            "",
        ]
    )
