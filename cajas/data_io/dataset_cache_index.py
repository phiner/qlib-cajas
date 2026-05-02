"""Dataset cache index builder from dataset manifests."""

from __future__ import annotations

import json
from pathlib import Path


def build_dataset_cache_index(*, manifest: dict, cache_root: str | Path) -> dict:
    root = Path(cache_root).expanduser().resolve()
    entries: list[dict] = []
    for src in manifest.get("source_files", []):
        cache_key = f"{Path(src['path']).stem}_{src.get('schema_fingerprint', '')[:12]}"
        target = root / cache_key
        entries.append(
            {
                "source_path": src["path"],
                "source_size_bytes": src.get("size_bytes"),
                "source_schema_fingerprint": src.get("schema_fingerprint"),
                "cache_key": cache_key,
                "cache_target_dir": target.as_posix(),
                "stale": False,
            }
        )
    return {
        "schema_version": "v1",
        "dataset_id": manifest.get("dataset_id"),
        "cache_root": root.as_posix(),
        "entries": entries,
    }


def detect_stale_cache(*, cache_index: dict, refreshed_manifest: dict) -> dict:
    by_path = {x["path"]: x for x in refreshed_manifest.get("source_files", [])}
    stale_count = 0
    for entry in cache_index.get("entries", []):
        src = by_path.get(entry.get("source_path"))
        if not src:
            entry["stale"] = True
            stale_count += 1
            continue
        if src.get("size_bytes") != entry.get("source_size_bytes"):
            entry["stale"] = True
            stale_count += 1
    cache_index["stale_entry_count"] = stale_count
    return cache_index


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
