from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from cajas.baseline.run_contract import build_phase12_baseline_run_contract


class RunContractTests(unittest.TestCase):
    def _write_cfg(self, tmp_dir: str) -> Path:
        cfg = {
            "name": "run_contract_test",
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
            "workflow_bridge": {
                "class": "cajas.workflows.prepared_workflow.PreparedWorkflow",
                "dry_run_only": True,
            },
            "training": {"enabled": False},
        }
        path = Path(tmp_dir) / "c.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return path

    def test_step_permissions_and_can_train(self) -> None:
        with TemporaryDirectory() as tmp:
            contract = build_phase12_baseline_run_contract(config_path=str(self._write_cfg(tmp)))
            self.assertFalse(contract.can_train)
            step_map = contract.step_map()
            self.assertTrue(step_map["load_config"])
            self.assertTrue(step_map["validate_config"])
            self.assertTrue(step_map["run_preflight"])
            self.assertTrue(step_map["build_dataset"])
            self.assertTrue(step_map["encode_labels"])
            self.assertTrue(step_map["write_artifacts"])
            self.assertFalse(step_map["build_model"])
            self.assertFalse(step_map["fit_model"])
            self.assertFalse(step_map["predict"])
            self.assertFalse(step_map["evaluate"])
            self.assertFalse(step_map["serialize_model"])

    def test_model_steps_not_executed_and_json(self) -> None:
        with TemporaryDirectory() as tmp:
            contract = build_phase12_baseline_run_contract(config_path=str(self._write_cfg(tmp)))
            for step in contract.steps:
                if step.name in {"build_model", "fit_model", "predict", "evaluate", "serialize_model"}:
                    self.assertFalse(step.executed)
            payload = contract.to_dict()
            self.assertIn("Training disabled by Phase 12 policy.", payload["blockers"])
            json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
