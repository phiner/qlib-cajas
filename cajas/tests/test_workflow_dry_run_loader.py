from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.qlib_compat.workflow_dry_run_loader import run_qlib_workflow_dry_run_loader


class WorkflowDryRunLoaderTests(unittest.TestCase):
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

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "phase18_workflow_dry_run_loader_test",
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

    def test_valid_config_produces_report(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            report = run_qlib_workflow_dry_run_loader(config_path=str(cfg))
            self.assertTrue(report.workflow_config_built)
            self.assertFalse(report.training_enabled)
            self.assertFalse(report.training_executed)
            self.assertFalse(report.model_enabled)
            self.assertFalse(report.model_constructed)
            self.assertFalse(report.qlib_initialized)
            self.assertFalse(report.qlib_workflow_executed)
            self.assertTrue(report.dataset_adapter_resolved)
            self.assertTrue(report.workflow_bridge_resolved)

    def test_class_resolution_includes_dataset_adapter(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            payload = run_qlib_workflow_dry_run_loader(config_path=str(cfg)).to_dict()
            dotted_paths = {item["dotted_path"] for item in payload["class_resolution"]["results"]}
            self.assertIn(
                "cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter",
                dotted_paths,
            )

    def test_json_serialization(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            payload = run_qlib_workflow_dry_run_loader(config_path=str(cfg)).to_dict()
            json.dumps(payload)

    def test_artifact_writing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            payload = run_qlib_workflow_dry_run_loader(config_path=str(cfg)).to_dict()
            out = write_baseline_reports(
                output_dir=tmp_dir,
                run_name="phase18",
                reports={
                    "qlib_workflow_dry_run_loader_report": payload,
                    "class_resolution_report": payload["class_resolution"],
                    "qlib_workflow_config_draft": payload["workflow_config"],
                },
            )
            self.assertTrue(Path(out["qlib_workflow_dry_run_loader_report"]).exists())
            self.assertTrue(Path(out["class_resolution_report"]).exists())
            self.assertTrue(Path(out["qlib_workflow_config_draft"]).exists())


if __name__ == "__main__":
    unittest.main()
