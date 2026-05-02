"""Data IO utilities for large CSV readiness and cache manifests."""

from .large_csv_metadata import inspect_large_csv_metadata
from .dataset_file_manifest import build_dataset_file_manifest
from .chunked_csv_reader import iter_csv_chunks
from .fx_kline_schema import inspect_fx_kline_schema
from .dataset_cache_index import build_dataset_cache_index

__all__ = [
    "inspect_large_csv_metadata",
    "build_dataset_file_manifest",
    "iter_csv_chunks",
    "inspect_fx_kline_schema",
    "build_dataset_cache_index",
]
