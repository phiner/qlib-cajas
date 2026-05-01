from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.baseline.local_baseline_trainer import train_local_baseline


class LocalBaselineTrainerTests(unittest.TestCase):
    def _write_dataset(self, tmp_dir: str) -> Path:
        rows: list[dict] = []
        def add_row(ts: str, label: str, i: int) -> None:
            base = 1.1 + i * 0.0001
            rows.append(
                {
                    "datetime": ts,
                    "symbol": "EURUSD",
                    "timeframe": "15m",
                    "open": base,
                    "high": base + 0.001,
                    "low": base - 0.001,
                    "close": base + 0.0002,
                    "volume": 100 + i,
                    "f1": float(i % 5),
                    "f2": float((i * 2) % 7),
                    "future_close_8": base + 0.0008,
                    "future_return_8": 0.001,
                    "future_direction_8": label,
                }
            )

        labels = ["down", "flat", "up"]
        for i in range(18):
            month = 1 if i < 9 else 2
            add_row(f"2025-{month:02d}-{(i%9)+1:02d}T00:00:00Z", labels[i % 3], i)
        for i in range(18, 30):
            add_row(f"2025-09-{(i-17):02d}T00:00:00Z", labels[i % 3], i)
        for i in range(30, 42):
            add_row(f"2025-11-{(i-29):02d}T00:00:00Z", labels[i % 3], i)

        path = Path(tmp_dir) / "prepared.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "phase20_local_baseline_test",
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

    def test_training_writes_artifacts_and_registry(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_dataset(tmp_dir)
            cfg = self._write_cfg(tmp_dir, csv_path)
            output_dir = Path(tmp_dir) / "runs"

            report = train_local_baseline(
                config_path=str(cfg),
                output_dir=output_dir,
                run_name="phase20_test",
                model_family="sklearn_random_forest",
                random_state=7,
            )
            self.assertTrue(report.training_executed)
            self.assertTrue(report.model_artifact_created)
            self.assertTrue(report.prediction_artifacts_created)
            self.assertTrue(report.metrics_artifacts_created)
            self.assertFalse(report.qlib_workflow_executed)
            self.assertFalse(report.trading_backtest_profit_outputs)
            self.assertIn("predictions_valid.csv", report.artifact_files)
            self.assertIn("metrics_valid.json", report.artifact_files)
            self.assertIn("feature_value_audit_train.json", report.artifact_files)
            self.assertIn("numeric_sanitization_train.json", report.artifact_files)
            self.assertIn("sanitation_summary", report.to_dict())

            registry_path = Path(report.run_registry_path)
            self.assertTrue(registry_path.exists())
            self.assertIn("tmp/cajas/run_registry", str(registry_path))

    def test_refuses_overwrite(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_dataset(tmp_dir)
            cfg = self._write_cfg(tmp_dir, csv_path)
            output_dir = Path(tmp_dir) / "runs"
            train_local_baseline(
                config_path=str(cfg),
                output_dir=output_dir,
                run_name="phase20_test",
                model_family="sklearn_random_forest",
            )
            with self.assertRaises(FileExistsError):
                train_local_baseline(
                    config_path=str(cfg),
                    output_dir=output_dir,
                    run_name="phase20_test",
                    model_family="sklearn_random_forest",
                )

    def test_training_succeeds_with_inf_values_after_sanitation(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_dataset(tmp_dir)
            df = pd.read_csv(csv_path)
            df.loc[0, "f1"] = float("inf")
            df.loc[1, "f2"] = float("-inf")
            df.to_csv(csv_path, index=False)
            cfg = self._write_cfg(tmp_dir, csv_path)
            output_dir = Path(tmp_dir) / "runs"
            report = train_local_baseline(
                config_path=str(cfg),
                output_dir=output_dir,
                run_name="phase20_inf_test",
                model_family="RandomForest",
            )
            self.assertTrue(report.training_executed)


if __name__ == "__main__":
    unittest.main()
