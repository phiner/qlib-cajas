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
EXPECTED_INTERVAL_MINUTES = 15
GAP_THRESHOLD_BARS = 4


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


def detect_time_axis_gaps(
    timestamps: list[Any],
    expected_interval_minutes: int = EXPECTED_INTERVAL_MINUTES,
    gap_threshold_bars: int = GAP_THRESHOLD_BARS,
) -> list[dict[str, Any]]:
    """Detect large market-closed or missing-data gaps on a compressed axis."""
    out: list[dict[str, Any]] = []
    threshold_minutes = expected_interval_minutes * gap_threshold_bars
    normalized = [pd.to_datetime(ts, utc=True, errors="coerce") for ts in timestamps]
    for idx in range(len(normalized) - 1):
        prev_ts = normalized[idx]
        next_ts = normalized[idx + 1]
        if pd.isna(prev_ts) or pd.isna(next_ts):
            continue
        gap_minutes = float((next_ts - prev_ts).total_seconds() / 60.0)
        if gap_minutes <= threshold_minutes:
            continue
        prev_wd = int(prev_ts.weekday())
        next_wd = int(next_ts.weekday())
        if prev_wd == 4 and next_wd in {6, 0} and gap_minutes >= 24 * 60:
            label = "weekend gap"
        elif gap_minutes >= 24 * 60:
            label = "market closed"
        else:
            label = "time gap"
        out.append(
            {
                "prev_index": idx,
                "next_index": idx + 1,
                "gap_minutes": gap_minutes,
                "gap_hours": gap_minutes / 60.0,
                "start_timestamp": str(prev_ts),
                "end_timestamp": str(next_ts),
                "label": f"{label} {gap_minutes/60.0:.1f}h",
                "display_x": idx + 0.5,
            }
        )
    return out


def build_compressed_time_axis(window_df: pd.DataFrame) -> dict[str, Any]:
    ts_list = window_df["timestamp"].tolist()
    display_x = list(range(len(ts_list)))
    gaps = detect_time_axis_gaps(ts_list)
    tickvals: list[int] = []
    ticktext: list[str] = []
    if ts_list:
        step = max(1, len(ts_list) // 8)
        for i in range(0, len(ts_list), step):
            tickvals.append(i)
            ticktext.append(str(pd.to_datetime(ts_list[i], utc=True, errors="coerce"))[5:16])
        if tickvals[-1] != len(ts_list) - 1:
            tickvals.append(len(ts_list) - 1)
            ticktext.append(str(pd.to_datetime(ts_list[-1], utc=True, errors="coerce"))[5:16])
    return {
        "display_axis": "compressed_gap_axis",
        "display_x": display_x,
        "tickvals": tickvals,
        "ticktext": ticktext,
        "gap_markers": gaps,
        "raw_time_axis_preserved_in_hover": True,
    }


def build_layer_summary(sample_row: pd.Series | dict[str, Any]) -> list[dict[str, str]]:
    r = sample_row if isinstance(sample_row, dict) else sample_row.to_dict()
    return [
        {"layer": "pattern_3", "state": str(r.get("pattern_3_event", "")), "actual_bars": str(r.get("pattern_3_actual_bars_used", ""))},
        {"layer": "market_8", "state": str(r.get("market_8_state", "")), "actual_bars": str(r.get("market_8_actual_bars_used", ""))},
        {"layer": "market_24", "state": str(r.get("market_24_state", "")), "actual_bars": str(r.get("market_24_actual_bars_used", ""))},
        {"layer": "market_128", "state": str(r.get("market_128_state", "")), "actual_bars": str(r.get("market_128_actual_bars_used", ""))},
        {"layer": "local_structure", "state": str(r.get("local_structure_state", "")), "actual_bars": str(r.get("market_128_actual_bars_used", ""))},
    ]


def build_inspection_chart(window_df: pd.DataFrame, target_local_idx: int, highlights: dict[str, tuple[int, int]]) -> go.Figure:
    axis_info = build_compressed_time_axis(window_df)
    x = axis_info["display_x"]
    ts_text = [str(ts) for ts in window_df["timestamp"].tolist()]
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=x,
                open=window_df["open"],
                high=window_df["high"],
                low=window_df["low"],
                close=window_df["close"],
                name="EURUSD 15m",
                customdata=ts_text,
                hovertemplate=(
                    "bar=%{x}<br>"
                    "timestamp=%{customdata}<br>"
                    "open=%{open}<br>"
                    "high=%{high}<br>"
                    "low=%{low}<br>"
                    "close=%{close}<extra></extra>"
                ),
            )
        ]
    )
    colors = {
        "market_128": "rgba(40,60,90,0.22)",
        "market_24": "rgba(255,145,0,0.20)",
        "market_8": "rgba(0,140,255,0.24)",
        "pattern_3": "rgba(220,20,60,0.30)",
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
            x0=s,
            x1=e,
            fillcolor=colors[layer],
            line_width=1,
            line_color="rgba(0,0,0,0.30)",
            annotation_text=f"{labels[layer]} bars",
            annotation_position="top left",
            annotation_font_size=12,
        )
    for gap in axis_info.get("gap_markers", []):
        gx = float(gap["display_x"])
        fig.add_vline(x=gx, line_width=1, line_dash="dot", line_color="rgba(90,90,90,0.8)")
        fig.add_annotation(
            x=gx,
            y=1.03,
            yref="paper",
            text=str(gap["label"]),
            showarrow=False,
            font={"size": 12, "color": "#444"},
        )
    if 0 <= target_local_idx < len(window_df):
        fig.add_vline(x=target_local_idx, line_width=2, line_color="black")
    fig.update_layout(
        title="EURUSD Four-layer Market-state Inspection",
        xaxis_title="Compressed candle axis (timestamps in hover)",
        yaxis_title="price",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )
    if axis_info.get("tickvals") and axis_info.get("ticktext"):
        fig.update_xaxes(tickmode="array", tickvals=axis_info["tickvals"], ticktext=axis_info["ticktext"])
    fig.update_layout(meta={"axis_info": axis_info})
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
