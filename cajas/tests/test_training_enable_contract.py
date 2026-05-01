from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.baseline.training_enable_contract import (
    build_phase13_training_enable_contract,
)


class TrainingEnableContractTests(unittest.TestCase):
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
                "f1": 0.1,
                "future_close_8": 1.2,
                "future_return_8": 0.01,
                "future_direction_8": "down",
            },
            {
                "datetime": "2025-09-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.3,
                "low": 1.1,
                "close": 1.22,
                "volume": 110,
                "f1": 0.2,
                "future_close_8": 1.25,
                "future_return_8": 0.02,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-11-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.3,
                "high": 1.31,
                "low": 1.2,
                "close": 1.23,
                "volume": 120,
                "f1": 0.3,
                "future_close_8": 1.27,
                "future_return_8": 0.03,
                "future_direction_8": "flat",
            },
        ]
        path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "phase13_enable_contract_test",
            "data_adapter": {
                "csv_path": str(csv_path),
                "label_col": "future_direction_8",
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
        path = Path(tmp_dir) / "c.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return path

    def test_phase13_defaults_block_training_enable(self) -> None:
        with TemporaryDirectory() as tmp:
            contract = build_phase13_training_enable_contract(
                config_path=str(self._write_cfg(tmp, self._write_csv(tmp)))
            )
            self.assertFalse(contract.can_enable_training)
            gate_map = contract.gate_map()
            self.assertFalse(gate_map["user_training_approval"])
            self.assertFalse(gate_map["phase_policy_allows_training"])
            self.assertFalse(gate_map["config_training_enabled"])
            self.assertFalse(gate_map["training_guard_allows_training"])
            self.assertTrue(gate_map["label_encoding_plan_present"])
            self.assertIn("Training disabled by Phase 13 policy.", contract.blockers)
            self.assertIn("Training disabled because user approval was not granted.", contract.blockers)

    def test_gate_map_and_json(self) -> None:
        with TemporaryDirectory() as tmp:
            contract = build_phase13_training_enable_contract(
                config_path=str(self._write_cfg(tmp, self._write_csv(tmp)))
            )
            self.assertIn("no_feature_leakage", contract.gate_map())
            json.dumps(contract.to_dict())


if __name__ == "__main__":
    unittest.main()
