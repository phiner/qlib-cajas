"""Small helper for writing baseline-related JSON report artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


def write_baseline_reports(
    *,
    output_dir: str | Path,
    run_name: str,
    reports: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    base = Path(output_dir).expanduser().resolve()
    run_dir = base / run_name
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    out: dict[str, str] = {"run_dir": str(run_dir)}
    for report_name, payload in reports.items():
        target = run_dir / f"{report_name}.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        out[report_name] = str(target)
    return out
