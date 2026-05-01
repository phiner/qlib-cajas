"""Baseline readiness gate combining config, workflow, and audits."""

from __future__ import annotations

from dataclasses import dataclass

from cajas.audits.feature_audit import audit_features
from cajas.audits.label_audit import audit_labels
from cajas.config.experiment_config import (
    assert_training_disabled,
    build_workflow_config,
    load_experiment_config,
    validate_experiment_config,
)
from cajas.workflows.prepared_workflow import PreparedWorkflow


@dataclass(frozen=True)
class BaselineReadinessReport:
    ready: bool
    training_enabled: bool
    training_executed: bool
    config_name: str
    label_col: str
    feature_count: int
    segments: dict[str, dict[str, int]]
    feature_audit: dict
    label_audit: dict
    issues: list[dict]

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "training_enabled": self.training_enabled,
            "training_executed": self.training_executed,
            "config_name": self.config_name,
            "label_col": self.label_col,
            "feature_count": self.feature_count,
            "segments": self.segments,
            "feature_audit": self.feature_audit,
            "label_audit": self.label_audit,
            "issues": self.issues,
        }


def run_baseline_readiness_check(
    *,
    config_path: str,
    input_override: str | None = None,
    strict: bool = False,
) -> BaselineReadinessReport:
    config = load_experiment_config(config_path)
    config_issues = validate_experiment_config(config)
    assert_training_disabled(config)

    wf_config = build_workflow_config(config, csv_path_override=input_override)
    workflow = PreparedWorkflow(wf_config)
    summary = workflow.dry_run()

    prepared = workflow.dataset.prepare_all()
    all_features = []
    all_labels = []
    segments: dict[str, dict[str, int]] = {}
    for name, (feat, lab) in prepared.items():
        all_features.append(feat)
        all_labels.append(lab)
        segments[name] = {"feature_rows": len(feat), "label_rows": len(lab)}

    features_df = all_features[0].iloc[0:0].copy() if not all_features else None
    if all_features:
        import pandas as pd

        features_df = pd.concat(all_features, ignore_index=True)
        labels_series = pd.concat(all_labels, ignore_index=True)
    else:
        raise ValueError("No segments prepared for readiness check")

    feature_report = audit_features(
        features_df,
        declared_leakage_columns=list(config.data_adapter.leakage_columns),
    )
    label_report = audit_labels(
        labels_series,
        label_col=config.data_adapter.label_col,
    )

    issues: list[dict] = []
    for issue in config_issues:
        issues.append(
            {"severity": "warning", "code": "CONFIG_WARNING", "message": issue}
        )
    issues.extend([i.to_dict() if hasattr(i, "to_dict") else i.__dict__ for i in feature_report.issues])
    issues.extend([i.to_dict() if hasattr(i, "to_dict") else i.__dict__ for i in label_report.issues])

    has_error = any(i["severity"] == "error" for i in issues)
    has_warning = any(i["severity"] == "warning" for i in issues)
    ready = not has_error and not (strict and has_warning)

    return BaselineReadinessReport(
        ready=ready,
        training_enabled=config.training.enabled,
        training_executed=summary.training_executed,
        config_name=config.name,
        label_col=config.data_adapter.label_col,
        feature_count=len(summary.feature_columns),
        segments=segments,
        feature_audit=feature_report.to_dict(),
        label_audit=label_report.to_dict(),
        issues=issues,
    )
