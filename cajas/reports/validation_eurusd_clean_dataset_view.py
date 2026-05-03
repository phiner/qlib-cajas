"""EURUSD 15m clean dataset view builder and report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.reports.validation_eurusd_dataset_audit import _canonical_column


def build_validation_eurusd_clean_dataset_view(
    *,
    input_paths: list[Path],
    anomaly_triage_report: Path,
    output_clean_csv: Path,
    output_quarantine_csv: Path,
    min_rows: int = 20,
) -> dict[str, Any]:
    triage = json.loads(anomaly_triage_report.read_text(encoding="utf-8"))
    anomaly_set = {
        (str(a.get("source_file")), int(a.get("source_row_index")))
        for a in triage.get("anomalies", [])
        if a.get("source_file") is not None and a.get("source_row_index") is not None
    }

    kept_frames: list[pd.DataFrame] = []
    quarantined_frames: list[pd.DataFrame] = []
    raw_rows = 0

    for path in input_paths:
        if not path.exists():
            continue
        raw = pd.read_csv(path)
        raw_rows += int(len(raw))
        normalized = raw.rename(columns={c: _canonical_column(c) for c in raw.columns}).copy()
        normalized["source_file"] = str(path)
        normalized["source_row_index"] = range(len(normalized))

        mask = normalized.apply(lambda r: (str(r["source_file"]), int(r["source_row_index"])) in anomaly_set, axis=1)
        quarantined_frames.append(normalized[mask].copy())
        kept_frames.append(normalized[~mask].copy())

    clean = pd.concat(kept_frames, ignore_index=True) if kept_frames else pd.DataFrame()
    quarantined = pd.concat(quarantined_frames, ignore_index=True) if quarantined_frames else pd.DataFrame()

    output_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(output_clean_csv, index=False)
    quarantined.to_csv(output_quarantine_csv, index=False)

    if not clean.empty:
        clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce", utc=True)
        for col in ["open", "high", "low", "close"]:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
        clean = clean.sort_values("timestamp").reset_index(drop=True)
        invalid_mask = (
            (clean["high"] < clean[["open", "close", "low"]].max(axis=1))
            | (clean["low"] > clean[["open", "close", "high"]].min(axis=1))
        )
        invalid_count = int(invalid_mask.fillna(False).sum())
        dup_count = int(clean["timestamp"].duplicated().sum())
        valid_ts = clean["timestamp"].dropna()
        start_ts = valid_ts.iloc[0].isoformat() if not valid_ts.empty else None
        end_ts = valid_ts.iloc[-1].isoformat() if not valid_ts.empty else None
        deltas = valid_ts.diff().dropna().dt.total_seconds() / 60.0
        gap_threshold = float(deltas.median() * 1.5) if not deltas.empty else 22.5
        gap_count = int((deltas > gap_threshold).sum()) if not deltas.empty else 0
        max_gap = float(deltas.max()) if not deltas.empty else 0.0
    else:
        invalid_count = 0
        dup_count = 0
        start_ts = None
        end_ts = None
        gap_threshold = 22.5
        gap_count = 0
        max_gap = 0.0

    clean_rows = int(len(clean))
    quarantined_rows = int(len(quarantined))
    removed_ratio = float(quarantined_rows / raw_rows) if raw_rows else 0.0

    status = "ready"
    if clean_rows < min_rows or invalid_count > 0 or dup_count > 0:
        status = "blocked"
    elif gap_count > 0 or quarantined_rows > 0:
        status = "watch"

    recommendation = "use_clean_view_for_pattern_research" if status in {"ready", "watch"} else "fix_dataset_source"

    reason_summary: dict[str, int] = {}
    for a in triage.get("anomalies", []):
        for v in a.get("violated_constraints", []):
            reason_summary[v] = reason_summary.get(v, 0) + 1

    return {
        "schema_version": 1,
        "status": status,
        "raw_row_count": raw_rows,
        "quarantined_row_count": quarantined_rows,
        "clean_row_count": clean_rows,
        "removed_ratio": removed_ratio,
        "clean_start_timestamp": start_ts,
        "clean_end_timestamp": end_ts,
        "clean_invalid_ohlc_relation_count": invalid_count,
        "clean_duplicate_timestamp_count": dup_count,
        "gap_summary_after_quarantine": {
            "count": gap_count,
            "threshold_minutes": gap_threshold,
            "max_gap_minutes": max_gap,
        },
        "quarantine_reason_summary": reason_summary,
        "output_paths": {
            "clean_csv": str(output_clean_csv),
            "quarantine_csv": str(output_quarantine_csv),
        },
        "recommendation": recommendation,
    }


def render_validation_eurusd_clean_dataset_view_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation EURUSD Clean Dataset View",
            "",
            f"- status: `{payload.get('status')}`",
            f"- raw_row_count: `{payload.get('raw_row_count')}`",
            f"- quarantined_row_count: `{payload.get('quarantined_row_count')}`",
            f"- clean_row_count: `{payload.get('clean_row_count')}`",
            f"- clean_invalid_ohlc_relation_count: `{payload.get('clean_invalid_ohlc_relation_count')}`",
            f"- clean_duplicate_timestamp_count: `{payload.get('clean_duplicate_timestamp_count')}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "",
            "## Output Paths",
            "",
            f"- clean_csv: `{(payload.get('output_paths') or {}).get('clean_csv')}`",
            f"- quarantine_csv: `{(payload.get('output_paths') or {}).get('quarantine_csv')}`",
            "",
            "## Policy",
            "",
            "- Raw CSV inputs are immutable and are not modified.",
            "- Quarantine is explicit and reviewable.",
            "",
        ]
    )
