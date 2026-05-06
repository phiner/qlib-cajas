"""Helpers for EURUSD micro-pattern packet manual labeling."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

LABEL_OPTIONS = [
    "true_noise",
    "inside_range_pause",
    "inside_range_chop",
    "weak_drift_up",
    "weak_drift_down",
    "micro_chop",
    "wick_conflict",
    "ambiguous_break",
    "directional_stall_up",
    "directional_stall_down",
    "possible_new_rule",
    "uncertain",
]
CONFIDENCE_OPTIONS = ["low", "medium", "high"]
SHOULD_CREATE_RULE_OPTIONS = ["yes", "no", "uncertain"]

REQUIRED_LABEL_FIELDS = [
    "human_micro_pattern_label",
    "human_micro_pattern_confidence",
    "human_micro_pattern_rationale_zh",
    "human_rule_suggestion_zh",
    "human_should_create_rule",
    "suggested_event_key",
    "review_updated_at_utc",
]

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


def _ensure_columns(df: pd.DataFrame, cols: list[str], default: str = "") -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = default
    return out


def load_micro_pattern_packet(packet_csv: Path) -> pd.DataFrame:
    if not packet_csv.exists():
        raise FileNotFoundError(f"packet CSV not found: {packet_csv}")
    df = pd.read_csv(packet_csv)
    if "sample_id" not in df.columns:
        raise ValueError("packet CSV missing required column: sample_id")
    return _ensure_columns(df, REQUIRED_LABEL_FIELDS)


def load_completed_micro_pattern_labels(completed_csv: Path) -> pd.DataFrame:
    if not completed_csv.exists():
        return pd.DataFrame(columns=["sample_id"] + REQUIRED_LABEL_FIELDS)
    df = pd.read_csv(completed_csv)
    if "sample_id" not in df.columns:
        raise ValueError("completed CSV missing required column: sample_id")
    return _ensure_columns(df, REQUIRED_LABEL_FIELDS)


def _latest_by_sample_id(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["sample_id"] = out["sample_id"].astype(str)
    out["review_updated_at_utc"] = out["review_updated_at_utc"].fillna("").astype(str)
    out = out.sort_values(["sample_id", "review_updated_at_utc"]).drop_duplicates("sample_id", keep="last")
    return out


def merge_packet_with_completed_labels(packet_df: pd.DataFrame, completed_df: pd.DataFrame) -> pd.DataFrame:
    packet = _ensure_columns(packet_df, REQUIRED_LABEL_FIELDS)
    if completed_df.empty:
        return packet
    completed = _latest_by_sample_id(_ensure_columns(completed_df, REQUIRED_LABEL_FIELDS))
    completed_map = completed.set_index("sample_id")[REQUIRED_LABEL_FIELDS].to_dict(orient="index")
    out = packet.copy()
    for idx, row in out.iterrows():
        sid = str(row["sample_id"])
        if sid in completed_map:
            for field in REQUIRED_LABEL_FIELDS:
                out.at[idx, field] = completed_map[sid].get(field, "")
    return out


def default_micro_pattern_label_values(row: dict[str, Any] | pd.Series) -> dict[str, str]:
    row_dict = dict(row)
    return {
        "human_micro_pattern_label": str(row_dict.get("human_micro_pattern_label", "") or ""),
        "human_micro_pattern_confidence": str(row_dict.get("human_micro_pattern_confidence", "") or ""),
        "human_micro_pattern_rationale_zh": str(row_dict.get("human_micro_pattern_rationale_zh", "") or ""),
        "human_rule_suggestion_zh": str(row_dict.get("human_rule_suggestion_zh", "") or ""),
        "human_should_create_rule": str(row_dict.get("human_should_create_rule", "") or ""),
        "suggested_event_key": str(row_dict.get("suggested_event_key", "") or ""),
        "review_updated_at_utc": str(row_dict.get("review_updated_at_utc", "") or ""),
    }


def validate_micro_pattern_label_update(row_update: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    keys_lower = {str(k).lower() for k in row_update.keys()}
    forbidden = sorted(keys_lower.intersection(FORBIDDEN_UPDATE_FIELDS))
    if forbidden:
        errors.append(f"forbidden_fields_present:{','.join(forbidden)}")
    if not str(row_update.get("sample_id", "")).strip():
        errors.append("sample_id_required")

    label = str(row_update.get("human_micro_pattern_label", "")).strip()
    if label and label not in LABEL_OPTIONS:
        errors.append("invalid_human_micro_pattern_label")

    conf = str(row_update.get("human_micro_pattern_confidence", "")).strip()
    if conf and conf not in CONFIDENCE_OPTIONS:
        errors.append("invalid_human_micro_pattern_confidence")

    should = str(row_update.get("human_should_create_rule", "")).strip()
    if should and should not in SHOULD_CREATE_RULE_OPTIONS:
        errors.append("invalid_human_should_create_rule")

    event_key = str(row_update.get("suggested_event_key", "")).strip()
    if event_key and not event_key.replace("_", "").isalnum():
        errors.append("invalid_suggested_event_key")
    return errors


def persist_micro_pattern_label(row_update: dict[str, Any], completed_csv: Path, audit_jsonl: Path) -> dict[str, Any]:
    errors = validate_micro_pattern_label_update(row_update)
    if errors:
        return {"status": "blocked", "errors": errors}

    now = _utc_now_iso()
    packet_identity = {
        "sample_id": str(row_update.get("sample_id", "")).strip(),
        "timestamp": str(row_update.get("timestamp", "") or ""),
        "symbol": str(row_update.get("symbol", "") or ""),
        "timeframe": str(row_update.get("timeframe", "") or ""),
        "micro_pattern_event_3": str(row_update.get("micro_pattern_event_3", "") or ""),
        "micro_noise_subtype": str(row_update.get("micro_noise_subtype", "") or ""),
        "micro_pattern_rule_version": str(row_update.get("micro_pattern_rule_version", "") or ""),
    }
    payload = {**packet_identity}
    payload.update(
        {
            "human_micro_pattern_label": str(row_update.get("human_micro_pattern_label", "") or "").strip(),
            "human_micro_pattern_confidence": str(row_update.get("human_micro_pattern_confidence", "") or "").strip(),
            "human_micro_pattern_rationale_zh": str(row_update.get("human_micro_pattern_rationale_zh", "") or "").strip(),
            "human_rule_suggestion_zh": str(row_update.get("human_rule_suggestion_zh", "") or "").strip(),
            "human_should_create_rule": str(row_update.get("human_should_create_rule", "") or "").strip(),
            "suggested_event_key": str(row_update.get("suggested_event_key", "") or "").strip(),
            "review_updated_at_utc": now,
        }
    )

    existing = load_completed_micro_pattern_labels(completed_csv)
    merged = pd.concat([existing, pd.DataFrame([payload])], ignore_index=True)
    latest = _latest_by_sample_id(_ensure_columns(merged, REQUIRED_LABEL_FIELDS))
    completed_csv.parent.mkdir(parents=True, exist_ok=True)
    latest.to_csv(completed_csv, index=False)

    audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
    event = {"event_type": "micro_pattern_label_saved", "event_time_utc": now, "payload": payload}
    with audit_jsonl.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {"status": "ok", "sample_id": payload["sample_id"], "review_updated_at_utc": now}
