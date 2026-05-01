"""Training-disabled baseline runner skeleton for Phase 12."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.baseline.baseline_preflight import run_baseline_preflight
from cajas.baseline.run_contract import build_phase12_baseline_run_contract
from cajas.config.experiment_config import load_experiment_config


@dataclass(frozen=True)
class BaselineBlockedRunReport:
    config_name: str
    phase: str
    model_family: str
    target_label: str
    training_enabled: bool
    phase_policy_allows_training: bool
    can_train: bool
    training_executed: bool
    model_built: bool
    predictions_generated: bool
    evaluation_executed: bool
    serialized_model: bool
    run_contract: dict
    preflight_report: dict
    blockers: list[str]
    warnings: list[str]
    next_steps: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def run_training_disabled_baseline(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselineBlockedRunReport:
    cfg = load_experiment_config(config_path)
    preflight = run_baseline_preflight(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        phase_policy_allows_training=phase_policy_allows_training,
    )
    contract = build_phase12_baseline_run_contract(
        config_path=config_path,
        model_family=model_family,
        phase_policy_allows_training=phase_policy_allows_training,
    )

    blockers = list(preflight.blockers) + list(contract.blockers)
    blockers = list(dict.fromkeys(blockers))
    warnings = list(preflight.warnings) + list(contract.warnings)
    warnings = list(dict.fromkeys(warnings))

    next_steps = [
        "Keep training disabled until a future explicit approval phase.",
        "Resolve strict readiness warnings before enabling any training switch.",
        "Finalize baseline metrics and label encoding application strategy.",
        "Use artifact-only dry-runs for any further command scaffolding.",
    ]

    return BaselineBlockedRunReport(
        config_name=cfg.name,
        phase="phase12",
        model_family=model_family,
        target_label=cfg.data_adapter.label_col,
        training_enabled=bool(cfg.training.enabled),
        phase_policy_allows_training=phase_policy_allows_training,
        can_train=False,
        training_executed=False,
        model_built=False,
        predictions_generated=False,
        evaluation_executed=False,
        serialized_model=False,
        run_contract=contract.to_dict(),
        preflight_report=preflight.to_dict(),
        blockers=blockers,
        warnings=warnings,
        next_steps=next_steps,
    )
