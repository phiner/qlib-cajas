"""Experiment artifact writer for qlib model bridge runs."""

from __future__ import annotations

import json
from pathlib import Path


def write_experiment_artifacts(*, out_dir: str | Path, artifacts: dict) -> dict:
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, payload in artifacts.items():
        path = out / name
        if name.endswith(".json"):
            path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")
        paths[name] = str(path)
    return paths
