from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.handlers.prepared_csv_handler import PreparedCsvHandler


class PreparedCsvHandlerTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str, rows: list[dict]) -> Path:
        path = Path(tmp_dir) / "prepared_dataset.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _base_rows(self) -> list[dict]:
        return [
            {
                "datetime": "2025-01-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 100,
                "return_1": 0.001,
                "future_close_8": 1.16,
                "future_return_8": 0.01,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-01-02T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.15,
                "high": 1.22,
                "low": 1.12,
                "close": 1.2,
                "volume": 120,
                "return_1": -0.001,
                "future_close_8": 1.18,
                "future_return_8": -0.01,
                "future_direction_8": "down",
            },
        ]

    def test_required_columns_validation(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            rows = self._base_rows()
            del rows[0]["volume"]
            path = self._write_csv(tmp_dir, rows)
            with self.assertRaisesRegex(ValueError, "Missing required columns"):
                PreparedCsvHandler(str(path))

    def test_feature_excludes_leakage_columns(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._base_rows())
            handler = PreparedCsvHandler(str(path))
            self.assertIn("return_1", handler.feature_columns)
            self.assertNotIn("future_close_8", handler.feature_columns)
            self.assertNotIn("future_return_8", handler.feature_columns)

    def test_segment_slicing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._base_rows())
            handler = PreparedCsvHandler(str(path))
            seg = handler.prepare_segment("2025-01-01", "2025-01-01")
            self.assertEqual(len(seg), 1)
            self.assertEqual(seg.iloc[0]["future_direction_8"], "up")

    def test_duplicate_datetime_rejection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            rows = self._base_rows()
            rows[1]["datetime"] = rows[0]["datetime"]
            path = self._write_csv(tmp_dir, rows)
            with self.assertRaisesRegex(ValueError, "Duplicate datetime"):
                PreparedCsvHandler(str(path))

    def test_label_distribution(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._base_rows())
            handler = PreparedCsvHandler(str(path))
            self.assertEqual(handler.label_distribution(), {"down": 1, "up": 1})


if __name__ == "__main__":
    unittest.main()
