from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.baseline.training_input_materialization import materialize_training_inputs_preview


class TrainingInputMaterializationTests(unittest.TestCase):
    def _write_dataset(self, tmp_dir: str) -> Path:
        rows = [
            {
                "datetime": "2025-01-10T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.11,
                "volume": 100,
                "feature_a": 0.1,
                "future_close_8": 1.15,
                "future_return_8": 0.01,
                "future_direction_8": "down",
            },
            {
                "datetime": "2025-09-10T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.3,
                "low": 1.15,
                "close": 1.22,
                "volume": 110,
                "feature_a": 0.2,
                "future_close_8": 1.25,
                "future_return_8": 0.02,
                "future_direction_8": "flat",
            },
            {
                "datetime": "2025-11-10T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.3,
                "high": 1.35,
                "low": 1.2,
                "close": 1.28,
                "volume": 120,
                "feature_a": 0.3,
                "future_close_8": 1.32,
                "future_return_8": 0.03,
                "future_direction_8": "up",
            },
        ]
        path = Path(tmp_dir) / "prepared.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_config(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "phase14_materialization_test",
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
        path = Path(tmp_dir) / "cfg.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return path

    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_writes_reports_and_csvs(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_dataset(tmp_dir)
            cfg = self._write_config(tmp_dir, csv)
            out = Path(tmp_dir) / "out"
            before = self._sha256(csv)
            report = materialize_training_inputs_preview(
                config_path=str(cfg),
                output_dir=out,
                run_name="r1",
                write_csv=True,
            )
            run_dir = out / "r1"
            self.assertTrue((run_dir / "training_input_materialization_report.json").exists())
            self.assertTrue((run_dir / "label_encoding_preview.json").exists())
            self.assertTrue((run_dir / "metric_plan.json").exists())
            self.assertTrue((run_dir / "train_features.csv").exists())
            self.assertTrue((run_dir / "valid_features.csv").exists())
            self.assertTrue((run_dir / "test_features.csv").exists())
            self.assertFalse(report.training_executed)
            self.assertFalse(report.model_built)
            self.assertEqual(before, self._sha256(csv))

    def test_no_csv_mode(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_dataset(tmp_dir)
            cfg = self._write_config(tmp_dir, csv)
            out = Path(tmp_dir) / "out"
            materialize_training_inputs_preview(
                config_path=str(cfg),
                output_dir=out,
                run_name="r2",
                write_csv=False,
            )
            run_dir = out / "r2"
            self.assertTrue((run_dir / "training_input_materialization_report.json").exists())
            self.assertFalse((run_dir / "train_features.csv").exists())

    def test_refuses_overwrite(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_dataset(tmp_dir)
            cfg = self._write_config(tmp_dir, csv)
            out = Path(tmp_dir) / "out"
            materialize_training_inputs_preview(
                config_path=str(cfg),
                output_dir=out,
                run_name="same",
                write_csv=False,
            )
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                materialize_training_inputs_preview(
                    config_path=str(cfg),
                    output_dir=out,
                    run_name="same",
                    write_csv=False,
                )

    def test_report_json_is_valid(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_dataset(tmp_dir)
            cfg = self._write_config(tmp_dir, csv)
            out = Path(tmp_dir) / "out"
            materialize_training_inputs_preview(
                config_path=str(cfg),
                output_dir=out,
                run_name="r3",
                write_csv=False,
            )
            payload = json.loads((out / "r3" / "training_input_materialization_report.json").read_text())
            self.assertEqual(payload["config_name"], "phase14_materialization_test")
            self.assertFalse(payload["training_executed"])
            self.assertFalse(payload["model_built"])


if __name__ == "__main__":
    unittest.main()
