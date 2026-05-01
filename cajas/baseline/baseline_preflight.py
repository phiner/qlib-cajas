"""Consolidated baseline preflight report for Phase 11."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cajas.baseline.baseline_plan import build_baseline_plan
from cajas.baseline.baseline_scaffold import build_training_disabled_baseline_scaffold
from cajas.baseline.execution_contract import build_phase11_execution_contract
from cajas.config.experiment_config import load_experiment_config
from cajas.quality.path_hygiene import check_path_hygiene
from cajas.readiness.baseline_readiness import run_baseline_readiness_check


@dataclass(frozen=True)
class BaselinePreflightReport:
    config_name: str
    phase: str
    can_train_now: bool
    training_enabled: bool
    phase_policy_allows_training: bool
    training_executed: bool
    readiness_ready: bool
    strict_readiness_ready: bool
    path_hygiene_passed: bool
    execution_contract: dict
    baseline_plan: dict
    baseline_scaffold: dict
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "phase": self.phase,
            "can_train_now": self.can_train_now,
            "training_enabled": self.training_enabled,
            "phase_policy_allows_training": self.phase_policy_allows_training,
            "training_executed": self.training_executed,
            "readiness_ready": self.readiness_ready,
            "strict_readiness_ready": self.strict_readiness_ready,
            "path_hygiene_passed": self.path_hygiene_passed,
            "execution_contract": self.execution_contract,
            "baseline_plan": self.baseline_plan,
            "baseline_scaffold": self.baseline_scaffold,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def run_baseline_preflight(
    *,
    config_path: str,
    root: str | Path = ".",
    input_override: str | None = None,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselinePreflightReport:
    cfg = load_experiment_config(config_path)
    readiness = run_baseline_readiness_check(
        config_path=config_path, input_override=input_override, strict=False
    )
    strict_readiness = run_baseline_readiness_check(
        config_path=config_path, input_override=input_override, strict=True
    )
    plan = build_baseline_plan(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        strict=False,
    )
    scaffold = build_training_disabled_baseline_scaffold(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        phase_policy_allows_training=phase_policy_allows_training,
    )
    contract = build_phase11_execution_contract(
        config_path=config_path, model_family=model_family
    )
    hygiene = check_path_hygiene(root=root)

    blockers = list(scaffold.blockers)
    warnings = list(scaffold.warnings)
    if not hygiene.passed:
        blockers.append("Path hygiene check failed.")
    if not strict_readiness.ready:
        warnings.append("Strict readiness is false due warning-level issues.")
    warnings = list(dict.fromkeys(warnings))

    can_train_now = False
    training_enabled = bool(cfg.training.enabled)

    return BaselinePreflightReport(
        config_name=cfg.name,
        phase="phase11",
        can_train_now=can_train_now,
        training_enabled=training_enabled,
        phase_policy_allows_training=phase_policy_allows_training,
        training_executed=False,
        readiness_ready=readiness.ready,
        strict_readiness_ready=strict_readiness.ready,
        path_hygiene_passed=hygiene.passed,
        execution_contract=contract.to_dict(),
        baseline_plan=plan.to_dict(),
        baseline_scaffold=scaffold.to_dict(),
        blockers=blockers,
        warnings=warnings,
    )
