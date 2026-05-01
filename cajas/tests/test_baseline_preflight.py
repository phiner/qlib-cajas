from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import yaml

from cajas.scripts.run_baseline_preflight import run_preflight


class BaselinePreflightTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str) -> Path:
        rows = [
            {"datetime": "2025-01-01T00:00:00Z", "symbol": "EURUSD", "timeframe": "15m", "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.1, "volume": 100, "f1": 0.1, "future_close_8": 1.2, "future_return_8": 0.1, "future_direction_8": "down"},
            {"datetime": "2025-09-01T00:00:00Z", "symbol": "EURUSD", "timeframe": "15m", "open": 1.2, "high": 1.3, "low": 1.1, "close": 1.2, "volume": 120, "f1": 0.2, "future_close_8": 1.3, "future_return_8": 0.2, "future_direction_8": "up"},
            {"datetime": "2025-11-01T00:00:00Z", "symbol": "EURUSD", "timeframe": "15m", "open": 1.3, "high": 1.4, "low": 1.2, "close": 1.3, "volume": 130, "f1": 0.3, "future_close_8": 1.4, "future_return_8": 0.3, "future_direction_8": "flat"},
        ]
        path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _write_cfg(self, tmp_dir: str, csv_path: Path) -> Path:
        cfg = {
            "name": "preflight_test",
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
            "workflow_bridge": {"class": "cajas.workflows.prepared_workflow.PreparedWorkflow", "dry_run_only": True},
            "training": {"enabled": False},
        }
        path = Path(tmp_dir) / "c.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return path

    def test_phase11_training_disabled(self) -> None:
        with TemporaryDirectory() as tmp:
            p = run_preflight(config_path=str(self._write_cfg(tmp, self._write_csv(tmp))), root=tmp)
            self.assertFalse(p["can_train_now"])
            self.assertFalse(p["training_executed"])

    def test_path_hygiene_blocker(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir()
            (root / "tasks" / "x.md").write_text("python caixas/scripts/bad.py\n", encoding="utf-8")
            p = run_preflight(config_path=str(self._write_cfg(tmp, self._write_csv(tmp))), root=tmp)
            self.assertIn("Path hygiene check failed.", p["blockers"])

    def test_artifact_and_json(self) -> None:
        with TemporaryDirectory() as tmp:
            p = run_preflight(
                config_path=str(self._write_cfg(tmp, self._write_csv(tmp))),
                root=tmp,
                write_artifacts=True,
                output_dir=tmp,
                run_name="pf1",
            )
            self.assertTrue(p["artifacts_written"])
            self.assertTrue(Path(p["artifact_paths"]["baseline_preflight_report"]).exists())
            self.assertTrue(Path(p["artifact_paths"]["baseline_execution_contract"]).exists())
            json.dumps(p)


if __name__ == "__main__":
    unittest.main()
