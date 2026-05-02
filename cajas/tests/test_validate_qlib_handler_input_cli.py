from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from cajas.reports.qlib_handler_input_builder import build_qlib_handler_input
from cajas.scripts import validate_qlib_handler_input as validate_cli


class ValidateQlibHandlerInputCliTests(unittest.TestCase):
    def test_cli_outputs_validation_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            pkg = root / "pkg"
            rep = root / "report.json"
            csv.write_text("instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n", encoding="utf-8")
            build_qlib_handler_input(input_csv=str(csv), out_dir=str(pkg), label_columns=["future_direction_8"])
            argv = [
                "validate_qlib_handler_input.py",
                "--handler-dir",
                str(pkg),
                "--out",
                str(rep),
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = validate_cli.main()
            self.assertEqual(rc, 0)
            self.assertTrue(rep.exists())


if __name__ == "__main__":
    unittest.main()
