from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_qlib_model_training_contract import main


class BuildQlibModelTrainingContractCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "handler_input.csv").write_text("instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n", encoding="utf-8")
            (d / "handler_input_manifest.json").write_text(json.dumps({"status": "ready_for_handler_smoke"}), encoding="utf-8")
            (d / "dataset_contract.json").write_text(json.dumps({"instrument_col": "instrument", "datetime_col": "datetime", "label_columns": ["future_direction_8"]}), encoding="utf-8")
            (d / "handler_smoke_report.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            out = d / "contract.json"
            code = main([
                "--handler-input", str(d / "handler_input.csv"),
                "--handler-manifest", str(d / "handler_input_manifest.json"),
                "--dataset-contract", str(d / "dataset_contract.json"),
                "--handler-smoke-report", str(d / "handler_smoke_report.json"),
                "--out", str(out),
            ])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
