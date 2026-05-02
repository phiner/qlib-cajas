from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.data_io.large_csv_metadata import inspect_large_csv_metadata


FIX = Path("cajas/data_examples/validation_fixtures/eurusd_tiny.csv")


class LargeCsvMetadataTests(unittest.TestCase):
    def test_sample_only_defaults(self) -> None:
        rep = inspect_large_csv_metadata(input_path=FIX)
        self.assertEqual(rep["row_count_mode"], "not_requested")
        self.assertEqual(rep["hash_mode"], "not_requested")
        self.assertIn("Open", rep["header_columns"])

    def test_count_rows_optional(self) -> None:
        rep = inspect_large_csv_metadata(input_path=FIX, count_rows=True)
        self.assertEqual(rep["row_count"], 3)

    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "meta.json"
            subprocess.run(
                [sys.executable, "cajas/scripts/inspect_large_csv.py", "--input", str(FIX), "--out", str(out), "--sample-lines", "10"],
                check=True,
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("header_columns", payload)


if __name__ == "__main__":
    unittest.main()
