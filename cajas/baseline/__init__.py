"""Training-disabled baseline planning helpers."""

from .baseline_plan import BaselineModelSpec, BaselinePlanReport, build_baseline_plan
from .baseline_preflight import BaselinePreflightReport, run_baseline_preflight
from .baseline_runner import BaselineBlockedRunReport, run_training_disabled_baseline
from .baseline_artifacts import write_baseline_reports
from .execution_contract import BaselineExecutionContract, ExecutionPermission, build_phase11_execution_contract
from .run_contract import BaselineRunContract, BaselineRunStep, build_phase12_baseline_run_contract
from .future_training_skeleton import (
    FutureTrainingSkeletonReport,
    FutureTrainingSkeletonStep,
    build_future_training_skeleton,
)
from .training_enable_contract import (
    TrainingEnableContract,
    TrainingEnableGate,
    build_phase13_training_enable_contract,
)
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
from .classification_metrics import (
    compute_classification_metrics,
    confusion_matrix_to_rows,
)
from .local_baseline_trainer import (
    LocalBaselineTrainingConfig,
    LocalBaselineTrainingReport,
    train_local_baseline,
)
from .baseline_artifact_inspector import (
    BaselineArtifactIssue,
    BaselineArtifactInspectionReport,
    inspect_baseline_run_artifacts,
)
from .prediction_review import PredictionReviewReport, build_prediction_review
from .baseline_run_comparison import BaselineRunComparisonReport, compare_baseline_runs
from .feature_importance_inspector import FeatureImportanceInspectionReport, inspect_feature_importance
from .feature_importance_summary import (
    AggregatedFeatureImportanceItem,
    FeatureImportanceSummaryReport,
    summarize_feature_importance_across_runs,
)
from .multi_model_baseline import MultiModelBaselineReport, run_multi_model_baseline

__all__ = [
    "BaselineModelSpec",
    "BaselinePlanReport",
    "BaselineDatasetSpec",
    "ExecutionPermission",
    "BaselineExecutionContract",
    "BaselinePreflightReport",
    "BaselineRunContract",
    "BaselineRunStep",
    "BaselineBlockedRunReport",
    "TrainingEnableContract",
    "TrainingEnableGate",
    "FutureTrainingSkeletonReport",
    "FutureTrainingSkeletonStep",
    "BaselineTrainingScaffoldReport",
    "TrainingDisabledError",
    "TrainingGuardResult",
    "LocalBaselineTrainingConfig",
    "LocalBaselineTrainingReport",
    "BaselineArtifactIssue",
    "BaselineArtifactInspectionReport",
    "PredictionReviewReport",
    "BaselineRunComparisonReport",
    "FeatureImportanceInspectionReport",
    "AggregatedFeatureImportanceItem",
    "FeatureImportanceSummaryReport",
    "MultiModelBaselineReport",
    "assert_baseline_training_allowed",
    "build_baseline_plan",
    "build_phase11_execution_contract",
    "build_phase12_baseline_run_contract",
    "build_phase13_training_enable_contract",
    "build_future_training_skeleton",
    "run_baseline_preflight",
    "run_training_disabled_baseline",
    "build_training_disabled_baseline_scaffold",
    "write_baseline_reports",
    "compute_classification_metrics",
    "confusion_matrix_to_rows",
    "train_local_baseline",
    "inspect_baseline_run_artifacts",
    "build_prediction_review",
    "compare_baseline_runs",
    "inspect_feature_importance",
    "summarize_feature_importance_across_runs",
    "run_multi_model_baseline",
]
