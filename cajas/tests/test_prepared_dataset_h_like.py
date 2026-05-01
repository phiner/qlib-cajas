from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.qlib_compat.prepared_dataset_h_like import PreparedDatasetHLike


class PreparedDatasetHLikeTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str) -> Path:
        rows = [
            {
                "datetime": "2025-01-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 100,
                "feature_a": 0.1,
                "future_close_8": 1.16,
                "future_return_8": 0.01,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-09-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.3,
                "low": 1.1,
                "close": 1.2,
                "volume": 110,
                "feature_a": 0.2,
                "future_close_8": 1.21,
                "future_return_8": 0.01,
                "future_direction_8": "down",
            },
            {
                "datetime": "2025-11-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.3,
                "high": 1.35,
                "low": 1.2,
                "close": 1.28,
                "volume": 120,
                "feature_a": 0.3,
                "future_close_8": 1.29,
                "future_return_8": 0.01,
                "future_direction_8": "flat",
            },
        ]
        path = Path(tmp_dir) / "d.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def test_prepare_single_segment(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            ds = PreparedDataset(str(self._write_csv(tmp_dir)))
            shim = PreparedDatasetHLike(ds)
            x, y = shim.prepare("train")
            self.assertEqual(len(x), len(y))

    def test_prepare_multiple_segments(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            ds = PreparedDataset(str(self._write_csv(tmp_dir)))
            shim = PreparedDatasetHLike(ds)
            out = shim.prepare(["train", "valid"], col_set="feature", data_key="learn")
            self.assertIn("train", out)
            self.assertIn("valid", out)

    def test_unknown_segment_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            ds = PreparedDataset(str(self._write_csv(tmp_dir)))
            shim = PreparedDatasetHLike(ds)
            with self.assertRaisesRegex(ValueError, "Unknown segment"):
                shim.prepare("bad")

    def test_invalid_segments_type_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            ds = PreparedDataset(str(self._write_csv(tmp_dir)))
            shim = PreparedDatasetHLike(ds)
            with self.assertRaisesRegex(TypeError, "segments must be"):
                shim.prepare({"train": True})


if __name__ == "__main__":
    unittest.main()
