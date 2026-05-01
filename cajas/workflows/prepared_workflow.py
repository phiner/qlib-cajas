"""Qlib-inspired workflow dry-run bridge for prepared research datasets.

This module is an external cajas-layer workflow validator.
It is not a trading strategy and not a full Qlib runtime workflow.
It only validates dataset segment shapes for later integration steps.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.handlers.prepared_csv_handler import LEAKAGE_COLUMNS


@dataclass(frozen=True)
class PreparedWorkflowConfig:
    csv_path: str
    label_col: str = "future_direction_8"
    segments: dict[str, tuple[str, str]] | None = None


@dataclass(frozen=True)
class SegmentShape:
    segment: str
    feature_rows: int
    feature_cols: int
    label_rows: int
    label_name: str


@dataclass(frozen=True)
class PreparedWorkflowSummary:
    label_col: str
    feature_columns: list[str]
    segment_shapes: list[SegmentShape]
    leakage_columns_in_features: bool
    training_executed: bool = False

    def to_dict(self) -> dict:
        return {
            "label_col": self.label_col,
            "feature_columns": self.feature_columns,
            "segment_shapes": [asdict(s) for s in self.segment_shapes],
            "leakage_columns_in_features": self.leakage_columns_in_features,
            "training_executed": self.training_executed,
        }


class PreparedWorkflow:
    """Dataset workflow bridge for dry-run validation only."""

    def __init__(self, config: PreparedWorkflowConfig) -> None:
        self._config = config
        self._dataset = PreparedDataset(
            csv_path=config.csv_path,
            label_col=config.label_col,
            segments=config.segments,
        )

    @property
    def dataset(self) -> PreparedDataset:
        return self._dataset

    def prepare(self, segment: str):
        return self._dataset.prepare(segment)

    def dry_run(self) -> PreparedWorkflowSummary:
        if not self._dataset.feature_columns:
            raise ValueError("No feature columns available")

        leakage_found = bool(
            set(self._dataset.feature_columns).intersection(LEAKAGE_COLUMNS)
        )
        if leakage_found:
            raise ValueError("Leakage columns found in features")

        segment_shapes: list[SegmentShape] = []
        for segment in self._dataset.segments:
            features, labels = self.prepare(segment)
            if len(features) != len(labels):
                raise ValueError(f"Feature/label row mismatch in segment: {segment}")
            segment_shapes.append(
                SegmentShape(
                    segment=segment,
                    feature_rows=len(features),
                    feature_cols=features.shape[1],
                    label_rows=len(labels),
                    label_name=getattr(labels, "name", self._config.label_col)
                    or self._config.label_col,
                )
            )

        return PreparedWorkflowSummary(
            label_col=self._config.label_col,
            feature_columns=self._dataset.feature_columns,
            segment_shapes=segment_shapes,
            leakage_columns_in_features=False,
            training_executed=False,
        )
