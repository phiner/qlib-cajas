from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.scripts.build_baseline_scaffold import run_baseline_scaffold


class BaselineScaffoldTests(unittest.TestCase):
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
                "f1": 0.1,
                "future_close_8": 1.2,
                "future_return_8": 0.01,
                "future_direction_8": "down",
            },
            {
                "datetime": "2025-09-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.3,
                "low": 1.1,
                "close": 1.22,
                "volume": 110,
                "f1": 0.2,
                "future_close_8": 1.25,
                "future_return_8": 0.02,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-11-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.3,
                "high": 1.31,
                "low": 1.2,
                "close": 1.23,
                "volume": 120,
                "f1": 0.3,
                "future_close_8": 1.27,
                "future_return_8": 0.03,
                "future_direction_8": "flat",
            },
        ]
        path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "baseline_scaffold_test",
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
        p = Path(tmp_dir) / "c.yaml"
        p.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return p

    def test_scaffold_training_disabled_and_json(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_csv(tmp_dir))
            payload = run_baseline_scaffold(config_path=str(cfg))
            self.assertFalse(payload["training_executed"])
            self.assertFalse(payload["training_allowed"])
            self.assertIn("Training remains disabled by Phase 10 policy.", payload["blockers"])
            self.assertIn("dataset_spec", payload)
            self.assertEqual(payload["label_encoding_plan"]["flat"], 1)
            json.dumps(payload)

    def test_scaffold_artifact_written(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_csv(tmp_dir))
            payload = run_baseline_scaffold(
                config_path=str(cfg),
                write_artifacts=True,
                output_dir=tmp_dir,
                run_name="scaf1",
            )
            self.assertTrue(payload["artifacts_written"])
            out = Path(payload["artifact_paths"]["baseline_scaffold_report"])
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
