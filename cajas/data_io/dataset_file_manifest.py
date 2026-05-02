"""Dataset file manifest builder for reusable CSV metadata."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from cajas.data_io.large_csv_metadata import inspect_large_csv_metadata


def _fingerprint(columns: list[str]) -> str:
    s = "|".join(columns)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_dataset_file_manifest(*, data_root: str | Path, pattern: str, include_hash: bool = False, count_rows: bool = False) -> dict:
    root = Path(data_root).expanduser().resolve()
    files = sorted(root.glob(pattern))
    entries: list[dict] = []
    warnings: list[str] = []
    for f in files:
        meta = inspect_large_csv_metadata(
            input_path=f,
            sample_lines=100,
            count_rows=count_rows,
            compute_hash=include_hash,
        )
        entries.append(
            {
                "path": meta["path"],
                "size_bytes": meta["size_bytes"],
                "header_columns": meta["header_columns"],
                "row_count": meta["row_count"],
                "row_count_mode": meta["row_count_mode"],
                "sha256": meta["sha256"],
                "warnings": meta["warnings"],
                "schema_fingerprint": _fingerprint(meta["header_columns"]),
            }
        )
        warnings.extend(meta["warnings"])

    dataset_id = pattern.lower().replace("*", "all").replace(" ", "_")
    return {
        "schema_version": "v1",
        "dataset_id": dataset_id,
        "data_root": root.as_posix(),
        "pattern": pattern,
        "generated_time_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": entries,
        "row_count_status": "available" if count_rows else "not_requested",
        "timestamp_range_status": "sample_only",
        "checksum_status": "available" if include_hash else "not_requested",
        "reusable": bool(entries),
        "warnings": sorted(set(warnings)),
    }
