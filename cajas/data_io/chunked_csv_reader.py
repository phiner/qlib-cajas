"""Chunked CSV reader helpers with pandas-first fallback."""

from __future__ import annotations

import csv
from pathlib import Path


def _iter_csv_chunks_stdlib(path: Path, columns: list[str] | None, chunk_size: int, row_limit: int | None):
    emitted = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        current: list[dict] = []
        for row in reader:
            if columns:
                row = {k: row.get(k) for k in columns}
            current.append(row)
            emitted += 1
            if len(current) >= chunk_size:
                yield current
                current = []
            if row_limit is not None and emitted >= row_limit:
                break
        if current:
            yield current


def iter_csv_chunks(
    path: str | Path,
    columns: list[str] | None = None,
    chunk_size: int = 100_000,
    row_limit: int | None = None,
    parse_dates: list[str] | None = None,
    dtype: dict | None = None,
):
    p = Path(path).expanduser().resolve()
    try:
        import pandas as pd  # type: ignore

        kwargs = {
            "chunksize": chunk_size,
            "usecols": columns,
        }
        if parse_dates:
            kwargs["parse_dates"] = parse_dates
        if dtype:
            kwargs["dtype"] = dtype
        emitted = 0
        for chunk in pd.read_csv(p, **kwargs):
            if row_limit is not None and emitted >= row_limit:
                break
            if row_limit is not None and emitted + len(chunk) > row_limit:
                chunk = chunk.iloc[: row_limit - emitted]
            emitted += len(chunk)
            yield chunk
    except Exception:
        yield from _iter_csv_chunks_stdlib(p, columns, chunk_size, row_limit)
