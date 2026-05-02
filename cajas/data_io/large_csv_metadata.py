"""Large CSV metadata scanner with cheap defaults."""

from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


def _line_stream(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line.rstrip("\n")


def _sample_rows(path: Path, sample_lines: int) -> list[str]:
    rows: list[str] = []
    for i, line in enumerate(_line_stream(path)):
        if i >= sample_lines:
            break
        rows.append(line)
    return rows


def _guess_delimiter(header: str) -> str:
    for delim in [",", "\t", ";", "|"]:
        if delim in header:
            return delim
    return ","


def _count_rows_streaming(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f) - 1


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_large_csv_metadata(
    *,
    input_path: str | Path,
    sample_lines: int = 100,
    count_rows: bool = False,
    compute_hash: bool = False,
    chunk_size: int = 100_000,
) -> dict:
    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    stat = path.stat()
    sample = _sample_rows(path, max(2, sample_lines))
    header = sample[0] if sample else ""
    delim = _guess_delimiter(header)
    columns = next(csv.reader([header], delimiter=delim), []) if header else []

    numeric_candidates: list[str] = []
    time_candidates: list[str] = []
    if len(sample) > 1 and columns:
        row = next(csv.reader([sample[1]], delimiter=delim), [])
        for c, v in zip(columns, row):
            c_low = c.lower()
            if any(x in c_low for x in ["time", "date", "timestamp"]):
                time_candidates.append(c)
            try:
                float(v)
                numeric_candidates.append(c)
            except Exception:
                pass

    warns: list[str] = []
    if " " in path.name:
        warns.append("filename contains spaces")

    row_count = None
    if count_rows:
        row_count = max(0, _count_rows_streaming(path))

    file_hash = None
    if compute_hash:
        file_hash = _sha256(path)

    dataset_id = path.stem.lower().replace(" ", "_").replace(".", "_")

    return {
        "schema_version": "v1",
        "path": path.as_posix(),
        "size_bytes": stat.st_size,
        "modified_time_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "sample_lines": sample[:sample_lines],
        "header_columns": columns,
        "delimiter": delim,
        "row_count": row_count,
        "row_count_mode": "streaming" if count_rows else "not_requested",
        "sha256": file_hash,
        "hash_mode": "full" if compute_hash else "not_requested",
        "chunk_size_hint": chunk_size,
        "time_column_candidates": time_candidates,
        "numeric_column_candidates": numeric_candidates,
        "warnings": warns,
        "suggested_dataset_id": dataset_id,
    }
