"""Compare PreparedDataset adapters for Qlib DatasetH API-shape compatibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.config.experiment_config import build_workflow_config, load_experiment_config
from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.handlers.prepared_csv_handler import LEAKAGE_COLUMNS
from cajas.qlib_compat.prepared_dataset_h_adapter import PreparedQlibDatasetHAdapter
from cajas.qlib_compat.prepared_dataset_h_like import PreparedDatasetHLike


@dataclass(frozen=True)
class AdapterSegmentComparison:
    segment: str
    prepared_rows: int
    h_like_rows: int
    qlib_adapter_rows: int
    prepared_feature_cols: int
    h_like_feature_cols: int
    qlib_adapter_feature_cols: int
    label_rows_match: bool
    feature_shape_match: bool
    label_values_match: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AdapterComparisonReport:
    config_name: str
    qlib_available: bool
    qlib_adapter_constructed: bool
    qlib_adapter_true_subclass: bool
    feature_count: int
    segments: list[AdapterSegmentComparison]
    compatible: bool
    blockers: list[str]
    warnings: list[str]
    training_executed: bool

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "qlib_available": self.qlib_available,
            "qlib_adapter_constructed": self.qlib_adapter_constructed,
            "qlib_adapter_true_subclass": self.qlib_adapter_true_subclass,
            "feature_count": self.feature_count,
            "segments": [s.to_dict() for s in self.segments],
            "compatible": self.compatible,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "training_executed": self.training_executed,
        }


def run_adapter_comparison_probe(*, config_path: str, input_override: str | None = None) -> AdapterComparisonReport:
    cfg = load_experiment_config(config_path)
    wf_cfg = build_workflow_config(cfg, csv_path_override=input_override)

    prepared = PreparedDataset(csv_path=wf_cfg.csv_path, label_col=wf_cfg.label_col, segments=wf_cfg.segments)
    h_like = PreparedDatasetHLike(prepared)
    qlib_adapter = PreparedQlibDatasetHAdapter(prepared)

    blockers: list[str] = []
    warnings: list[str] = []
    segments: list[AdapterSegmentComparison] = []

    if not qlib_adapter.is_qlib_available:
        warnings.append("Qlib unavailable; adapter still runs in composition probe mode.")
    if not qlib_adapter.is_true_qlib_subclass:
        warnings.append("Adapter is not a true Qlib DatasetH subclass; composition mode is active.")

    for segment_name in wf_cfg.segments:
        px, py = prepared.prepare(segment_name)
        hx, hy = h_like.prepare(segment_name)
        qx, qy = qlib_adapter.prepare(segment_name)

        leakage = sorted(set(px.columns).intersection(LEAKAGE_COLUMNS))
        if leakage:
            blockers.append(
                f"Leakage columns found in features for segment {segment_name}: {', '.join(leakage)}"
            )

        label_rows_match = len(py) == len(hy) == len(qy)
        feature_shape_match = px.shape == hx.shape == qx.shape
        label_values_match = py.reset_index(drop=True).equals(
            hy.reset_index(drop=True)
        ) and py.reset_index(drop=True).equals(qy.reset_index(drop=True))

        if not label_rows_match:
            blockers.append(f"Label row mismatch across adapters in segment: {segment_name}")
        if not feature_shape_match:
            blockers.append(f"Feature shape mismatch across adapters in segment: {segment_name}")
        if not label_values_match:
            blockers.append(f"Label values mismatch across adapters in segment: {segment_name}")

        segments.append(
            AdapterSegmentComparison(
                segment=segment_name,
                prepared_rows=int(px.shape[0]),
                h_like_rows=int(hx.shape[0]),
                qlib_adapter_rows=int(qx.shape[0]),
                prepared_feature_cols=int(px.shape[1]),
                h_like_feature_cols=int(hx.shape[1]),
                qlib_adapter_feature_cols=int(qx.shape[1]),
                label_rows_match=label_rows_match,
                feature_shape_match=feature_shape_match,
                label_values_match=label_values_match,
            )
        )

    compatible = len(blockers) == 0

    return AdapterComparisonReport(
        config_name=cfg.name,
        qlib_available=qlib_adapter.is_qlib_available,
        qlib_adapter_constructed=True,
        qlib_adapter_true_subclass=qlib_adapter.is_true_qlib_subclass,
        feature_count=len(prepared.feature_columns),
        segments=segments,
        compatible=compatible,
        blockers=blockers,
        warnings=list(dict.fromkeys(warnings)),
        training_executed=False,
    )
