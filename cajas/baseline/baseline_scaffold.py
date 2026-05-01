"""Training-disabled baseline scaffold report builder."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.baseline.baseline_plan import build_baseline_plan
from cajas.baseline.training_guard import (
    TrainingDisabledError,
    TrainingGuardResult,
    assert_baseline_training_allowed,
)


@dataclass(frozen=True)
class BaselineDatasetSpec:
    feature_count: int
    label_col: str
    segments: dict[str, dict[str, int]]
    leakage_columns_in_features: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BaselineTrainingScaffoldReport:
    config_name: str
    model_family: str
    task_type: str
    target_label: str
    dataset_spec: BaselineDatasetSpec
    dependency_probe: dict
    readiness: dict
    training_guard: dict
    label_encoding_plan: dict[str, int]
    training_enabled: bool
    training_allowed: bool
    training_executed: bool
    next_steps: list[str]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "model_family": self.model_family,
            "task_type": self.task_type,
            "target_label": self.target_label,
            "dataset_spec": self.dataset_spec.to_dict(),
            "dependency_probe": self.dependency_probe,
            "readiness": self.readiness,
            "training_guard": self.training_guard,
            "label_encoding_plan": self.label_encoding_plan,
            "training_enabled": self.training_enabled,
            "training_allowed": self.training_allowed,
            "training_executed": self.training_executed,
            "next_steps": self.next_steps,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


def build_training_disabled_baseline_scaffold(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    phase_policy_allows_training: bool = False,
) -> BaselineTrainingScaffoldReport:
    plan = build_baseline_plan(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        strict=False,
    )
    blockers = list(plan.blockers)
    warnings = list(plan.warnings)

    guard_result: TrainingGuardResult | None = None
    try:
        guard_result = assert_baseline_training_allowed(
            config_training_enabled=bool(plan.training_enabled),
            phase_policy_allows_training=phase_policy_allows_training,
        )
    except TrainingDisabledError as exc:
        msg = str(exc)
        phase_blocker = "Training remains disabled by Phase 10 policy."
        if phase_blocker not in blockers:
            blockers.append(phase_blocker)
        if "configuration" in msg:
            warnings.append("Config has training.enabled=false as expected in Phase 10.")

    # Phase 10 scaffold expects a single training-policy blocker.
    blockers = [b for b in blockers if "Phase 9 policy" not in b and "configuration" not in b]
    if "Training remains disabled by Phase 10 policy." not in blockers:
        blockers.append("Training remains disabled by Phase 10 policy.")

    dataset_spec = BaselineDatasetSpec(
        feature_count=int(plan.readiness_report["feature_count"]),
        label_col=str(plan.model_spec.target_label),
        segments=dict(plan.readiness_report["segments"]),
        leakage_columns_in_features=bool(
            plan.readiness_report["feature_audit"]["leakage_columns_found"]
        ),
    )

    next_steps = [
        "Resolve strict readiness warnings to reduce data-quality risk.",
        "Decide label encoding application strategy for a later phase.",
        "Define multiclass baseline metrics before any training phase.",
        "Keep explicit training enable flags disabled until approved in a later phase.",
    ]

    return BaselineTrainingScaffoldReport(
        config_name=plan.config_name,
        model_family=model_family,
        task_type=plan.model_spec.task_type,
        target_label=plan.model_spec.target_label,
        dataset_spec=dataset_spec,
        dependency_probe=plan.dependency_probe,
        readiness=plan.readiness_report,
        training_guard=(
            guard_result.to_dict()
            if guard_result
            else {
                "allowed": False,
                "reason": "Training blocked by guard.",
                "config_training_enabled": bool(plan.training_enabled),
                "phase_policy_allows_training": bool(phase_policy_allows_training),
            }
        ),
        label_encoding_plan={"down": 0, "flat": 1, "up": 2},
        training_enabled=False,
        training_allowed=False,
        training_executed=False,
        next_steps=next_steps,
        blockers=blockers,
        warnings=warnings,
    )
