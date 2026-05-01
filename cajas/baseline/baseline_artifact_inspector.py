"""Inspect local baseline run artifacts without retraining."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


REQUIRED_FILES = [
    "run_manifest.json",
    "training_config.json",
    "feature_columns.json",
    "label_encoding.json",
    "label_distribution.json",
    "metrics_valid.json",
    "metrics_test.json",
    "confusion_matrix_valid.csv",
    "confusion_matrix_test.csv",
    "predictions_valid.csv",
    "predictions_test.csv",
    "model_metadata.json",
    "model.joblib",
]


@dataclass(frozen=True)
class BaselineArtifactIssue:
    severity: str
    code: str
    message: str
    file: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BaselineArtifactInspectionReport:
    run_dir: str
    run_name: str
    required_files_present: bool
    artifact_files: list[str]
    model_family_used: str | None
    target_label: str | None
    feature_count: int | None
    train_rows: int | None
    valid_rows: int | None
    test_rows: int | None
    metrics_valid: dict
    metrics_test: dict
    metrics_holdout: dict
    issues: list[BaselineArtifactIssue]
    warnings: list[str]
    training_executed: bool | None
    qlib_workflow_executed: bool

    def to_dict(self) -> dict:
        return {
            "run_dir": self.run_dir,
            "run_name": self.run_name,
            "required_files_present": self.required_files_present,
            "artifact_files": list(self.artifact_files),
            "model_family_used": self.model_family_used,
            "target_label": self.target_label,
            "feature_count": self.feature_count,
            "train_rows": self.train_rows,
            "valid_rows": self.valid_rows,
            "test_rows": self.test_rows,
            "metrics_valid": self.metrics_valid,
            "metrics_test": self.metrics_test,
            "metrics_holdout": self.metrics_holdout,
            "issues": [item.to_dict() for item in self.issues],
            "warnings": list(self.warnings),
            "training_executed": self.training_executed,
            "qlib_workflow_executed": self.qlib_workflow_executed,
        }


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file must be an object: {path}")
    return payload


def inspect_baseline_run_artifacts(run_dir: str | Path) -> BaselineArtifactInspectionReport:
    base = Path(run_dir).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Run directory not found: {base}")

    artifact_files = sorted(path.name for path in base.glob("*") if path.is_file())
    issues: list[BaselineArtifactIssue] = []
    warnings: list[str] = []

    missing = [name for name in REQUIRED_FILES if not (base / name).exists()]
    if missing:
        for name in missing:
            issues.append(
                BaselineArtifactIssue(
                    severity="error",
                    code="missing_required_file",
                    message=f"Required artifact file is missing: {name}",
                    file=name,
                )
            )

    run_manifest = _load_json(base / "run_manifest.json") if (base / "run_manifest.json").exists() else {}
    training_cfg = _load_json(base / "training_config.json") if (base / "training_config.json").exists() else {}
    feature_cols = _load_json(base / "feature_columns.json") if (base / "feature_columns.json").exists() else {}
    model_meta = _load_json(base / "model_metadata.json") if (base / "model_metadata.json").exists() else {}
    metrics_valid = _load_json(base / "metrics_valid.json") if (base / "metrics_valid.json").exists() else {}
    metrics_test = _load_json(base / "metrics_test.json") if (base / "metrics_test.json").exists() else {}
    metrics_holdout = _load_json(base / "metrics_holdout.json") if (base / "metrics_holdout.json").exists() else {}

    feature_count = model_meta.get("feature_count")
    if feature_count is None and isinstance(feature_cols.get("feature_columns"), list):
        feature_count = len(feature_cols["feature_columns"])

    if not metrics_valid:
        warnings.append("metrics_valid.json unavailable or empty")
    if not metrics_test:
        warnings.append("metrics_test.json unavailable or empty")
    if not metrics_holdout:
        warnings.append("metrics_holdout.json unavailable or empty")

    return BaselineArtifactInspectionReport(
        run_dir=str(base),
        run_name=str(training_cfg.get("run_name", base.name)),
        required_files_present=len(missing) == 0,
        artifact_files=artifact_files,
        model_family_used=model_meta.get("model_family_used"),
        target_label=model_meta.get("target_label"),
        feature_count=int(feature_count) if feature_count is not None else None,
        train_rows=model_meta.get("train_rows"),
        valid_rows=model_meta.get("valid_rows"),
        test_rows=model_meta.get("test_rows"),
        metrics_valid=metrics_valid,
        metrics_test=metrics_test,
        metrics_holdout=metrics_holdout,
        issues=issues,
        warnings=warnings,
        training_executed=run_manifest.get("training_executed"),
        qlib_workflow_executed=bool(run_manifest.get("qlib_workflow_executed", False)),
    )
