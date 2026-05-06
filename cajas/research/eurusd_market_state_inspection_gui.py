"""Helpers for chart-first EURUSD market-state inspection and feedback persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from cajas.reports.validation_eurusd_market_state_inspection_packet import FEEDBACK_FIELDS

AGREEMENT_VALUES = {"", "agree", "disagree", "uncertain"}
FORBIDDEN_UPDATE_FIELDS = {
    "trade_signal",
    "entry",
    "exit",
    "order",
    "position_size",
    "target_position",
    "buy",
    "sell",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_feedback_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in FEEDBACK_FIELDS:
        if col not in out.columns:
            out[col] = ""
    return out


def load_inspection_packet(packet_csv: Path) -> pd.DataFrame:
    if not packet_csv.exists():
        raise FileNotFoundError(f"inspection packet not found: {packet_csv}")
    df = pd.read_csv(packet_csv)
    if "sample_id" not in df.columns or "timestamp" not in df.columns:
        raise ValueError("inspection packet missing required columns: sample_id/timestamp")
    return _ensure_feedback_columns(df)


def load_raw_clean_csv(raw_csv: Path) -> pd.DataFrame:
    if not raw_csv.exists():
        raise FileNotFoundError(f"raw clean CSV not found: {raw_csv}")
    df = pd.read_csv(raw_csv)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"raw clean CSV missing required columns: {missing}")
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")
    out = out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return out


def load_completed_feedback(completed_csv: Path) -> pd.DataFrame:
    if not completed_csv.exists():
        return pd.DataFrame(columns=["sample_id"] + FEEDBACK_FIELDS)
    df = pd.read_csv(completed_csv)
    if "sample_id" not in df.columns:
        raise ValueError("completed feedback CSV missing sample_id")
    return _ensure_feedback_columns(df)


def _latest_by_sample_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["sample_id"] = out["sample_id"].astype(str)
    out["review_updated_at_utc"] = out["review_updated_at_utc"].fillna("").astype(str)
    return out.sort_values(["sample_id", "review_updated_at_utc"]).drop_duplicates("sample_id", keep="last")


def merge_packet_with_completed(packet_df: pd.DataFrame, completed_df: pd.DataFrame) -> pd.DataFrame:
    packet = _ensure_feedback_columns(packet_df)
    if completed_df.empty:
        return packet
    completed = _latest_by_sample_id(_ensure_feedback_columns(completed_df))
    by_id = completed.set_index("sample_id")[FEEDBACK_FIELDS].to_dict(orient="index")
    out = packet.copy()
    for idx, row in out.iterrows():
        sid = str(row["sample_id"])
        if sid in by_id:
            for col in FEEDBACK_FIELDS:
                out.at[idx, col] = by_id[sid].get(col, "")
    return out


def compute_chart_window(raw_df: pd.DataFrame, timestamp: str, total_bars: int = 176) -> tuple[pd.DataFrame, int]:
    ts = pd.to_datetime(timestamp, utc=True, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"invalid timestamp: {timestamp}")
    matches = raw_df.index[raw_df["timestamp"] == ts].tolist()
    if not matches:
        raise ValueError(f"timestamp not found in raw dataset: {timestamp}")
    target_idx = int(matches[0])
    left = max(total_bars // 2, 128)
    right = max(16, total_bars - left - 1)
    start = max(0, target_idx - left)
    end = min(len(raw_df), target_idx + right + 1)
    window = raw_df.iloc[start:end].reset_index(drop=True)
    target_local_idx = target_idx - start
    return window, target_local_idx


def compute_layer_highlights(target_local_idx: int, sample_row: pd.Series | dict[str, Any]) -> dict[str, tuple[int, int]]:
    r = sample_row if isinstance(sample_row, dict) else sample_row.to_dict()

    def _rng(layer: str) -> tuple[int, int]:
        used = int(pd.to_numeric(r.get(f"{layer}_actual_bars_used", 0), errors="coerce") or 0)
        used = max(0, used)
        s = max(0, target_local_idx - used + 1)
        e = max(0, target_local_idx)
        return s, e

    return {
        "pattern_3": _rng("pattern_3"),
        "market_8": _rng("market_8"),
        "market_24": _rng("market_24"),
        "market_128": _rng("market_128"),
    }


def build_inspection_chart(window_df: pd.DataFrame, target_local_idx: int, highlights: dict[str, tuple[int, int]]) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=window_df["timestamp"],
                open=window_df["open"],
                high=window_df["high"],
                low=window_df["low"],
                close=window_df["close"],
                name="EURUSD 15m",
            )
        ]
    )
    colors = {
        "market_128": "rgba(80,80,80,0.10)",
        "market_24": "rgba(255,145,0,0.15)",
        "market_8": "rgba(0,140,255,0.18)",
        "pattern_3": "rgba(220,20,60,0.20)",
    }
    labels = {
        "market_128": "128",
        "market_24": "24",
        "market_8": "8",
        "pattern_3": "3",
    }
    for layer in ["market_128", "market_24", "market_8", "pattern_3"]:
        s, e = highlights[layer]
        if e < s or s >= len(window_df):
            continue
        s = max(0, min(s, len(window_df) - 1))
        e = max(0, min(e, len(window_df) - 1))
        fig.add_vrect(
            x0=window_df.iloc[s]["timestamp"],
            x1=window_df.iloc[e]["timestamp"],
            fillcolor=colors[layer],
            line_width=0,
            annotation_text=f"{labels[layer]} bars",
            annotation_position="top left",
        )
    if 0 <= target_local_idx < len(window_df):
        fig.add_vline(x=window_df.iloc[target_local_idx]["timestamp"], line_width=2, line_color="black")
    fig.update_layout(
        title="EURUSD Four-layer Market-state Inspection",
        xaxis_title="timestamp",
        yaxis_title="price",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )
    return fig


def default_feedback_values(row: pd.Series | dict[str, Any]) -> dict[str, str]:
    r = row if isinstance(row, dict) else row.to_dict()
    return {k: str(r.get(k, "") or "") for k in FEEDBACK_FIELDS}


def validate_feedback_update(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    keys_lower = {str(k).lower() for k in payload.keys()}
    forbidden = sorted(keys_lower.intersection(FORBIDDEN_UPDATE_FIELDS))
    if forbidden:
        errors.append(f"forbidden_fields_present:{','.join(forbidden)}")
    if not str(payload.get("sample_id", "")).strip():
        errors.append("sample_id_required")
    for col in [
        "human_pattern_3_agreement",
        "human_market_8_agreement",
        "human_market_24_agreement",
        "human_market_128_agreement",
        "human_local_structure_agreement",
    ]:
        value = str(payload.get(col, "")).strip()
        if value and value not in AGREEMENT_VALUES:
            errors.append(f"invalid_enum:{col}")
    return errors


def persist_feedback(
    row_update: dict[str, Any],
    completed_csv: Path,
    audit_jsonl: Path,
) -> dict[str, Any]:
    errors = validate_feedback_update(row_update)
    if errors:
        return {"status": "blocked", "errors": errors}

    now = _utc_now_iso()
    identity = {
        "sample_id": str(row_update.get("sample_id", "")).strip(),
        "timestamp": str(row_update.get("timestamp", "") or ""),
        "symbol": str(row_update.get("symbol", "") or ""),
        "timeframe": str(row_update.get("timeframe", "") or ""),
    }
    payload = {**identity}
    for col in FEEDBACK_FIELDS:
        payload[col] = str(row_update.get(col, "") or "").strip()
    payload["review_updated_at_utc"] = now

    existing = load_completed_feedback(completed_csv)
    merged = pd.concat([existing, pd.DataFrame([payload])], ignore_index=True)
    latest = _latest_by_sample_id(_ensure_feedback_columns(merged))
    completed_csv.parent.mkdir(parents=True, exist_ok=True)
    latest.to_csv(completed_csv, index=False)

    audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
    event = {"event_type": "market_state_inspection_feedback_saved", "event_time_utc": now, "payload": payload}
    with audit_jsonl.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"status": "ok", "sample_id": payload["sample_id"], "review_updated_at_utc": now}
