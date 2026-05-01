from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_dataset_contract_builder import build_qlib_dataset_contract


class QlibDatasetContractBuilderTests(unittest.TestCase):
    def test_builder_on_fixture(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            csv.write_text(
                "instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n",
                encoding="utf-8",
            )
            contract = build_qlib_dataset_contract(
                input_csv=csv,
                out_path=None,
                dataset_id="ds1",
                label_columns=["future_direction_8"],
            )
            self.assertEqual(contract["row_count"], 1)
            self.assertIn("close", contract["feature_columns"])


if __name__ == "__main__":
    unittest.main()
