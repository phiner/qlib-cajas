"""Real Qlib DatasetH adapter probe wrapper around PreparedDataset.

This module does not call qlib.init() and does not trigger training.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from cajas.datasets.prepared_dataset import PreparedDataset

try:  # pragma: no cover
    from qlib.data.dataset import DatasetH as QlibDatasetH
except Exception:  # pragma: no cover
    QlibDatasetH = None


@dataclass(frozen=True)
class PreparedQlibDatasetHAdapterDescription:
    qlib_available: bool
    is_true_qlib_subclass: bool
    adapter_class: str
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


class PreparedQlibDatasetHAdapter:
    """Adapter that exposes Qlib-like `prepare` behavior over PreparedDataset."""

    def __init__(self, prepared_dataset: PreparedDataset) -> None:
        self._prepared_dataset = prepared_dataset

    @property
    def is_qlib_available(self) -> bool:
        return QlibDatasetH is not None

    @property
    def is_true_qlib_subclass(self) -> bool:
        return False

    def prepare(self, segments, col_set=None, data_key=None):
        _ = col_set
        _ = data_key
        if isinstance(segments, str):
            return self._prepared_dataset.prepare(segments)
        if isinstance(segments, (list, tuple)):
            return {segment: self._prepared_dataset.prepare(segment) for segment in segments}
        raise TypeError("segments must be a string or a list/tuple of strings")

    def describe(self) -> dict:
        return PreparedQlibDatasetHAdapterDescription(
            qlib_available=self.is_qlib_available,
            is_true_qlib_subclass=self.is_true_qlib_subclass,
            adapter_class=f"{self.__class__.__module__}.{self.__class__.__name__}",
            note=(
                "Composition adapter for probe usage. It stays outside qlib core and does not call qlib.init()."
            ),
        ).to_dict()
