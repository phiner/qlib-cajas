from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class ValidationDataGuardrailsTests(unittest.TestCase):
    def test_fast_validation_mentions_real_data_flag(self) -> None:
        txt = Path("cajas/scripts/run_fast_validation.py").read_text(encoding="utf-8")
        self.assertIn("--include-real-data", txt)
        self.assertIn("--allow-large-data", txt)

    def test_smoke_validation_large_data_guard(self) -> None:
        with TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            data_root.mkdir(parents=True, exist_ok=True)
            big = data_root / "big.csv"
            big.write_bytes(b"x" * (2 * 1024 * 1024))
            result = subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/run_smoke_validation.py",
                    "--tier",
                    "micro",
                    "--include-real-data",
                    "--data-root",
                    str(data_root),
                    "--large-data-threshold-mb",
                    "1",
                ],
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
