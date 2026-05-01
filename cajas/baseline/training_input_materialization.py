"""Materialize training input previews for inspection-only baseline preparation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from cajas.baseline.label_encoding import (
    default_future_direction_8_encoding,
    encode_labels_for_preview,
    preview_label_encoding,
)
from cajas.baseline.metric_plan import build_multiclass_metric_plan
from cajas.config.experiment_config import build_workflow_config, load_experiment_config
from cajas.datasets.prepared_dataset import PreparedDataset


@dataclass(frozen=True)
class SegmentMaterializationSummary:
    segment: str
    feature_rows: int
    feature_cols: int
    label_rows: int
    encoded_label_rows: int
    output_files: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TrainingInputMaterializationReport:
    config_name: str
    label_col: str
    feature_count: int
    label_encoding: dict
    metric_plan: dict
    segments: list[SegmentMaterializationSummary]
    training_enabled: bool
    training_executed: bool
    model_built: bool

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "label_col": self.label_col,
            "feature_count": self.feature_count,
            "label_encoding": self.label_encoding,
            "metric_plan": self.metric_plan,
            "segments": [s.to_dict() for s in self.segments],
            "training_enabled": self.training_enabled,
            "training_executed": self.training_executed,
            "model_built": self.model_built,
        }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def materialize_training_inputs_preview(
    *,
    config_path: str,
    output_dir: str | Path,
    run_name: str,
    input_override: str | None = None,
    write_csv: bool = True,
) -> TrainingInputMaterializationReport:
    cfg = load_experiment_config(config_path)
    wf_cfg = build_workflow_config(cfg, csv_path_override=input_override)

    dataset = PreparedDataset(
        csv_path=wf_cfg.csv_path,
        label_col=wf_cfg.label_col,
        segments=wf_cfg.segments,
    )
    plan = default_future_direction_8_encoding(label_col=wf_cfg.label_col)
    metric_plan = build_multiclass_metric_plan(target_label=wf_cfg.label_col)

    base = Path(output_dir).expanduser().resolve()
    run_dir = base / run_name
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    segments: list[SegmentMaterializationSummary] = []
    preview_by_segment: dict[str, dict] = {}

    for segment_name in ("train", "valid", "test"):
        features, labels = dataset.prepare(segment_name)
        label_preview = preview_label_encoding(labels, plan)
        if label_preview.issues:
            issue_text = "; ".join(i["message"] for i in label_preview.issues)
            raise ValueError(f"Label encoding issues in segment '{segment_name}': {issue_text}")

        encoded = encode_labels_for_preview(labels, plan)
        output_files: dict[str, str] = {}

        if write_csv:
            f_path = run_dir / f"{segment_name}_features.csv"
            l_path = run_dir / f"{segment_name}_labels.csv"
            e_path = run_dir / f"{segment_name}_encoded_labels.csv"
            features.to_csv(f_path, index=False)
            labels.to_frame(name=wf_cfg.label_col).to_csv(l_path, index=False)
            encoded.to_frame(name=f"{wf_cfg.label_col}_encoded").to_csv(e_path, index=False)
            output_files.update(
                {
                    "features_csv": str(f_path),
                    "labels_csv": str(l_path),
                    "encoded_labels_csv": str(e_path),
                }
            )

        segments.append(
            SegmentMaterializationSummary(
                segment=segment_name,
                feature_rows=int(features.shape[0]),
                feature_cols=int(features.shape[1]),
                label_rows=int(labels.shape[0]),
                encoded_label_rows=int(encoded.shape[0]),
                output_files=output_files,
            )
        )
        preview_by_segment[segment_name] = label_preview.to_dict()

    label_preview_payload = {
        "label_col": plan.label_col,
        "mapping": plan.mapping,
        "segments": preview_by_segment,
    }
    metric_payload = metric_plan.to_dict()

    report = TrainingInputMaterializationReport(
        config_name=cfg.name,
        label_col=wf_cfg.label_col,
        feature_count=len(dataset.feature_columns),
        label_encoding=label_preview_payload,
        metric_plan=metric_payload,
        segments=segments,
        training_enabled=bool(cfg.training.enabled),
        training_executed=False,
        model_built=False,
    )

    _write_json(run_dir / "training_input_materialization_report.json", report.to_dict())
    _write_json(run_dir / "label_encoding_preview.json", label_preview_payload)
    _write_json(run_dir / "metric_plan.json", metric_payload)

    return report
