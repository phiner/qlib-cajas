"""Research pipeline manifest collector for reproducibility and readiness checks."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_summary(cwd: Path) -> dict:
    rep = {"branch": None, "commit": None, "dirty": None, "warning": None}
    try:
        rep["branch"] = subprocess.check_output(["git", "branch", "--show-current"], cwd=str(cwd), text=True).strip() or None
        rep["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(cwd), text=True).strip() or None
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(cwd), text=True)
        rep["dirty"] = bool(status.strip())
    except Exception as exc:  # noqa: BLE001
        rep["warning"] = f"git metadata unavailable: {exc}"
    return rep


def build_research_pipeline_manifest(*, root: str | Path, command_summary: list[str] | None = None) -> dict:
    root_path = Path(root).expanduser().resolve()
    artifact_entries: list[dict] = []
    existing_paths: list[str] = []
    missing_paths: list[str] = []

    expected = [
        root_path / "model_bridge" / "gate" / "research_gate_packet.json",
        root_path / "model_bridge" / "no_broker" / "no_broker_dry_run_packet.json",
        root_path / "model_bridge" / "summary" / "research_gate_summary.md",
    ]

    for p in expected:
        if p.exists():
            existing_paths.append(str(p))
        else:
            missing_paths.append(str(p))

    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root_path))
        if path.suffix.lower() in {".json", ".csv", ".md", ".jsonl"}:
            checksum = _sha256(path)
        else:
            checksum = None
        artifact_entries.append(
            {
                "relative_path": rel,
                "absolute_path": str(path),
                "size_bytes": int(path.stat().st_size),
                "sha256": checksum,
            }
        )

    phase_coverage = {
        "phase_041_055": True,
        "phase_056_065": True,
        "phase_066_075": True,
        "phase_076_085": True,
        "phase_086_095": True,
        "phase_096_105": True,
        "phase_106_115": True,
    }

    return {
        "schema_version": "v1",
        "created_at_utc": datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat(),
        "root": str(root_path),
        "phase_coverage": phase_coverage,
        "expected_artifact_paths": [str(p) for p in expected],
        "existing_artifact_paths": existing_paths,
        "missing_artifact_paths": missing_paths,
        "artifact_inventory": artifact_entries,
        "command_summary": command_summary or [],
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "working_directory": str(Path.cwd().resolve()),
        },
        "git": _git_summary(Path.cwd().resolve()),
    }
