"""Builder for Qlib adapter contracts from promotion manifest inputs."""

from __future__ import annotations

import json
from pathlib import Path

from .qlib_adapter_contract import QlibAdapterContract, ContractIssue, utc_now_iso, validate_qlib_adapter_contract


def build_qlib_adapter_contract(
    *,
    promotion_manifest_path: str | Path,
    candidate_id: str,
    dataset_version: str,
    feature_set_id: str,
    label_variant_id: str,
    target_name: str,
    frequency: str,
    prediction_horizon: int,
    instrument_universe: list[str] | None = None,
    required_feature_columns: list[str] | None = None,
    required_label_columns: list[str] | None = None,
    artifact_paths: dict[str, str] | None = None,
    strict_paths: bool = False,
) -> tuple[dict, list[ContractIssue]]:
    manifest_path = Path(promotion_manifest_path).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contract = QlibAdapterContract(
        contract_version="v1",
        candidate_id=candidate_id,
        research_run_id=manifest.get("promotion_id", "unknown_promotion"),
        dataset_version=dataset_version,
        feature_set_id=feature_set_id,
        label_variant_id=label_variant_id,
        target_name=target_name,
        prediction_horizon=prediction_horizon,
        instrument_universe=instrument_universe or ["EURUSD"],
        frequency=frequency,
        required_feature_columns=required_feature_columns or ["open", "high", "low", "close", "volume"],
        required_label_columns=required_label_columns or [target_name],
        artifact_paths=artifact_paths
        or {
            "decision_packet_path": manifest.get("decision_packet_path", ""),
            "promotion_manifest_path": str(manifest_path),
        },
        known_limitations=list(manifest.get("known_limitations", [])),
        promotion_status=manifest.get("status", "draft"),
        created_at_utc=utc_now_iso(),
    ).to_dict()
    issues = validate_qlib_adapter_contract(contract, strict_paths=strict_paths)
    return contract, issues
