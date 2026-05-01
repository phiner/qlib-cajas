"""Qlib-style workflow config probe without qlib initialization or training."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.config.experiment_config import build_workflow_config, load_experiment_config
from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.qlib_compat.qlib_probe import probe_qlib_dataset_api


@dataclass(frozen=True)
class QlibWorkflowConfigIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QlibWorkflowConfigProbeReport:
    config_name: str
    qlib_available: bool
    workflow_config_built: bool
    training_enabled: bool
    training_executed: bool
    qlib_initialized: bool
    qlib_workflow_executed: bool
    workflow_config: dict
    issues: list[QlibWorkflowConfigIssue]
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "qlib_available": self.qlib_available,
            "workflow_config_built": self.workflow_config_built,
            "training_enabled": self.training_enabled,
            "training_executed": self.training_executed,
            "qlib_initialized": self.qlib_initialized,
            "qlib_workflow_executed": self.qlib_workflow_executed,
            "workflow_config": self.workflow_config,
            "issues": [i.to_dict() for i in self.issues],
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


def validate_qlib_workflow_config_dict(workflow_config: dict) -> list[QlibWorkflowConfigIssue]:
    issues: list[QlibWorkflowConfigIssue] = []

    experiment = workflow_config.get("experiment", {})
    dataset = workflow_config.get("dataset", {})
    model = workflow_config.get("model", {})
    workflow = workflow_config.get("workflow", {})

    if bool(experiment.get("training_enabled", True)):
        issues.append(QlibWorkflowConfigIssue("error", "training_enabled_true", "experiment.training_enabled must be false"))
    if bool(experiment.get("training_executed", True)):
        issues.append(QlibWorkflowConfigIssue("error", "training_executed_true", "experiment.training_executed must be false"))

    if bool(model.get("enabled", True)):
        issues.append(QlibWorkflowConfigIssue("error", "model_enabled_true", "model.enabled must be false"))
    if bool(model.get("constructed", True)):
        issues.append(QlibWorkflowConfigIssue("error", "model_constructed_true", "model.constructed must be false"))

    if bool(workflow.get("execute_workflow", True)):
        issues.append(QlibWorkflowConfigIssue("error", "workflow_execute_true", "workflow.execute_workflow must be false"))
    if bool(workflow.get("qlib_initialized", True)):
        issues.append(QlibWorkflowConfigIssue("error", "qlib_initialized_true", "workflow.qlib_initialized must be false"))

    label_col = str(dataset.get("label_col", "")).strip()
    if not label_col:
        issues.append(QlibWorkflowConfigIssue("error", "label_missing", "dataset.label_col is required"))

    segments = dataset.get("segments")
    if not isinstance(segments, dict) or not segments:
        issues.append(QlibWorkflowConfigIssue("error", "segments_missing", "dataset.segments is required"))

    leakage_cols = dataset.get("leakage_columns")
    if not isinstance(leakage_cols, list) or not leakage_cols:
        issues.append(QlibWorkflowConfigIssue("error", "leakage_missing", "dataset.leakage_columns must be declared"))

    feature_count = int(dataset.get("feature_count", 0) or 0)
    if feature_count <= 0:
        issues.append(QlibWorkflowConfigIssue("error", "feature_count_invalid", "dataset.feature_count must be > 0"))

    return issues


def build_training_disabled_qlib_workflow_config(*, config_path: str, input_override: str | None = None) -> dict:
    cfg = load_experiment_config(config_path)
    wf_cfg = build_workflow_config(cfg, csv_path_override=input_override)
    ds = PreparedDataset(csv_path=wf_cfg.csv_path, label_col=wf_cfg.label_col, segments=wf_cfg.segments)

    return {
        "experiment": {
            "name": cfg.name,
            "phase": "phase17",
            "training_enabled": False,
            "training_executed": False,
        },
        "dataset": {
            "class": "cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter",
            "label_col": wf_cfg.label_col,
            "segments": wf_cfg.segments,
            "feature_count": len(ds.feature_columns),
            "leakage_columns": ["future_close_8", "future_return_8"],
        },
        "model": {
            "family": "LightGBM",
            "enabled": False,
            "constructed": False,
        },
        "workflow": {
            "qlib_init_required": False,
            "qlib_initialized": False,
            "execute_workflow": False,
        },
    }


def probe_qlib_workflow_config(*, config_path: str, input_override: str | None = None) -> QlibWorkflowConfigProbeReport:
    qlib_api = probe_qlib_dataset_api()
    workflow_config = build_training_disabled_qlib_workflow_config(
        config_path=config_path,
        input_override=input_override,
    )
    issues = validate_qlib_workflow_config_dict(workflow_config)
    blockers = [i.message for i in issues if i.severity == "error"]
    warnings = [i.message for i in issues if i.severity != "error"]
    if not qlib_api.qlib_available:
        warnings.append("Qlib import is unavailable; probe result is config-only.")

    return QlibWorkflowConfigProbeReport(
        config_name=workflow_config["experiment"]["name"],
        qlib_available=qlib_api.qlib_available,
        workflow_config_built=True,
        training_enabled=False,
        training_executed=False,
        qlib_initialized=False,
        qlib_workflow_executed=False,
        workflow_config=workflow_config,
        issues=issues,
        warnings=list(dict.fromkeys(warnings)),
        blockers=blockers,
    )
