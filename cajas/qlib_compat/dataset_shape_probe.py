"""PreparedDataset shape probe toward DatasetH-style compatibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.config.experiment_config import build_workflow_config, load_experiment_config
from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.handlers.prepared_csv_handler import LEAKAGE_COLUMNS
from cajas.qlib_compat.qlib_probe import probe_qlib_dataset_api


@dataclass(frozen=True)
class SegmentShapeProbe:
    segment: str
    feature_rows: int
    feature_cols: int
    label_rows: int
    feature_index_name: str | None
    label_index_name: str | None
    feature_columns: list[str]
    label_name: str
    row_count_match: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DatasetHShapeProbeReport:
    config_name: str
    label_col: str
    qlib_dataset_api: dict
    feature_count: int
    segments: list[SegmentShapeProbe]
    compatible_shape: bool
    blockers: list[str]
    warnings: list[str]
    training_executed: bool

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "label_col": self.label_col,
            "qlib_dataset_api": self.qlib_dataset_api,
            "feature_count": self.feature_count,
            "segments": [s.to_dict() for s in self.segments],
            "compatible_shape": self.compatible_shape,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "training_executed": self.training_executed,
        }


def run_dataset_h_shape_probe(*, config_path: str, input_override: str | None = None) -> DatasetHShapeProbeReport:
    cfg = load_experiment_config(config_path)
    wf_cfg = build_workflow_config(cfg, csv_path_override=input_override)

    ds = PreparedDataset(csv_path=wf_cfg.csv_path, label_col=wf_cfg.label_col, segments=wf_cfg.segments)
    qlib_status = probe_qlib_dataset_api()

    segments: list[SegmentShapeProbe] = []
    blockers: list[str] = []
    warnings: list[str] = []

    if not qlib_status.qlib_available:
        warnings.append("Qlib unavailable; DatasetH compatibility is shape-only in this environment.")
    if not qlib_status.dataset_h_available:
        warnings.append("DatasetH unavailable; shape probe still completed.")

    for segment_name in wf_cfg.segments:
        try:
            features, labels = ds.prepare(segment_name)
        except ValueError as exc:
            blockers.append(f"Segment probe failed for {segment_name}: {exc}")
            segments.append(
                SegmentShapeProbe(
                    segment=segment_name,
                    feature_rows=0,
                    feature_cols=0,
                    label_rows=0,
                    feature_index_name=None,
                    label_index_name=None,
                    feature_columns=[],
                    label_name=wf_cfg.label_col,
                    row_count_match=False,
                )
            )
            continue
        leakage_found = sorted(set(features.columns).intersection(LEAKAGE_COLUMNS))
        row_count_match = len(features) == len(labels)
        if len(features) == 0:
            blockers.append(f"Segment has zero rows: {segment_name}")
        if not row_count_match:
            blockers.append(f"Feature/label row mismatch in segment: {segment_name}")
        if leakage_found:
            blockers.append(
                f"Leakage columns found in features for segment {segment_name}: {', '.join(leakage_found)}"
            )

        segments.append(
            SegmentShapeProbe(
                segment=segment_name,
                feature_rows=int(features.shape[0]),
                feature_cols=int(features.shape[1]),
                label_rows=int(labels.shape[0]),
                feature_index_name=features.index.name,
                label_index_name=labels.index.name,
                feature_columns=[str(c) for c in features.columns.tolist()],
                label_name=str(labels.name or wf_cfg.label_col),
                row_count_match=row_count_match,
            )
        )

    feature_count = len(ds.feature_columns)
    if feature_count <= 0:
        blockers.append("No feature columns available.")

    compatible_shape = len(blockers) == 0

    return DatasetHShapeProbeReport(
        config_name=cfg.name,
        label_col=wf_cfg.label_col,
        qlib_dataset_api=qlib_status.to_dict(),
        feature_count=feature_count,
        segments=segments,
        compatible_shape=compatible_shape,
        blockers=blockers,
        warnings=list(dict.fromkeys(warnings)),
        training_executed=False,
    )
