from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from cajas.config.experiment_config import (
    assert_training_disabled,
    build_workflow_config,
    load_experiment_config,
    validate_experiment_config,
)


def _base_yaml(training_enabled: bool = False, leakage: bool = True) -> str:
    payload = {
        "name": "test_cfg",
        "data_adapter": {
            "csv_path": "tmp/demo.csv",
            "label_col": "future_direction_8",
            "handler_class": "cajas.handlers.prepared_csv_handler.PreparedCsvHandler",
            "dataset_class": "cajas.datasets.prepared_dataset.PreparedDataset",
            "leakage_columns": (
                ["future_close_8", "future_return_8"] if leakage else []
            ),
            "segments": {
                "train": {"start": "2025-01-01", "end": "2025-01-31"},
                "valid": {"start": "2025-02-01", "end": "2025-02-28"},
                "test": {"start": "2025-03-01", "end": "2025-03-31"},
            },
        },
        "workflow_bridge": {
            "class": "cajas.workflows.prepared_workflow.PreparedWorkflow",
            "dry_run_only": True,
        },
        "training": {"enabled": training_enabled},
    }
    return yaml.safe_dump(payload, sort_keys=False)


class ExperimentConfigTests(unittest.TestCase):
    def test_load_valid_config(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "c.yaml"
            path.write_text(_base_yaml(), encoding="utf-8")
            cfg = load_experiment_config(path)
            self.assertEqual(cfg.name, "test_cfg")
            self.assertIn("train", cfg.data_adapter.segments)

    def test_missing_label_fails(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            payload = yaml.safe_load(_base_yaml())
            del payload["data_adapter"]["label_col"]
            path = Path(tmp_dir) / "c.yaml"
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "label_col"):
                load_experiment_config(path)

    def test_training_enabled_assert_fails(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "c.yaml"
            path.write_text(_base_yaml(training_enabled=True), encoding="utf-8")
            cfg = load_experiment_config(path)
            with self.assertRaisesRegex(ValueError, "training.enabled"):
                assert_training_disabled(cfg)

    def test_missing_leakage_reports_issue(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "c.yaml"
            path.write_text(_base_yaml(leakage=False), encoding="utf-8")
            cfg = load_experiment_config(path)
            issues = validate_experiment_config(cfg)
            self.assertIn("leakage_columns is empty", issues)

    def test_build_workflow_config_override(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "c.yaml"
            path.write_text(_base_yaml(), encoding="utf-8")
            cfg = load_experiment_config(path)
            wf = build_workflow_config(cfg, csv_path_override="override.csv")
            self.assertEqual(wf.csv_path, "override.csv")


if __name__ == "__main__":
    unittest.main()
