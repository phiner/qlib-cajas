from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.train_qlib_model_bridge_baseline import main


class TrainQlibModelBridgeBaselineCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            csv = d / "handler.csv"
            csv.write_text(
                "instrument,datetime,close,volume,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.1,100,up\n"
                "EURUSD,2025-01-01 00:15:00,1.2,101,down\n"
                "EURUSD,2025-01-01 00:30:00,1.3,102,up\n"
                "EURUSD,2025-01-01 00:45:00,1.4,103,down\n"
                "EURUSD,2025-01-01 01:00:00,1.5,104,up\n"
                "EURUSD,2025-01-01 01:15:00,1.6,105,down\n",
                encoding="utf-8",
            )
            contract = d / "contract.json"
            contract.write_text(json.dumps({
                "run_id": "r1",
                "readiness_status": "ready_for_training_smoke",
                "handler_input_path": str(csv),
                "datetime_col": "datetime",
                "label_col": "future_direction_8",
                "feature_columns": ["close", "volume"],
                "split_ratios": {"train": 0.5, "valid": 0.25, "test": 0.25},
            }), encoding="utf-8")
            out = d / "exp"
            code = main([
                "--training-contract", str(contract), "--out-dir", str(out), "--seed", "42", "--max-rows", "100"
            ])
            self.assertEqual(code, 0)
            self.assertTrue((out / "metrics.json").exists())


if __name__ == "__main__":
    unittest.main()
