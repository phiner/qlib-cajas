"""Baseline execution contract for Phase 11 preflight gating."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.config.experiment_config import load_experiment_config


@dataclass(frozen=True)
class ExecutionPermission:
    name: str
    allowed: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BaselineExecutionContract:
    phase: str
    config_name: str
    model_family: str
    target_label: str
    permissions: list[ExecutionPermission]
    required_before_training: list[str]
    forbidden_actions: list[str]

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "config_name": self.config_name,
            "model_family": self.model_family,
            "target_label": self.target_label,
            "permissions": [p.to_dict() for p in self.permissions],
            "required_before_training": self.required_before_training,
            "forbidden_actions": self.forbidden_actions,
        }

    def permission_map(self) -> dict[str, bool]:
        return {p.name: p.allowed for p in self.permissions}


def build_phase11_execution_contract(
    *,
    config_path: str,
    model_family: str = "LightGBM",
) -> BaselineExecutionContract:
    cfg = load_experiment_config(config_path)
    label = cfg.data_adapter.label_col

    allowed = [
        "load_config",
        "validate_dataset",
        "run_readiness_check",
        "build_plan",
        "build_scaffold",
        "probe_dependencies",
        "write_local_artifacts",
    ]
    forbidden = [
        "build_model",
        "fit_model",
        "predict",
        "evaluate_model",
        "serialize_model",
        "backtest",
        "trade",
        "submit_orders",
    ]
    permissions = [ExecutionPermission(name=a, allowed=True, reason="Allowed in preflight/planning phases.") for a in allowed]
    permissions += [ExecutionPermission(name=f, allowed=False, reason="Forbidden in Phase 11 training-disabled policy.") for f in forbidden]

    required = [
        "explicit future phase approval",
        "training.enabled: true in config",
        "phase policy allows training",
        "strict readiness warnings reviewed or accepted",
        "label encoding finalized",
        "baseline metrics finalized",
        "artifact output location confirmed",
        "no Qlib core modifications required",
    ]
    forbidden_actions = [
        "live trading",
        "order submission",
        "position sizing",
        "profit claims",
        "backtest optimization",
    ]
    return BaselineExecutionContract(
        phase="phase11",
        config_name=cfg.name,
        model_family=model_family,
        target_label=label,
        permissions=permissions,
        required_before_training=required,
        forbidden_actions=forbidden_actions,
    )
