from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_handler_input_builder import build_qlib_handler_input
from cajas.reports.qlib_handler_smoke_validator import validate_qlib_handler_input


class QlibHandlerSmokeValidatorTests(unittest.TestCase):
    def test_pass_case(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            csv.write_text(
                "instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n",
                encoding="utf-8",
            )
            out = root / "pkg"
            build_qlib_handler_input(input_csv=csv, out_dir=out, label_columns=["future_direction_8"])
            rep = validate_qlib_handler_input(handler_dir=out)
            self.assertIn(rep["status"], {"pass", "pass_with_warnings"})

    def test_fail_case_missing_files(self) -> None:
        with TemporaryDirectory() as tmp:
            rep = validate_qlib_handler_input(handler_dir=tmp)
            self.assertEqual(rep["status"], "fail")


if __name__ == "__main__":
    unittest.main()
