"""Training-disabled baseline planning helpers."""

from .baseline_plan import BaselineModelSpec, BaselinePlanReport, build_baseline_plan
from .baseline_preflight import BaselinePreflightReport, run_baseline_preflight
from .execution_contract import BaselineExecutionContract, ExecutionPermission, build_phase11_execution_contract
from .baseline_scaffold import (
    BaselineDatasetSpec,
    BaselineTrainingScaffoldReport,
    build_training_disabled_baseline_scaffold,
)
from .training_guard import (
    TrainingDisabledError,
    TrainingGuardResult,
    assert_baseline_training_allowed,
)

__all__ = [
    "BaselineModelSpec",
    "BaselinePlanReport",
    "BaselineDatasetSpec",
    "ExecutionPermission",
    "BaselineExecutionContract",
    "BaselinePreflightReport",
    "BaselineTrainingScaffoldReport",
    "TrainingDisabledError",
    "TrainingGuardResult",
    "assert_baseline_training_allowed",
    "build_baseline_plan",
    "build_phase11_execution_contract",
    "run_baseline_preflight",
    "build_training_disabled_baseline_scaffold",
]
