from __future__ import annotations

import unittest
from pathlib import Path

from cajas.data_io.chunked_csv_reader import iter_csv_chunks
from cajas.data_io.fx_kline_schema import inspect_fx_kline_schema


FIX = Path("cajas/data_examples/validation_fixtures/eurusd_tiny.csv")


class ChunkedCsvReaderTests(unittest.TestCase):
    def test_iterates_chunks_with_row_limit(self) -> None:
        chunks = list(iter_csv_chunks(FIX, chunk_size=2, row_limit=2))
        total = sum(len(c) for c in chunks)
        self.assertEqual(total, 2)

    def test_selected_columns(self) -> None:
        chunks = list(iter_csv_chunks(FIX, columns=["Open", "Close"], chunk_size=2, row_limit=2))
        first = chunks[0]
        if hasattr(first, "columns"):
            self.assertIn("Open", list(first.columns))
            self.assertNotIn("High", list(first.columns))
        else:
            self.assertIn("Open", first[0])
            self.assertNotIn("High", first[0])

    def test_fx_schema_inspection(self) -> None:
        rep = inspect_fx_kline_schema(csv_path=FIX)
        self.assertEqual(rep["status"], "pass")
        self.assertEqual(rep["mapped_columns"]["open"], "Open")


if __name__ == "__main__":
    unittest.main()
