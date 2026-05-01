from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.datasets.prepared_dataset import PreparedDataset


class PreparedDatasetTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str, rows: list[dict]) -> Path:
        path = Path(tmp_dir) / "prepared_dataset.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _rows(self) -> list[dict]:
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
                "datetime": "2025-09-15T00:00:00Z",
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

    def test_prepare_train_lengths_match(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            ds = PreparedDataset(str(path))
            x, y = ds.prepare("train")
            self.assertEqual(len(x), len(y))

    def test_unknown_segment_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            ds = PreparedDataset(str(path))
            with self.assertRaisesRegex(ValueError, "Unknown segment"):
                ds.prepare("unknown")

    def test_empty_segment_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            ds = PreparedDataset(
                str(path),
                segments={"train": ("2024-01-01", "2024-01-02")},
            )
            with self.assertRaisesRegex(ValueError, "Segment has zero rows"):
                ds.prepare("train")

    def test_leakage_excluded_from_features(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            ds = PreparedDataset(str(path))
            self.assertNotIn("future_close_8", ds.feature_columns)
            self.assertNotIn("future_return_8", ds.feature_columns)

    def test_labels_remain_available(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            ds = PreparedDataset(str(path))
            _, y = ds.prepare("train")
            self.assertIn(y.iloc[0], {"up", "down", "flat"})


if __name__ == "__main__":
    unittest.main()
