"""External holdout dataset loader for arbitrary label variant columns."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


@dataclass(frozen=True)
class LabelVariantDatasetSummary:
    train_path: str
    holdout_path: str
    label_col: str
    feature_count: int
    train_rows: int
    holdout_rows: int
    label_distribution_train: dict[str, int]
    label_distribution_holdout: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


def _is_leak_col(col: str) -> bool:
    c = col.lower()
    return c.startswith("future_close_") or c.startswith("future_return_") or c.startswith("future_direction_")


class LabelVariantExternalHoldoutDataset:
    def __init__(
        self,
        *,
        train_path: str | Path,
        holdout_path: str | Path,
        label_col: str,
        leakage_columns: tuple[str, ...] = ("future_close_8", "future_return_8"),
        row_limit: int | None = None,
        allow_large_data: bool = False,
    ) -> None:
        self.train_path = Path(train_path).expanduser().resolve()
        self.holdout_path = Path(holdout_path).expanduser().resolve()
        self.label_col = label_col
        self.leakage_columns = set(leakage_columns)
        self._row_limit = row_limit
        self._allow_large_data = allow_large_data
        
        # Policy guard for large data reads
        policy = CsvLoadingPolicy(row_limit=row_limit, allow_large_data=allow_large_data)
        train_decision = evaluate_loading_decision(self.train_path, policy)
        holdout_decision = evaluate_loading_decision(self.holdout_path, policy)
        
        if not train_decision["can_full_read"] and row_limit is None:
            raise ValueError(f"train CSV requires row_limit or allow_large_data: {train_decision['warnings']}")
        if not holdout_decision["can_full_read"] and row_limit is None:
            raise ValueError(f"holdout CSV requires row_limit or allow_large_data: {holdout_decision['warnings']}")
        
        read_kwargs = {}
        if row_limit is not None:
            read_kwargs["nrows"] = row_limit
        
        self.train_frame = pd.read_csv(self.train_path, **read_kwargs)
        self.holdout_frame = pd.read_csv(self.holdout_path, **read_kwargs)
        if label_col not in self.train_frame.columns or label_col not in self.holdout_frame.columns:
            raise ValueError(f"label column missing: {label_col}")
        self._features = self._build_feature_columns()

    def _build_feature_columns(self) -> list[str]:
        cols = []
        for col in self.train_frame.columns:
            if col in {"datetime", "symbol", "timeframe", self.label_col}:
                continue
            if col in self.leakage_columns or _is_leak_col(col):
                continue
            if col in self.holdout_frame.columns and pd.api.types.is_numeric_dtype(self.train_frame[col]):
                cols.append(col)
        return cols

    @property
    def feature_columns(self) -> list[str]:
        return list(self._features)

    def prepare_train(self):
        mask = self.train_frame[self.label_col].notna()
        f = self.train_frame.loc[mask, self._features]
        y = self.train_frame.loc[mask, self.label_col].astype(str)
        return f, y

    def prepare_holdout(self):
        mask = self.holdout_frame[self.label_col].notna()
        f = self.holdout_frame.loc[mask, self._features]
        y = self.holdout_frame.loc[mask, self.label_col].astype(str)
        return f, y

    def summary(self) -> LabelVariantDatasetSummary:
        return LabelVariantDatasetSummary(
            train_path=str(self.train_path),
            holdout_path=str(self.holdout_path),
            label_col=self.label_col,
            feature_count=len(self._features),
            train_rows=int(self.train_frame[self.label_col].notna().sum()),
            holdout_rows=int(self.holdout_frame[self.label_col].notna().sum()),
            label_distribution_train={k: int(v) for k, v in self.train_frame[self.label_col].dropna().astype(str).value_counts().to_dict().items()},
            label_distribution_holdout={k: int(v) for k, v in self.holdout_frame[self.label_col].dropna().astype(str).value_counts().to_dict().items()},
        )
