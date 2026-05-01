from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.qlib_compat.adapter_comparison_probe import run_adapter_comparison_probe


class AdapterComparisonProbeTests(unittest.TestCase):
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

    def _write_cfg(self, tmp_dir: str, csv_path: Path, label_col: str = "future_direction_8") -> Path:
        cfg = {
            "name": "phase16_adapter_probe_test",
            "data_adapter": {
                "csv_path": str(csv_path),
                "label_col": label_col,
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

    def test_probe_compatible(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            report = run_adapter_comparison_probe(config_path=str(cfg))
            self.assertTrue(report.compatible)
            self.assertFalse(report.training_executed)
            self.assertTrue(len(report.segments) == 3)

    def test_probe_serialization_and_warning(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            payload = run_adapter_comparison_probe(config_path=str(cfg)).to_dict()
            self.assertIn("segments", payload)
            self.assertIn("warnings", payload)

    def test_mismatch_detection_via_bad_label_col(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir), label_col="missing_label")
            with self.assertRaisesRegex(ValueError, "Label column not found"):
                run_adapter_comparison_probe(config_path=str(cfg))


if __name__ == "__main__":
    unittest.main()
