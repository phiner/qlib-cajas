"""Classification metric plan for future multiclass baseline training."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MetricSpec:
    name: str
    enabled: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BaselineMetricPlan:
    task_type: str
    target_label: str
    metrics: list[MetricSpec]
    primary_metric: str
    notes: list[str]

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "target_label": self.target_label,
            "metrics": [m.to_dict() for m in self.metrics],
            "primary_metric": self.primary_metric,
            "notes": list(self.notes),
        }


def build_multiclass_metric_plan(
    target_label: str = "future_direction_8",
) -> BaselineMetricPlan:
    metrics = [
        MetricSpec("accuracy", True, "Core multiclass classification metric."),
        MetricSpec("macro_f1", True, "Primary metric robust to class imbalance."),
        MetricSpec("weighted_f1", True, "Tracks overall F1 weighted by support."),
        MetricSpec("per_class_precision", True, "Class-level precision diagnostics."),
        MetricSpec("per_class_recall", True, "Class-level recall diagnostics."),
        MetricSpec("confusion_matrix", True, "Error pattern inspection by class pair."),
        MetricSpec("class_distribution", True, "Label balance tracking across splits."),
    ]
    return BaselineMetricPlan(
        task_type="multiclass_classification",
        target_label=target_label,
        metrics=metrics,
        primary_metric="macro_f1",
        notes=[
            "Plan only: metrics are not computed in Phase 14 because no predictions exist.",
            "Trading metrics such as profit/return/sharpe/drawdown are out of scope.",
        ],
    )
