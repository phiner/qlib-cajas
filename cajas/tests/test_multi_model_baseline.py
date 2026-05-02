from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest
import yaml

from cajas.baseline.multi_model_baseline import run_multi_model_baseline

pytestmark = [pytest.mark.integration]


class MultiModelBaselineTests(unittest.TestCase):
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
            add_row(f"2025-{month:02d}-{(i % 9) + 1:02d}T00:00:00Z", labels[i % 3], i)
        for i in range(18, 30):
            add_row(f"2025-09-{(i - 17):02d}T00:00:00Z", labels[i % 3], i)
        for i in range(30, 42):
            add_row(f"2025-11-{(i - 29):02d}T00:00:00Z", labels[i % 3], i)

        path = Path(tmp_dir) / "prepared.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "phase20_multi_model_test",
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

    def test_runs_sklearn_models(self) -> None:
        with TemporaryDirectory() as tmp:
            data = self._write_dataset(tmp)
            cfg = self._write_cfg(tmp, data)
            rep = run_multi_model_baseline(
                config_path=str(cfg),
                output_dir=tmp,
                run_name="multi",
                model_families=["RandomForest", "HistGradientBoosting"],
                input_override=str(data),
                random_state=2,
            )
            self.assertGreaterEqual(len(rep.model_runs), 1)
            self.assertFalse(rep.trading_metrics_present)
            self.assertTrue((Path(rep.output_dir) / "model_run_status.csv").exists())


if __name__ == "__main__":
    unittest.main()
