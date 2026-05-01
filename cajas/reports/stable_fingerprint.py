"""Stable fingerprinting over normalized artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .artifact_normalizer import normalize_json_artifact, normalize_markdown_artifact


def _hash_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _file_fp(path: Path) -> tuple[str | None, str | None]:
    if path.suffix.lower() == ".json":
        rep = normalize_json_artifact(input_path=path)
        content = json.dumps(rep["normalized_payload"], ensure_ascii=True, sort_keys=True).encode("utf-8")
        return _hash_bytes(content), "json"
    if path.suffix.lower() == ".md":
        rep = normalize_markdown_artifact(input_path=path)
        return _hash_bytes(rep["normalized_text"].encode("utf-8")), "md"
    if path.suffix.lower() in {".csv", ".jsonl"}:
        txt = path.read_text(encoding="utf-8")
        txt = txt.replace(str(Path.cwd().resolve()), "<CWD>")
        return _hash_bytes(txt.encode("utf-8")), "text"
    return None, None


def build_stable_fingerprint(*, root: str | Path) -> dict:
    root_path = Path(root).expanduser().resolve()
    included: list[dict] = []
    skipped: list[str] = []

    for p in sorted(root_path.rglob("*")):
        if not p.is_file():
            continue
        fp, kind = _file_fp(p)
        rel = str(p.relative_to(root_path))
        if fp is None:
            skipped.append(rel)
            continue
        included.append({"relative_path": rel, "kind": kind, "stable_hash": fp})

    agg_src = "\n".join(f"{i['relative_path']}:{i['stable_hash']}" for i in included).encode("utf-8")
    aggregate = _hash_bytes(agg_src)
    return {
        "schema_version": "v1",
        "root": str(root_path),
        "included_files": included,
        "skipped_files": skipped,
        "aggregate_stable_hash": aggregate,
        "normalization_rule_summary": ["timestamp normalization", "tmp/cwd path normalization", "sorted json keys"],
        "warnings": [],
    }
