from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.scripts.run_experiment_plan_dry_run import run_experiment_plan


def _config_yaml(csv_path: str, training_enabled: bool = False) -> str:
    return textwrap.dedent(
        f"""
        name: test_plan
        data_adapter:
          csv_path: {csv_path}
          label_col: future_direction_8
          handler_class: cajas.handlers.prepared_csv_handler.PreparedCsvHandler
          dataset_class: cajas.datasets.prepared_dataset.PreparedDataset
          leakage_columns:
            - future_close_8
            - future_return_8
          segments:
            train: {{start: "2025-01-01", end: "2025-08-31"}}
            valid: {{start: "2025-09-01", end: "2025-10-31"}}
            test: {{start: "2025-11-01", end: "2025-12-31"}}
        workflow_bridge:
          class: cajas.workflows.prepared_workflow.PreparedWorkflow
          dry_run_only: true
        training:
          enabled: {str(training_enabled).lower()}
        """
    ).strip() + "\n"


class ExperimentPlanDryRunTests(unittest.TestCase):
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
                "datetime": "2025-09-15T00:00:00Z",
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
                "datetime": "2025-11-15T00:00:00Z",
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
        csv_path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        return csv_path

    def test_plan_dry_run_shapes_match(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_csv(tmp_dir)
            cfg_path = Path(tmp_dir) / "c.yaml"
            cfg_path.write_text(_config_yaml(str(csv_path)), encoding="utf-8")
            payload, issues = run_experiment_plan(str(cfg_path))
            self.assertFalse(issues)
            self.assertEqual(payload["training_executed"], False)
            self.assertEqual(len(payload["segment_shapes"]), 3)
            for s in payload["segment_shapes"]:
                self.assertEqual(s["feature_rows"], s["label_rows"])

    def test_json_ready_payload(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_csv(tmp_dir)
            cfg_path = Path(tmp_dir) / "c.yaml"
            cfg_path.write_text(_config_yaml(str(csv_path)), encoding="utf-8")
            payload, _ = run_experiment_plan(str(cfg_path))
            self.assertIn("segment_shapes", payload)
            self.assertIn("feature_count", payload)

    def test_training_enabled_fails(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = self._write_csv(tmp_dir)
            cfg_path = Path(tmp_dir) / "c.yaml"
            cfg_path.write_text(
                _config_yaml(str(csv_path), training_enabled=True), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "training.enabled"):
                run_experiment_plan(str(cfg_path))


if __name__ == "__main__":
    unittest.main()
