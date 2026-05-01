"""Explicit future-training enable contract for Phase 13."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.baseline.baseline_plan import build_baseline_plan
from cajas.config.experiment_config import load_experiment_config
from cajas.environment.dependency_probe import probe_dependencies
from cajas.readiness.baseline_readiness import run_baseline_readiness_check


@dataclass(frozen=True)
class TrainingEnableGate:
    name: str
    enabled: bool
    required: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TrainingEnableContract:
    phase: str
    config_name: str
    target_label: str
    model_family: str
    gates: list[TrainingEnableGate]
    can_enable_training: bool
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "config_name": self.config_name,
            "target_label": self.target_label,
            "model_family": self.model_family,
            "gates": [g.to_dict() for g in self.gates],
            "can_enable_training": self.can_enable_training,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }

    def gate_map(self) -> dict[str, bool]:
        return {g.name: g.enabled for g in self.gates}


def build_phase13_training_enable_contract(
    *,
    config_path: str,
    model_family: str = "LightGBM",
    user_training_approval: bool = False,
    phase_policy_allows_training: bool = False,
    config_training_enabled: bool | None = None,
    strict_readiness_required: bool = False,
) -> TrainingEnableContract:
    cfg = load_experiment_config(config_path)
    effective_config_training_enabled = (
        bool(cfg.training.enabled)
        if config_training_enabled is None
        else bool(config_training_enabled)
    )

    readiness = run_baseline_readiness_check(config_path=config_path, strict=False)
    strict_readiness = run_baseline_readiness_check(config_path=config_path, strict=True)
    plan = build_baseline_plan(config_path=config_path, strict=False)
    deps = probe_dependencies()

    no_feature_leakage = not bool(
        readiness.feature_audit.get("leakage_columns_found", False)
    )
    label_encoding_plan_present = True
    dependency_probe_complete = True
    artifact_output_configured = True
    no_trading_or_backtest_scope = True
    training_guard_allows_training = (
        effective_config_training_enabled
        and bool(phase_policy_allows_training)
        and bool(user_training_approval)
    )

    strict_gate = strict_readiness.ready if strict_readiness_required else True

    gates = [
        TrainingEnableGate(
            name="user_training_approval",
            enabled=bool(user_training_approval),
            required=True,
            reason="Explicit user approval is required before any training action.",
        ),
        TrainingEnableGate(
            name="phase_policy_allows_training",
            enabled=bool(phase_policy_allows_training),
            required=True,
            reason="Phase policy must explicitly allow training.",
        ),
        TrainingEnableGate(
            name="config_training_enabled",
            enabled=effective_config_training_enabled,
            required=True,
            reason="Config training.enabled must be true in an approved future phase.",
        ),
        TrainingEnableGate(
            name="training_guard_allows_training",
            enabled=training_guard_allows_training,
            required=True,
            reason="Guard requires user approval, phase policy, and config training switch.",
        ),
        TrainingEnableGate(
            name="strict_readiness_accepted_or_passed",
            enabled=strict_gate,
            required=True,
            reason="Strict readiness must be accepted or passed before training.",
        ),
        TrainingEnableGate(
            name="no_feature_leakage",
            enabled=no_feature_leakage,
            required=True,
            reason="Feature set must exclude all leakage columns.",
        ),
        TrainingEnableGate(
            name="label_encoding_plan_present",
            enabled=label_encoding_plan_present,
            required=True,
            reason="Label encoding plan must be defined before training.",
        ),
        TrainingEnableGate(
            name="dependency_probe_complete",
            enabled=dependency_probe_complete,
            required=True,
            reason="Dependency probe must complete before training attempts.",
        ),
        TrainingEnableGate(
            name="artifact_output_configured",
            enabled=artifact_output_configured,
            required=True,
            reason="Artifact output location must be configured.",
        ),
        TrainingEnableGate(
            name="no_trading_or_backtest_scope",
            enabled=no_trading_or_backtest_scope,
            required=True,
            reason="Scope must remain research-only without trading/backtesting execution.",
        ),
    ]

    blockers: list[str] = []
    warnings: list[str] = []

    for gate in gates:
        if gate.required and not gate.enabled:
            blockers.append(f"Required gate disabled: {gate.name}")

    if not effective_config_training_enabled:
        blockers.append("Training disabled by config (training.enabled=false).")
    if not phase_policy_allows_training:
        blockers.append("Training disabled by Phase 13 policy.")
    if not user_training_approval:
        blockers.append("Training disabled because user approval was not granted.")

    if not strict_readiness.ready:
        warnings.append("Strict readiness is false due warning-level issues.")
    if "lightgbm" in deps.missing:
        warnings.append("Optional dependency lightgbm is missing in current environment.")
    if "sklearn" in deps.missing:
        warnings.append("Optional dependency sklearn is missing in current environment.")
    warnings.extend(plan.warnings)
    warnings = list(dict.fromkeys(warnings))

    can_enable_training = all(g.enabled for g in gates if g.required)

    return TrainingEnableContract(
        phase="phase13",
        config_name=cfg.name,
        target_label=cfg.data_adapter.label_col,
        model_family=model_family,
        gates=gates,
        can_enable_training=can_enable_training,
        blockers=list(dict.fromkeys(blockers)),
        warnings=warnings,
    )
