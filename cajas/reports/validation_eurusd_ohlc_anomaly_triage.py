"""EURUSD 15m OHLC anomaly triage report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED = ["timestamp", "open", "high", "low", "close"]


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


def _violations(row: pd.Series) -> list[str]:
    v: list[str] = []
    o = row.get("open")
    h = row.get("high")
    l = row.get("low")
    c = row.get("close")

    if pd.isna(o):
        v.append("missing_open")
    if pd.isna(h):
        v.append("missing_high")
    if pd.isna(l):
        v.append("missing_low")
    if pd.isna(c):
        v.append("missing_close")

    if pd.notna(h) and pd.notna(o) and h < o:
        v.append("high_lt_open")
    if pd.notna(h) and pd.notna(c) and h < c:
        v.append("high_lt_close")
    if pd.notna(h) and pd.notna(l) and h < l:
        v.append("high_lt_low")
    if pd.notna(l) and pd.notna(o) and l > o:
        v.append("low_gt_open")
    if pd.notna(l) and pd.notna(c) and l > c:
        v.append("low_gt_close")
    if pd.notna(l) and pd.notna(h) and l > h:
        v.append("low_gt_high")
    return v


def build_validation_eurusd_ohlc_anomaly_triage(
    *,
    input_paths: list[Path],
    symbol: str = "EURUSD",
    timeframe: str = "15m",
    price_side: str = "Bid",
) -> dict[str, Any]:
    anomalies: list[dict[str, Any]] = []
    total_rows = 0
    by_file: dict[str, int] = {}
    by_type: dict[str, int] = {}

    for path in input_paths:
        if not path.exists():
            continue
        raw_df = pd.read_csv(path)
        total_rows += int(len(raw_df))
        mapped = raw_df.rename(columns={c: _canonical_column(c) for c in raw_df.columns}).copy()

        if "timestamp" not in mapped.columns:
            mapped["timestamp"] = pd.NaT
            raw_ts_col = None
        else:
            raw_ts_col = next((c for c in raw_df.columns if _canonical_column(c) == "timestamp"), None)
            mapped["timestamp"] = pd.to_datetime(mapped["timestamp"], errors="coerce", utc=True)

        for col in ["open", "high", "low", "close"]:
            if col not in mapped.columns:
                mapped[col] = pd.NA
            else:
                mapped[col] = pd.to_numeric(mapped[col], errors="coerce")

        for idx, row in mapped.iterrows():
            vio = _violations(row)
            if not vio:
                continue
            raw_ts = raw_df.iloc[idx][raw_ts_col] if raw_ts_col and raw_ts_col in raw_df.columns else None
            record = {
                "source_file": str(path),
                "source_row_index": int(idx),
                "normalized_timestamp": row["timestamp"].isoformat() if pd.notna(row["timestamp"]) else None,
                "raw_timestamp": None if pd.isna(raw_ts) else str(raw_ts),
                "open": None if pd.isna(row["open"]) else float(row["open"]),
                "high": None if pd.isna(row["high"]) else float(row["high"]),
                "low": None if pd.isna(row["low"]) else float(row["low"]),
                "close": None if pd.isna(row["close"]) else float(row["close"]),
                "violated_constraints": vio,
                "severity": "blocking",
                "suggested_action": "quarantine_row",
                "notes": "do_not_mutate_original_file",
            }
            anomalies.append(record)
            by_file[str(path)] = by_file.get(str(path), 0) + 1
            for x in vio:
                by_type[x] = by_type.get(x, 0) + 1

    ts = [x["normalized_timestamp"] for x in anomalies if x.get("normalized_timestamp")]
    status = "clean" if not anomalies else "blocked"

    return {
        "schema_version": 1,
        "status": status,
        "symbol": symbol,
        "timeframe": timeframe,
        "price_side": price_side,
        "inputs": [str(p) for p in input_paths],
        "total_input_rows": int(total_rows),
        "total_anomaly_rows": int(len(anomalies)),
        "anomaly_count_by_file": by_file,
        "anomaly_count_by_violation_type": by_type,
        "earliest_anomaly_timestamp": min(ts) if ts else None,
        "latest_anomaly_timestamp": max(ts) if ts else None,
        "recommendation": "create_clean_view",
        "anomalies": anomalies,
    }


def render_validation_eurusd_ohlc_anomaly_triage_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation EURUSD OHLC Anomaly Triage",
        "",
        f"- status: `{payload.get('status')}`",
        f"- total_input_rows: `{payload.get('total_input_rows')}`",
        f"- total_anomaly_rows: `{payload.get('total_anomaly_rows')}`",
        f"- earliest_anomaly_timestamp: `{payload.get('earliest_anomaly_timestamp')}`",
        f"- latest_anomaly_timestamp: `{payload.get('latest_anomaly_timestamp')}`",
        "",
        "## Counts By Violation",
        "",
    ]
    for k, v in sorted((payload.get("anomaly_count_by_violation_type") or {}).items()):
        lines.append(f"- `{k}`: `{v}`")
    lines.extend([
        "",
        "## Policy",
        "",
        "- Anomaly rows are quarantined; raw CSV files are not modified.",
        "- Use clean-view generation for downstream pattern research.",
        "",
    ])
    return "\n".join(lines)
