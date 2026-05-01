from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.scripts.run_experiment_plan_dry_run import run_experiment_plan


class ExperimentPlanArtifactTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str) -> Path:
        rows = [
            {
                "datetime": "2025-01-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 100,
                "return_1": 0.001,
                "future_close_8": 1.16,
                "future_return_8": 0.01,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-10-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.15,
                "high": 1.22,
                "low": 1.12,
                "close": 1.2,
                "volume": 120,
                "return_1": -0.001,
                "future_close_8": 1.18,
                "future_return_8": -0.01,
                "future_direction_8": "down",
            },
            {
                "datetime": "2025-12-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.25,
                "low": 1.18,
                "close": 1.24,
                "volume": 125,
                "return_1": 0.002,
                "future_close_8": 1.26,
                "future_return_8": 0.005,
                "future_direction_8": "flat",
            },
        ]
        path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "artifact_test",
            "data_adapter": {
                "csv_path": str(csv_path),
                "label_col": "future_direction_8",
                "handler_class": "cajas.handlers.prepared_csv_handler.PreparedCsvHandler",
                "dataset_class": "cajas.datasets.prepared_dataset.PreparedDataset",
                "leakage_columns": ["future_close_8", "future_return_8"],
                "segments": {
                    "train": {"start": "2025-01-01", "end": "2025-08-31"},
                    "valid": {"start": "2025-09-01", "end": "2025-10-31"},
                    "test": {"start": "2025-11-01", "end": "2025-12-31"},
                },
            },
            "workflow_bridge": {
                "class": "cajas.workflows.prepared_workflow.PreparedWorkflow",
                "dry_run_only": True,
            },
            "training": {"enabled": False},
        }
        cfg_path = Path(tmp_dir) / "c.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return cfg_path

    def test_artifacts_written_and_content(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_csv(tmp_dir)
            cfg_path = self._write_cfg(tmp_dir, csv_path)
            payload, _ = run_experiment_plan(
                config_path=str(cfg_path),
                write_artifacts=True,
                output_dir=tmp_dir,
                run_name="run1",
            )
            self.assertTrue(payload["artifacts_written"])
            run_dir = Path(payload["artifact_paths"]["run_dir"])
            files = sorted(p.name for p in run_dir.glob("*.json"))
            self.assertEqual(
                files,
                [
                    "config_snapshot.json",
                    "run_manifest.json",
                    "validation_report.json",
                    "workflow_summary.json",
                ],
            )
            manifest = json.loads((run_dir / "run_manifest.json").read_text("utf-8"))
            self.assertFalse(manifest["training_executed"])
            summary = json.loads((run_dir / "workflow_summary.json").read_text("utf-8"))
            self.assertTrue(summary["segment_shapes"])
            report = json.loads((run_dir / "validation_report.json").read_text("utf-8"))
            self.assertFalse(report["leakage_columns_found_in_features"])

    def test_existing_run_name_fails(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_csv(tmp_dir)
            cfg_path = self._write_cfg(tmp_dir, csv_path)
            run_experiment_plan(
                config_path=str(cfg_path),
                write_artifacts=True,
                output_dir=tmp_dir,
                run_name="run1",
            )
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                run_experiment_plan(
                    config_path=str(cfg_path),
                    write_artifacts=True,
                    output_dir=tmp_dir,
                    run_name="run1",
                )


if __name__ == "__main__":
    unittest.main()
