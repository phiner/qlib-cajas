"""Small reusable filesystem and JSON helpers for runtime audits."""

from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from pathlib import Path


def count_files(root: str | Path) -> int:
    path = Path(root).expanduser()
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def summarize_extension_counts(root: str | Path, top_n: int = 20) -> list[dict]:
    path = Path(root).expanduser()
    if not path.exists():
        return []
    ctr: Counter[str] = Counter()
    for p in path.rglob("*"):
        if p.is_file():
            ctr[p.suffix.lower() or "<no_ext>"] += 1
    return [{"extension": k, "count": v} for k, v in ctr.most_common(top_n)]


def summarize_largest_files(root: str | Path, top_n: int = 20) -> list[dict]:
    path = Path(root).expanduser()
    if not path.exists():
        return []
    rows: list[dict] = []
    for p in path.rglob("*"):
        if p.is_file():
            try:
                size = p.stat().st_size
            except OSError:
                continue
            rows.append({"path": p.as_posix(), "bytes": size})
    rows.sort(key=lambda x: x["bytes"], reverse=True)
    return rows[:top_n]


def summarize_directory_depth(root: str | Path) -> dict:
    path = Path(root).expanduser()
    if not path.exists():
        return {"max_depth": 0, "avg_depth": 0.0}
    depths: list[int] = []
    base_parts = len(path.resolve().parts)
    for p in path.rglob("*"):
        depths.append(max(0, len(p.resolve().parts) - base_parts))
    if not depths:
        return {"max_depth": 0, "avg_depth": 0.0}
    return {"max_depth": max(depths), "avg_depth": round(sum(depths) / len(depths), 3)}


def safe_json_read(path: str | Path, default: dict | list | None = None):
    p = Path(path).expanduser()
    if not p.exists():
        return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8"))


def safe_json_write(path: str | Path, payload: dict | list, atomic: bool = False) -> Path:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if not atomic:
        p.write_text(text, encoding="utf-8")
        return p
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=p.parent, delete=False) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, p)
    return p
