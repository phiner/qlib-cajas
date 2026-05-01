"""Qlib workflow config dry-run loader without initialization or execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.config.experiment_config import load_experiment_config
from cajas.qlib_compat.class_resolver import resolve_dotted_paths
from cajas.qlib_compat.qlib_probe import probe_qlib_dataset_api
from cajas.qlib_compat.workflow_config_probe import build_training_disabled_qlib_workflow_config


@dataclass(frozen=True)
class WorkflowDryRunIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowDryRunLoaderReport:
    config_name: str
    workflow_config_built: bool
    workflow_config: dict
    class_resolution: dict
    qlib_available: bool
    qlib_initialized: bool
    qlib_workflow_executed: bool
    training_enabled: bool
    training_executed: bool
    model_enabled: bool
    model_constructed: bool
    dataset_adapter_resolved: bool
    workflow_bridge_resolved: bool
    issues: list[WorkflowDryRunIssue]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "workflow_config_built": self.workflow_config_built,
            "workflow_config": self.workflow_config,
            "class_resolution": self.class_resolution,
            "qlib_available": self.qlib_available,
            "qlib_initialized": self.qlib_initialized,
            "qlib_workflow_executed": self.qlib_workflow_executed,
            "training_enabled": self.training_enabled,
            "training_executed": self.training_executed,
            "model_enabled": self.model_enabled,
            "model_constructed": self.model_constructed,
            "dataset_adapter_resolved": self.dataset_adapter_resolved,
            "workflow_bridge_resolved": self.workflow_bridge_resolved,
            "issues": [item.to_dict() for item in self.issues],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


def _build_class_paths(config_path: str) -> list[str]:
    cfg = load_experiment_config(config_path)
    class_paths = [
        "cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter",
        cfg.workflow_bridge.workflow_class,
    ]
    if cfg.data_adapter.handler_class:
        class_paths.append(str(cfg.data_adapter.handler_class))
    if cfg.data_adapter.dataset_class:
        class_paths.append(str(cfg.data_adapter.dataset_class))
    class_paths.append("cajas.workflows.prepared_workflow.PreparedWorkflowConfig")

    deduped: list[str] = []
    seen: set[str] = set()
    for path in class_paths:
        key = str(path).strip()
        if key and key not in seen:
            deduped.append(key)
            seen.add(key)
    return deduped


def run_qlib_workflow_dry_run_loader(
    *,
    config_path: str,
    input_override: str | None = None,
) -> WorkflowDryRunLoaderReport:
    qlib_api = probe_qlib_dataset_api()
    workflow_config = build_training_disabled_qlib_workflow_config(
        config_path=config_path,
        input_override=input_override,
    )
    class_paths = _build_class_paths(config_path)
    class_report = resolve_dotted_paths(class_paths)

    issues: list[WorkflowDryRunIssue] = []

    training_enabled = bool(workflow_config.get("experiment", {}).get("training_enabled", True))
    training_executed = bool(workflow_config.get("experiment", {}).get("training_executed", True))
    model_enabled = bool(workflow_config.get("model", {}).get("enabled", True))
    model_constructed = bool(workflow_config.get("model", {}).get("constructed", True))
    qlib_workflow_executed = bool(workflow_config.get("workflow", {}).get("execute_workflow", True))
    qlib_initialized = bool(workflow_config.get("workflow", {}).get("qlib_initialized", True))

    if training_enabled:
        issues.append(WorkflowDryRunIssue("error", "training_enabled_true", "training.enabled must be false"))
    if training_executed:
        issues.append(WorkflowDryRunIssue("error", "training_executed_true", "training_executed must be false"))
    if model_enabled:
        issues.append(WorkflowDryRunIssue("error", "model_enabled_true", "model.enabled must be false"))
    if model_constructed:
        issues.append(WorkflowDryRunIssue("error", "model_constructed_true", "model.constructed must be false"))
    if qlib_workflow_executed:
        issues.append(WorkflowDryRunIssue("error", "workflow_execute_true", "workflow.execute_workflow must be false"))
    if qlib_initialized:
        issues.append(WorkflowDryRunIssue("error", "qlib_initialized_true", "workflow.qlib_initialized must be false"))

    unresolved_map = {item.dotted_path: item for item in class_report.unresolved}
    dataset_class_path = workflow_config.get("dataset", {}).get("class", "")
    workflow_bridge_path = load_experiment_config(config_path).workflow_bridge.workflow_class

    dataset_adapter_resolved = dataset_class_path not in unresolved_map
    workflow_bridge_resolved = workflow_bridge_path not in unresolved_map

    if not dataset_adapter_resolved:
        issues.append(
            WorkflowDryRunIssue(
                "error",
                "dataset_adapter_unresolved",
                f"Failed to resolve dataset adapter class: {dataset_class_path}",
            )
        )

    if not workflow_bridge_resolved:
        issues.append(
            WorkflowDryRunIssue(
                "error",
                "workflow_bridge_unresolved",
                f"Failed to resolve workflow bridge class: {workflow_bridge_path}",
            )
        )

    blockers = [item.message for item in issues if item.severity == "error"]
    warnings = [item.message for item in issues if item.severity != "error"]
    if not qlib_api.qlib_available:
        warnings.append("Qlib import is unavailable; dry-run loader result is config-only.")

    return WorkflowDryRunLoaderReport(
        config_name=workflow_config.get("experiment", {}).get("name", ""),
        workflow_config_built=True,
        workflow_config=workflow_config,
        class_resolution=class_report.to_dict(),
        qlib_available=qlib_api.qlib_available,
        qlib_initialized=qlib_initialized,
        qlib_workflow_executed=qlib_workflow_executed,
        training_enabled=training_enabled,
        training_executed=training_executed,
        model_enabled=model_enabled,
        model_constructed=model_constructed,
        dataset_adapter_resolved=dataset_adapter_resolved,
        workflow_bridge_resolved=workflow_bridge_resolved,
        issues=issues,
        blockers=blockers,
        warnings=list(dict.fromkeys(warnings)),
    )
