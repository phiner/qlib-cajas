from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.baseline.qlib_model_bridge_trainer import train_qlib_model_bridge_baseline


class QlibModelBridgeTrainerTests(unittest.TestCase):
    def test_train_smoke(self) -> None:
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
            contract = {
                "readiness_status": "ready_for_training_smoke",
                "handler_input_path": str(csv),
                "datetime_col": "datetime",
                "label_col": "future_direction_8",
                "feature_columns": ["close", "volume"],
                "split_ratios": {"train": 0.5, "valid": 0.25, "test": 0.25},
            }
            rep = train_qlib_model_bridge_baseline(contract=contract, out_dir=d / "exp", seed=42, max_rows=100)
            self.assertIn("metrics_valid", rep)
            self.assertIn("loading_decision", rep)


if __name__ == "__main__":
    unittest.main()
