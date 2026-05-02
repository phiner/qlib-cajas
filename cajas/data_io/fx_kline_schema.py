"""FX/K-line schema inspection helpers."""

from __future__ import annotations

from pathlib import Path

from cajas.data_io.large_csv_metadata import inspect_large_csv_metadata

ALIASES = {
    "timestamp": ["time", "date", "datetime", "timestamp", "time (utc)"],
    "open": ["open"],
    "high": ["high"],
    "low": ["low"],
    "close": ["close"],
    "volume": ["volume", "vol"],
}


def _normalize(c: str) -> str:
    return c.strip().lower()


def inspect_fx_kline_schema(*, csv_path: str | Path, strict: bool = False) -> dict:
    meta = inspect_large_csv_metadata(input_path=csv_path, sample_lines=20, count_rows=False, compute_hash=False)
    cols = meta.get("header_columns", [])
    normalized = {_normalize(c): c for c in cols}

    mapped: dict[str, str | None] = {}
    missing: list[str] = []
    for key, aliases in ALIASES.items():
        hit = None
        for a in aliases:
            if a in normalized:
                hit = normalized[a]
                break
        mapped[key] = hit
        if key in {"open", "high", "low", "close"} and hit is None:
            missing.append(key)

    warnings = list(meta.get("warnings", []))
    if missing:
        warnings.append(f"missing required OHLC columns: {','.join(missing)}")

    status = "pass" if not missing else "warn"
    if strict and missing:
        raise ValueError("missing required OHLC columns")

    return {
        "schema_version": "v1",
        "path": meta.get("path"),
        "status": status,
        "mapped_columns": mapped,
        "missing_required": missing,
        "numeric_column_candidates": meta.get("numeric_column_candidates", []),
        "time_column_candidates": meta.get("time_column_candidates", []),
        "warnings": warnings,
    }
