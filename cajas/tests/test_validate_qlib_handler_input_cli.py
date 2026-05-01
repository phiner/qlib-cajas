from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class ValidateQlibHandlerInputCliTests(unittest.TestCase):
    def test_cli_outputs_validation_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            pkg = root / "pkg"
            rep = root / "report.json"
            csv.write_text("instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n", encoding="utf-8")
            subprocess.run(
                [sys.executable, "cajas/scripts/build_qlib_handler_input.py", "--input-csv", str(csv), "--out-dir", str(pkg), "--label-col", "future_direction_8"],
                check=True,
            )
            subprocess.run(
                [sys.executable, "cajas/scripts/validate_qlib_handler_input.py", "--handler-dir", str(pkg), "--out", str(rep)],
                check=True,
            )
            self.assertTrue(rep.exists())


if __name__ == "__main__":
    unittest.main()
