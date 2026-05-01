from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_model_training_contract_builder import build_qlib_model_training_contract


class QlibModelTrainingContractBuilderTests(unittest.TestCase):
    def test_builder(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "handler_input.csv").write_text(
                "instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n",
                encoding="utf-8",
            )
            (d / "handler_input_manifest.json").write_text(json.dumps({"status": "ready_for_handler_smoke"}), encoding="utf-8")
            (d / "dataset_contract.json").write_text(
                json.dumps({"instrument_col": "instrument", "datetime_col": "datetime", "label_columns": ["future_direction_8"]}),
                encoding="utf-8",
            )
            (d / "handler_smoke_report.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            c = build_qlib_model_training_contract(
                handler_input_path=d / "handler_input.csv",
                handler_manifest_path=d / "handler_input_manifest.json",
                dataset_contract_path=d / "dataset_contract.json",
                handler_smoke_report_path=d / "handler_smoke_report.json",
            )
            self.assertIn(c["readiness_status"], {"ready_for_training_smoke", "ready_with_warnings"})


if __name__ == "__main__":
    unittest.main()
