"""Candidate promotion manifest for future manual Qlib-trial review."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def build_candidate_promotion_manifest(
    *,
    decision_packet_path: str | Path,
    out_dir: str | Path,
    label_variant_id: str,
    feature_set_id: str,
    target_name: str,
    horizon: int,
    model_family: str,
) -> dict:
    packet_path = Path(decision_packet_path).expanduser().resolve()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    decision = packet.get("final_decision", "reject")
    status = "candidate_for_manual_review" if decision == "candidate_for_qlib_trial" else "blocked"
    run_id = packet.get("run_id", "unknown")
    manifest = {
        "promotion_id": f"promotion_{run_id}",
        "created_at_utc": _utc_now_iso(),
        "decision_packet_path": str(packet_path),
        "label_variant_id": label_variant_id,
        "feature_set_id": feature_set_id,
        "target_name": target_name,
        "horizon": int(horizon),
        "model_family": model_family,
        "train_period": packet.get("train_period", "unknown"),
        "holdout_period": packet.get("holdout_period", "unknown"),
        "known_limitations": [f.message for f in packet.get("non_blocking_findings", [])],
        "required_rechecks": ["re-run leakage/drift audit", "re-run seed stability on latest dataset snapshot"],
        "status": status,
    }
    return manifest

