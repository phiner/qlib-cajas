"""Write reproducible local artifacts for experiment plan dry-runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class DryRunArtifactPaths:
    run_dir: Path
    manifest_path: Path
    config_snapshot_path: Path
    workflow_summary_path: Path
    validation_report_path: Path


class DryRunRecorder:
    def __init__(self, output_dir: str | Path, run_name: str | None = None) -> None:
        base_dir = Path(output_dir)
        actual_run_name = run_name or datetime.now().strftime("dry_run_%Y%m%d_%H%M%S")
        run_dir = base_dir / actual_run_name
        if run_dir.exists():
            raise FileExistsError(f"Run directory already exists: {run_dir}")
        run_dir.mkdir(parents=True, exist_ok=False)

        self._paths = DryRunArtifactPaths(
            run_dir=run_dir,
            manifest_path=run_dir / "run_manifest.json",
            config_snapshot_path=run_dir / "config_snapshot.json",
            workflow_summary_path=run_dir / "workflow_summary.json",
            validation_report_path=run_dir / "validation_report.json",
        )

    @property
    def paths(self) -> DryRunArtifactPaths:
        return self._paths

    def _write_json(self, path: Path, data: Mapping[str, Any]) -> Path:
        path.write_text(
            json.dumps(dict(data), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def write_manifest(self, manifest: Mapping[str, Any]) -> Path:
        return self._write_json(self.paths.manifest_path, manifest)

    def write_config_snapshot(self, config_data: Mapping[str, Any]) -> Path:
        return self._write_json(self.paths.config_snapshot_path, config_data)

    def write_workflow_summary(self, summary_data: Mapping[str, Any]) -> Path:
        return self._write_json(self.paths.workflow_summary_path, summary_data)

    def write_validation_report(self, report_data: Mapping[str, Any]) -> Path:
        return self._write_json(self.paths.validation_report_path, report_data)

    def write_all(
        self,
        manifest: Mapping[str, Any],
        config_snapshot: Mapping[str, Any],
        workflow_summary: Mapping[str, Any],
        validation_report: Mapping[str, Any],
    ) -> DryRunArtifactPaths:
        self.write_manifest(manifest)
        self.write_config_snapshot(config_snapshot)
        self.write_workflow_summary(workflow_summary)
        self.write_validation_report(validation_report)
        return self.paths
