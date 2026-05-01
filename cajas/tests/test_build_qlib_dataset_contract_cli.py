from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildQlibDatasetContractCliTests(unittest.TestCase):
    def test_cli_outputs_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "input.csv"
            out = root / "contract.json"
            csv.write_text("instrument,datetime,close,future_direction_8\nEURUSD,2025-01-01 00:00:00,1.1,up\n", encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/build_qlib_dataset_contract.py",
                    "--input-csv",
                    str(csv),
                    "--out",
                    str(out),
                    "--dataset-id",
                    "d1",
                    "--label-col",
                    "future_direction_8",
                ],
                check=True,
            )
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
