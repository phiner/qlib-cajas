from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.qlib_compat.workflow_config_probe import (
    build_training_disabled_qlib_workflow_config,
    probe_qlib_workflow_config,
    validate_qlib_workflow_config_dict,
)


class QlibWorkflowConfigProbeTests(unittest.TestCase):
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
            "name": "phase17_workflow_probe_test",
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

    def test_workflow_config_build_and_probe(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            wf = build_training_disabled_qlib_workflow_config(config_path=str(cfg))
            self.assertFalse(wf["experiment"]["training_enabled"])
            self.assertGreater(wf["dataset"]["feature_count"], 0)

            report = probe_qlib_workflow_config(config_path=str(cfg))
            self.assertTrue(report.workflow_config_built)
            self.assertFalse(report.training_enabled)
            self.assertFalse(report.training_executed)
            self.assertFalse(report.qlib_initialized)
            self.assertFalse(report.qlib_workflow_executed)
            self.assertFalse(report.workflow_config["model"]["enabled"])
            self.assertFalse(report.workflow_config["model"]["constructed"])

    def test_report_serialization(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            payload = probe_qlib_workflow_config(config_path=str(cfg)).to_dict()
            json.dumps(payload)
            self.assertIn("workflow_config", payload)

    def test_missing_label_or_segments_produce_issues(self) -> None:
        broken = {
            "experiment": {"training_enabled": False, "training_executed": False},
            "dataset": {
                "class": "x",
                "label_col": "",
                "segments": {},
                "feature_count": 0,
                "leakage_columns": [],
            },
            "model": {"enabled": False, "constructed": False},
            "workflow": {"execute_workflow": False, "qlib_initialized": False},
        }
        issues = validate_qlib_workflow_config_dict(broken)
        codes = {i.code for i in issues}
        self.assertIn("label_missing", codes)
        self.assertIn("segments_missing", codes)
        self.assertIn("feature_count_invalid", codes)

    def test_artifact_writing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            cfg = self._write_cfg(tmp_dir, self._write_dataset(tmp_dir))
            payload = probe_qlib_workflow_config(config_path=str(cfg)).to_dict()
            out = write_baseline_reports(
                output_dir=tmp_dir,
                run_name="phase17",
                reports={
                    "qlib_workflow_config_probe_report": payload,
                    "qlib_workflow_config_draft": payload["workflow_config"],
                },
            )
            self.assertTrue(Path(out["qlib_workflow_config_probe_report"]).exists())
            self.assertTrue(Path(out["qlib_workflow_config_draft"]).exists())


if __name__ == "__main__":
    unittest.main()
