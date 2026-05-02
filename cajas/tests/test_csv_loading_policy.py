from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


class CsvLoadingPolicyTests(unittest.TestCase):
    def test_tiny_fixture_full_read_allowed(self) -> None:
        p = Path("cajas/data_examples/validation_fixtures/eurusd_tiny.csv")
        rep = evaluate_loading_decision(p, CsvLoadingPolicy())
        self.assertTrue(rep["can_full_read"])

    def test_large_file_blocked_without_allow(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "large.csv"
            p.write_bytes(b"x" * (2 * 1024 * 1024))
            rep = evaluate_loading_decision(
                p,
                CsvLoadingPolicy(max_bytes_without_allow_large_data=1024 * 1024),
            )
            self.assertEqual(rep["mode"], "blocked_full_read")

    def test_row_limit_enables_sample_mode(self) -> None:
        p = Path("cajas/data_examples/validation_fixtures/eurusd_tiny.csv")
        rep = evaluate_loading_decision(p, CsvLoadingPolicy(row_limit=2))
        self.assertEqual(rep["mode"], "sampled_read")


if __name__ == "__main__":
    unittest.main()
