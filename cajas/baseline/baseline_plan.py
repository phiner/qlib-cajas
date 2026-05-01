"""Build a training-disabled baseline plan report."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.environment.dependency_probe import probe_dependencies
from cajas.readiness.baseline_readiness import run_baseline_readiness_check


@dataclass(frozen=True)
class BaselineModelSpec:
    model_family: str
    target_label: str
    task_type: str
    enabled: bool
    training_allowed: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BaselinePlanReport:
    config_name: str
    ready_non_strict: bool
    ready_strict: bool
    training_enabled: bool
    training_allowed: bool
    training_executed: bool
    model_spec: BaselineModelSpec
    dependency_probe: dict
    readiness_report: dict
    required_next_steps: list[str]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "ready_non_strict": self.ready_non_strict,
            "ready_strict": self.ready_strict,
            "training_enabled": self.training_enabled,
            "training_allowed": self.training_allowed,
            "training_executed": self.training_executed,
            "model_spec": self.model_spec.to_dict(),
            "dependency_probe": self.dependency_probe,
            "readiness_report": self.readiness_report,
            "required_next_steps": self.required_next_steps,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def build_baseline_plan(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    strict: bool = False,
) -> BaselinePlanReport:
    non_strict = run_baseline_readiness_check(
        config_path=config_path,
        input_override=input_override,
        strict=False,
    )
    strict_report = run_baseline_readiness_check(
        config_path=config_path,
        input_override=input_override,
        strict=True,
    )
    deps = probe_dependencies()

    model_spec = BaselineModelSpec(
        model_family=model_family,
        target_label=non_strict.label_col,
        task_type="multiclass_classification",
        enabled=False,
        training_allowed=False,
    )

    blockers: list[str] = []
    warnings: list[str] = []
    if not strict_report.ready:
        warnings.append("Strict readiness is false due warning-level issues.")
    if non_strict.training_enabled:
        blockers.append("Training is enabled in config but must remain disabled.")
    blockers.append("Training remains disabled by Phase 9 policy.")
    for dep in ("sklearn", "lightgbm"):
        if dep in deps.missing:
            warnings.append(f"Missing optional future baseline dependency: {dep}")

    required_steps = [
        "Resolve strict readiness warnings where practical.",
        "Confirm optional baseline dependencies availability.",
        "Keep training disabled until explicitly approved in a later phase.",
    ]

    if strict and warnings:
        blockers.append("Strict mode requested with outstanding warnings.")

    return BaselinePlanReport(
        config_name=non_strict.config_name,
        ready_non_strict=non_strict.ready,
        ready_strict=strict_report.ready,
        training_enabled=non_strict.training_enabled,
        training_allowed=False,
        training_executed=False,
        model_spec=model_spec,
        dependency_probe=deps.to_dict(),
        readiness_report=non_strict.to_dict(),
        required_next_steps=required_steps,
        blockers=blockers,
        warnings=warnings,
    )
