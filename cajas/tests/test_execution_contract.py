from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from cajas.baseline.execution_contract import build_phase11_execution_contract


class ExecutionContractTests(unittest.TestCase):
    def _write_cfg(self, tmp_dir: str) -> Path:
        cfg = {
            "name": "contract_test",
            "data_adapter": {
                "csv_path": "tmp/demo.csv",
                "label_col": "future_direction_8",
                "leakage_columns": ["future_close_8", "future_return_8"],
                "segments": {
                    "train": {"start": "2025-01-01", "end": "2025-01-31"},
                    "valid": {"start": "2025-02-01", "end": "2025-02-28"},
                    "test": {"start": "2025-03-01", "end": "2025-03-31"},
                },
            },
            "workflow_bridge": {"class": "cajas.workflows.prepared_workflow.PreparedWorkflow", "dry_run_only": True},
            "training": {"enabled": False},
        }
        path = Path(tmp_dir) / "c.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return path

    def test_allowed_and_forbidden_permissions(self) -> None:
        with TemporaryDirectory() as tmp:
            c = build_phase11_execution_contract(config_path=str(self._write_cfg(tmp)))
            p = c.permission_map()
            self.assertTrue(p["build_plan"])
            self.assertFalse(p["fit_model"])
            self.assertFalse(p["trade"])

    def test_required_items_and_permission_map(self) -> None:
        with TemporaryDirectory() as tmp:
            c = build_phase11_execution_contract(config_path=str(self._write_cfg(tmp)))
            self.assertIn("explicit future phase approval", c.required_before_training)
            self.assertIn("load_config", c.permission_map())


if __name__ == "__main__":
    unittest.main()
