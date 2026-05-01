"""Local DatasetH-like shim around PreparedDataset for API-shape compatibility checks.

This shim is not a real Qlib DatasetH subclass and does not implement full Qlib semantics.
"""

from __future__ import annotations

from cajas.datasets.prepared_dataset import PreparedDataset


class PreparedDatasetHLike:
    def __init__(self, prepared_dataset: PreparedDataset) -> None:
        self._prepared_dataset = prepared_dataset

    def prepare(self, segments, col_set=None, data_key=None):
        _ = col_set
        _ = data_key
        if isinstance(segments, str):
            return self._prepared_dataset.prepare(segments)
        if isinstance(segments, (list, tuple)):
            return {segment: self._prepared_dataset.prepare(segment) for segment in segments}
        raise TypeError("segments must be a string or a list/tuple of strings")
