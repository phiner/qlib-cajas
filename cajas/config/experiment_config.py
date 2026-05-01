"""Training-disabled experiment config loader for research dry-runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cajas.workflows.prepared_workflow import PreparedWorkflowConfig


@dataclass(frozen=True)
class SegmentConfig:
    start: str
    end: str


@dataclass(frozen=True)
class DataAdapterConfig:
    csv_path: str
    label_col: str
    leakage_columns: tuple[str, ...]
    segments: dict[str, SegmentConfig]
    handler_class: str | None = None
    dataset_class: str | None = None


@dataclass(frozen=True)
class WorkflowBridgeConfig:
    workflow_class: str
    dry_run_only: bool


@dataclass(frozen=True)
class TrainingConfig:
    enabled: bool


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    data_adapter: DataAdapterConfig
    workflow_bridge: WorkflowBridgeConfig
    training: TrainingConfig


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    root = _require_mapping(raw, "root")

    name = str(root.get("name", "")).strip()
    if not name:
        raise ValueError("name is required")

    data_raw = _require_mapping(root.get("data_adapter"), "data_adapter")
    csv_path = str(data_raw.get("csv_path", "")).strip()
    label_col = str(data_raw.get("label_col", "")).strip()
    if not csv_path:
        raise ValueError("data_adapter.csv_path is required")
    if not label_col:
        raise ValueError("data_adapter.label_col is required")

    leakage = data_raw.get("leakage_columns")
    if not isinstance(leakage, list):
        raise ValueError("data_adapter.leakage_columns must be a list")
    leakage_columns = tuple(str(x) for x in leakage if str(x).strip())

    seg_raw = _require_mapping(data_raw.get("segments"), "data_adapter.segments")
    segments: dict[str, SegmentConfig] = {}
    for key in ("train", "valid", "test"):
        item = _require_mapping(seg_raw.get(key), f"data_adapter.segments.{key}")
        start = str(item.get("start", "")).strip()
        end = str(item.get("end", "")).strip()
        if not start or not end:
            raise ValueError(f"data_adapter.segments.{key} requires start/end")
        segments[key] = SegmentConfig(start=start, end=end)

    workflow_raw = _require_mapping(root.get("workflow_bridge"), "workflow_bridge")
    workflow_class = str(workflow_raw.get("class", "")).strip()
    if not workflow_class:
        raise ValueError("workflow_bridge.class is required")

    training_raw = _require_mapping(root.get("training"), "training")
    enabled = training_raw.get("enabled")
    if not isinstance(enabled, bool):
        raise ValueError("training.enabled must be boolean")

    return ExperimentConfig(
        name=name,
        data_adapter=DataAdapterConfig(
            csv_path=csv_path,
            label_col=label_col,
            leakage_columns=leakage_columns,
            segments=segments,
            handler_class=data_raw.get("handler_class"),
            dataset_class=data_raw.get("dataset_class"),
        ),
        workflow_bridge=WorkflowBridgeConfig(
            workflow_class=workflow_class,
            dry_run_only=bool(workflow_raw.get("dry_run_only", False)),
        ),
        training=TrainingConfig(enabled=enabled),
    )


def validate_experiment_config(config: ExperimentConfig) -> list[str]:
    issues: list[str] = []
    if not config.data_adapter.leakage_columns:
        issues.append("leakage_columns is empty")
    if not config.workflow_bridge.dry_run_only:
        issues.append("workflow_bridge.dry_run_only should be true")
    if config.training.enabled:
        issues.append("training.enabled should be false")
    if config.data_adapter.handler_class and (
        config.data_adapter.handler_class
        != "cajas.handlers.prepared_csv_handler.PreparedCsvHandler"
    ):
        issues.append("handler_class does not match current PreparedCsvHandler path")
    if config.data_adapter.dataset_class and (
        config.data_adapter.dataset_class
        != "cajas.datasets.prepared_dataset.PreparedDataset"
    ):
        issues.append("dataset_class does not match current PreparedDataset path")
    if (
        config.workflow_bridge.workflow_class
        != "cajas.workflows.prepared_workflow.PreparedWorkflow"
    ):
        issues.append("workflow_bridge.class does not match current PreparedWorkflow path")
    return issues


def assert_training_disabled(config: ExperimentConfig) -> None:
    if config.training.enabled:
        raise ValueError("training.enabled must be false for dry-run phases")


def build_workflow_config(
    config: ExperimentConfig,
    csv_path_override: str | None = None,
) -> PreparedWorkflowConfig:
    segments = {
        name: (seg.start, seg.end) for name, seg in config.data_adapter.segments.items()
    }
    return PreparedWorkflowConfig(
        csv_path=csv_path_override or config.data_adapter.csv_path,
        label_col=config.data_adapter.label_col,
        segments=segments,
    )
