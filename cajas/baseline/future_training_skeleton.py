"""Future baseline training skeleton with explicit Phase 13 blocking gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.baseline.baseline_runner import run_training_disabled_baseline
from cajas.baseline.baseline_preflight import run_baseline_preflight
from cajas.baseline.training_enable_contract import (
    build_phase13_training_enable_contract,
)
from cajas.config.experiment_config import load_experiment_config


@dataclass(frozen=True)
class FutureTrainingSkeletonStep:
    name: str
    planned: bool
    allowed_now: bool
    executed: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FutureTrainingSkeletonReport:
    config_name: str
    phase: str
    model_family: str
    target_label: str
    can_enable_training: bool
    can_train_now: bool
    training_executed: bool
    model_built: bool
    fit_executed: bool
    prediction_executed: bool
    evaluation_executed: bool
    serialization_executed: bool
    enable_contract: dict
    steps: list[dict]
    blockers: list[str]
    warnings: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def build_future_training_skeleton(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    user_training_approval: bool = False,
    phase_policy_allows_training: bool = False,
) -> FutureTrainingSkeletonReport:
    cfg = load_experiment_config(config_path)
    enable_contract = build_phase13_training_enable_contract(
        config_path=config_path,
        model_family=model_family,
        user_training_approval=user_training_approval,
        phase_policy_allows_training=phase_policy_allows_training,
        config_training_enabled=bool(cfg.training.enabled),
        strict_readiness_required=False,
    )
    disabled = run_training_disabled_baseline(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        phase_policy_allows_training=phase_policy_allows_training,
    )
    preflight = run_baseline_preflight(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        phase_policy_allows_training=phase_policy_allows_training,
    )

    allowed_now = {
        "load_config",
        "run_preflight",
        "build_dataset",
        "apply_label_encoding",
        "write_training_report",
    }
    step_names = [
        "load_config",
        "run_preflight",
        "build_dataset",
        "apply_label_encoding",
        "construct_model",
        "fit_model",
        "predict_valid",
        "evaluate_valid",
        "write_model_artifact",
        "write_training_report",
    ]
    steps: list[FutureTrainingSkeletonStep] = []
    for step in step_names:
        allowed = step in allowed_now
        reason = (
            "Allowed metadata-only step in Phase 13 skeleton."
            if allowed
            else "Forbidden in Phase 13 before explicit training approval."
        )
        steps.append(
            FutureTrainingSkeletonStep(
                name=step,
                planned=True,
                allowed_now=allowed,
                executed=False,
                reason=reason,
            )
        )

    blockers = list(enable_contract.blockers)
    blockers.extend(preflight.blockers)
    blockers.extend(disabled.blockers)
    blockers = list(dict.fromkeys(blockers))

    warnings = list(enable_contract.warnings)
    warnings.extend(preflight.warnings)
    warnings.extend(disabled.warnings)
    warnings = list(dict.fromkeys(warnings))

    next_steps = [
        "Keep all training gates disabled until explicit user approval in a future phase.",
        "Resolve strict readiness warnings before requesting any training enablement.",
        "Review Phase 14 label encoding preview and metric plan artifacts before training approval.",
        "Materialize training input previews under tmp/ for segment-level inspection when needed.",
        "Keep all outputs artifact-only and preserve no-trading scope.",
    ]

    can_enable = bool(enable_contract.can_enable_training)
    can_train_now = bool(can_enable and phase_policy_allows_training and cfg.training.enabled)

    return FutureTrainingSkeletonReport(
        config_name=cfg.name,
        phase="phase13",
        model_family=model_family,
        target_label=cfg.data_adapter.label_col,
        can_enable_training=can_enable,
        can_train_now=can_train_now,
        training_executed=False,
        model_built=False,
        fit_executed=False,
        prediction_executed=False,
        evaluation_executed=False,
        serialization_executed=False,
        enable_contract=enable_contract.to_dict(),
        steps=[s.to_dict() for s in steps],
        blockers=blockers,
        warnings=warnings,
        next_steps=next_steps,
    )
