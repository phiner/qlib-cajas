from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.readiness.baseline_readiness import run_baseline_readiness_check


class BaselineReadinessTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str, *, with_leakage: bool = False) -> Path:
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
                "datetime": "2025-09-15T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.3,
                "low": 1.1,
                "close": 1.25,
                "volume": 120,
                "f1": 0.2,
                "future_close_8": 1.3,
                "future_return_8": -0.01,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-11-15T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.25,
                "high": 1.35,
                "low": 1.2,
                "close": 1.3,
                "volume": 130,
                "f1": 0.3,
                "future_close_8": 1.31,
                "future_return_8": 0.0,
                "future_direction_8": "flat",
            },
        ]
        if with_leakage:
            for r in rows:
                r["future_return_8"] = r["future_return_8"]
        path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path, *, training_enabled: bool = False) -> Path:
        cfg = {
            "name": "readiness_test",
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
            "training": {"enabled": training_enabled},
        }
        p = Path(tmp_dir) / "c.yaml"
        p.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return p

    def test_valid_config_ready(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_csv(tmp_dir)
            cfg = self._write_cfg(tmp_dir, csv)
            report = run_baseline_readiness_check(config_path=str(cfg))
            self.assertTrue(report.ready)
            self.assertFalse(report.training_enabled)

    def test_training_enabled_fails(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_csv(tmp_dir)
            cfg = self._write_cfg(tmp_dir, csv, training_enabled=True)
            with self.assertRaisesRegex(ValueError, "training.enabled"):
                run_baseline_readiness_check(config_path=str(cfg))

    def test_strict_mode_not_ready_on_warnings(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv = self._write_csv(tmp_dir)
            cfg = self._write_cfg(tmp_dir, csv)
            report = run_baseline_readiness_check(config_path=str(cfg), strict=True)
            self.assertFalse(report.ready)


if __name__ == "__main__":
    unittest.main()
