from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.reports.qlib_handler_input_builder import build_qlib_handler_input


class QlibHandlerInputBuilderTests(unittest.TestCase):
    def test_preserves_rows_and_required_columns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            csv.write_text(
                "instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\nEURUSD,2025-01-01 00:15:00,1.2,down\n",
                encoding="utf-8",
            )
            out = root / "out"
            manifest = build_qlib_handler_input(input_csv=csv, out_dir=out, label_columns=["future_direction_8"])
            df = pd.read_csv(out / "handler_input.csv")
            self.assertEqual(len(df), 2)
            self.assertEqual(manifest["row_count"], 2)

    def test_reports_missing_required_columns(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            csv.write_text("instrument,datetime,close\nEURUSD,2025-01-01 00:00:00,1.1\n", encoding="utf-8")
            out = root / "out"
            manifest = build_qlib_handler_input(input_csv=csv, out_dir=out, label_columns=["future_direction_8"])
            self.assertEqual(manifest["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
