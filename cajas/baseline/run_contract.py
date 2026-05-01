"""Phase 12 baseline run contract for a training-disabled command skeleton."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.config.experiment_config import load_experiment_config


@dataclass(frozen=True)
class BaselineRunStep:
    name: str
    allowed: bool
    executed: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BaselineRunContract:
    config_name: str
    phase: str
    model_family: str
    target_label: str
    training_enabled: bool
    phase_policy_allows_training: bool
    can_train: bool
    steps: list[BaselineRunStep]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "phase": self.phase,
            "model_family": self.model_family,
            "target_label": self.target_label,
            "training_enabled": self.training_enabled,
            "phase_policy_allows_training": self.phase_policy_allows_training,
            "can_train": self.can_train,
            "steps": [s.to_dict() for s in self.steps],
            "blockers": self.blockers,
            "warnings": self.warnings,
        }

    def step_map(self) -> dict[str, bool]:
        return {s.name: s.allowed for s in self.steps}


def build_phase12_baseline_run_contract(
    *,
    config_path: str,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselineRunContract:
    cfg = load_experiment_config(config_path)
    training_enabled = bool(cfg.training.enabled)
    can_train = training_enabled and phase_policy_allows_training

    allowed_steps = {
        "load_config",
        "validate_config",
        "run_preflight",
        "build_dataset",
        "encode_labels",
        "write_artifacts",
    }
    all_steps = [
        "load_config",
        "validate_config",
        "run_preflight",
        "build_dataset",
        "encode_labels",
        "build_model",
        "fit_model",
        "predict",
        "evaluate",
        "serialize_model",
        "write_artifacts",
    ]
    steps: list[BaselineRunStep] = []
    for name in all_steps:
        allowed = name in allowed_steps
        reason = (
            "Allowed in Phase 12 metadata-only baseline command."
            if allowed
            else "Forbidden in Phase 12 training-disabled policy."
        )
        steps.append(BaselineRunStep(name=name, allowed=allowed, executed=False, reason=reason))

    blockers = []
    if not training_enabled:
        blockers.append("Training disabled by config (training.enabled=false).")
    if not phase_policy_allows_training:
        blockers.append("Training disabled by Phase 12 policy.")
    warnings = [
        "Baseline runner is a skeleton and stops before model construction.",
        "Label encoding plan is metadata-only and not applied in Phase 12.",
    ]

    return BaselineRunContract(
        config_name=cfg.name,
        phase="phase12",
        model_family=model_family,
        target_label=cfg.data_adapter.label_col,
        training_enabled=training_enabled,
        phase_policy_allows_training=phase_policy_allows_training,
        can_train=can_train,
        steps=steps,
        blockers=blockers,
        warnings=warnings,
    )
