"""EURUSD 15m Bid dataset audit report."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_CANONICAL_COLUMNS = ["timestamp", "open", "high", "low", "close"]
OPTIONAL_CANONICAL_COLUMNS = ["volume", "spread", "source"]


def _norm_key(raw: str) -> str:
    return "".join(ch for ch in raw.lower() if ch.isalnum())


def _canonical_column(raw: str) -> str:
    key = _norm_key(raw)
    if key in {"time", "timeutc", "timestamp", "datetime", "date"}:
        return "timestamp"
    if key in {"open", "o"}:
        return "open"
    if key in {"high", "h"}:
        return "high"
    if key in {"low", "l"}:
        return "low"
    if key in {"close", "c"}:
        return "close"
    if key in {"volume", "vol", "tickvolume"}:
        return "volume"
    if key == "spread":
        return "spread"
    if key == "source":
        return "source"
    return key


def _load_one(path: Path, *, min_rows: int) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "status": "blocked",
            "blocking_reasons": ["file_missing"],
        }

    raw_df = pd.read_csv(path)
    rename_map = {c: _canonical_column(c) for c in raw_df.columns}
    df = raw_df.rename(columns=rename_map)

    missing_required = [c for c in REQUIRED_CANONICAL_COLUMNS if c not in df.columns]
    if missing_required:
        return {
            "path": str(path),
            "status": "blocked",
            "missing_required_columns": missing_required,
            "blocking_reasons": ["required_columns_missing"],
            "column_mapping": rename_map,
        }

    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", utc=True)
    for col in ["open", "high", "low", "close"]:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    row_count = int(len(work))
    invalid_ts = int(work["timestamp"].isna().sum())
    missing_ohlc = {c: int(work[c].isna().sum()) for c in ["open", "high", "low", "close"]}

    work = work.sort_values("timestamp").reset_index(drop=True)
    duplicate_timestamps = int(work["timestamp"].duplicated().sum())

    invalid_ohlc_mask = (
        (work["high"] < work[["open", "close", "low"]].max(axis=1))
        | (work["low"] > work[["open", "close", "high"]].min(axis=1))
    )
    invalid_ohlc_count = int(invalid_ohlc_mask.fillna(False).sum())

    valid_ts = work["timestamp"].dropna()
    start_ts = valid_ts.iloc[0].isoformat() if not valid_ts.empty else None
    end_ts = valid_ts.iloc[-1].isoformat() if not valid_ts.empty else None

    deltas = valid_ts.diff().dropna().dt.total_seconds() / 60.0
    median_interval_min = float(deltas.median()) if not deltas.empty else None
    inferred_frequency = f"{int(median_interval_min)}m" if median_interval_min and math.isfinite(median_interval_min) else None

    gap_threshold = (median_interval_min or 15.0) * 1.5
    large_gaps = deltas[deltas > gap_threshold]
    gap_summary = {
        "count": int(large_gaps.shape[0]),
        "threshold_minutes": float(gap_threshold),
        "max_gap_minutes": float(large_gaps.max()) if not large_gaps.empty else 0.0,
    }

    close = work["close"].dropna()
    rets = close.pct_change().dropna()
    return_summary = {
        "count": int(rets.shape[0]),
        "mean": float(rets.mean()) if not rets.empty else 0.0,
        "std": float(rets.std(ddof=0)) if not rets.empty else 0.0,
        "min": float(rets.min()) if not rets.empty else 0.0,
        "max": float(rets.max()) if not rets.empty else 0.0,
    }

    close_precision_dp = int(
        close.astype(str).str.split(".").str[1].fillna("").str.len().clip(lower=0).median()
    ) if not close.empty else 0

    optional_missing = [c for c in OPTIONAL_CANONICAL_COLUMNS if c not in work.columns]

    status = "ready"
    blocking_reasons: list[str] = []
    watch_reasons: list[str] = []
    if row_count < min_rows:
        status = "blocked"
        blocking_reasons.append("too_few_rows")
    if invalid_ts > 0:
        status = "blocked"
        blocking_reasons.append("invalid_timestamp_rows")
    if any(v > 0 for v in missing_ohlc.values()):
        status = "blocked"
        blocking_reasons.append("missing_ohlc_values")
    if invalid_ohlc_count > 0:
        status = "blocked"
        blocking_reasons.append("invalid_ohlc_relations")
    if duplicate_timestamps > 0:
        status = "blocked"
        blocking_reasons.append("duplicate_timestamps")

    if status != "blocked":
        if optional_missing:
            status = "watch"
            watch_reasons.append("optional_columns_missing")
        if gap_summary["count"] > 0:
            status = "watch"
            watch_reasons.append("large_gaps_detected")

    return {
        "path": str(path),
        "status": status,
        "blocking_reasons": blocking_reasons,
        "watch_reasons": watch_reasons,
        "symbol": "EURUSD",
        "timeframe": "15m",
        "price_side": "Bid",
        "column_mapping": rename_map,
        "row_count": row_count,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "inferred_frequency": inferred_frequency,
        "median_bar_interval_minutes": median_interval_min,
        "duplicate_timestamp_count": duplicate_timestamps,
        "missing_ohlc_counts": missing_ohlc,
        "invalid_timestamp_count": invalid_ts,
        "invalid_ohlc_relation_count": invalid_ohlc_count,
        "gap_summary": gap_summary,
        "price_range_summary": {
            "open_min": float(work["open"].min()) if row_count else None,
            "open_max": float(work["open"].max()) if row_count else None,
            "high_min": float(work["high"].min()) if row_count else None,
            "high_max": float(work["high"].max()) if row_count else None,
            "low_min": float(work["low"].min()) if row_count else None,
            "low_max": float(work["low"].max()) if row_count else None,
            "close_min": float(work["close"].min()) if row_count else None,
            "close_max": float(work["close"].max()) if row_count else None,
            "close_precision_decimal_places_median": close_precision_dp,
        },
        "return_summary": return_summary,
        "optional_columns_missing": optional_missing,
    }


def build_validation_eurusd_dataset_audit(
    *,
    input_paths: list[Path],
    min_rows: int = 20,
) -> dict[str, Any]:
    per_file = [_load_one(p, min_rows=min_rows) for p in input_paths]

    blocked = [x for x in per_file if x.get("status") == "blocked"]
    watch = [x for x in per_file if x.get("status") == "watch"]

    overall_status = "ready"
    if blocked:
        overall_status = "blocked"
    elif watch:
        overall_status = "watch"

    with_rows = [x for x in per_file if isinstance(x.get("row_count"), int) and int(x.get("row_count", 0)) > 0]
    combined_start = min((x.get("start_timestamp") for x in with_rows if x.get("start_timestamp")), default=None)
    combined_end = max((x.get("end_timestamp") for x in with_rows if x.get("end_timestamp")), default=None)
    combined_rows = sum(int(x.get("row_count", 0)) for x in with_rows)

    return {
        "schema_version": 1,
        "status": overall_status,
        "symbol": "EURUSD",
        "timeframe": "15m",
        "price_side": "Bid",
        "inputs": [str(p) for p in input_paths],
        "files": per_file,
        "combined_coverage": {
            "row_count": combined_rows,
            "start_timestamp": combined_start,
            "end_timestamp": combined_end,
            "file_count": len(input_paths),
        },
        "policy": {"min_rows_per_file": int(min_rows)},
    }


def render_validation_eurusd_dataset_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation EURUSD Dataset Audit",
        "",
        f"- status: `{payload.get('status')}`",
        f"- symbol: `{payload.get('symbol')}`",
        f"- timeframe: `{payload.get('timeframe')}`",
        "",
        "## Combined Coverage",
        "",
    ]
    c = payload.get("combined_coverage", {})
    lines.extend(
        [
            f"- row_count: `{c.get('row_count')}`",
            f"- start_timestamp: `{c.get('start_timestamp')}`",
            f"- end_timestamp: `{c.get('end_timestamp')}`",
            f"- file_count: `{c.get('file_count')}`",
            "",
            "## Per File",
            "",
        ]
    )
    for f in payload.get("files", []):
        lines.extend(
            [
                f"- path: `{f.get('path')}`",
                f"  status=`{f.get('status')}` rows=`{f.get('row_count')}` dup_ts=`{f.get('duplicate_timestamp_count')}` invalid_ohlc=`{f.get('invalid_ohlc_relation_count')}` gaps=`{(f.get('gap_summary') or {}).get('count')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Fixed to EURUSD 15m Bid research input.",
            "- No aggregation and no trading execution scope.",
            "",
        ]
    )
    return "\n".join(lines)
