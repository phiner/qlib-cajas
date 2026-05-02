"""Central CSV loading policy helpers for full-read guardrails."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CsvLoadingPolicy:
    row_limit: int | None = None
    chunk_size: int | None = None
    sample_only: bool = False
    allow_large_data: bool = False
    include_real_data: bool = False
    selected_columns: list[str] | None = None
    use_cache: bool = False
    cache_root: str | None = None
    manifest: str | None = None
    max_bytes_without_allow_large_data: int = 8 * 1024 * 1024


def classify_size(path: str | Path) -> str:
    size = Path(path).expanduser().resolve().stat().st_size
    if size < 1 * 1024 * 1024:
        return "tiny"
    if size < 16 * 1024 * 1024:
        return "small"
    return "large"


def evaluate_loading_decision(path: str | Path, policy: CsvLoadingPolicy) -> dict:
    p = Path(path).expanduser().resolve()
    size = p.stat().st_size
    size_class = classify_size(p)
    warnings: list[str] = []

    should_chunk = bool(policy.chunk_size or policy.row_limit or policy.sample_only)
    can_full_read = True
    if size > policy.max_bytes_without_allow_large_data and not policy.allow_large_data:
        can_full_read = False
        warnings.append(
            f"file exceeds max_bytes_without_allow_large_data ({size} > {policy.max_bytes_without_allow_large_data})"
        )

    mode = "full_read"
    if policy.sample_only or policy.row_limit:
        mode = "sampled_read"
    elif should_chunk:
        mode = "chunked_read"
    elif not can_full_read:
        mode = "blocked_full_read"

    return {
        "path": p.as_posix(),
        "size_bytes": size,
        "size_class": size_class,
        "mode": mode,
        "can_full_read": can_full_read,
        "warnings": warnings,
        "policy": asdict(policy),
    }
