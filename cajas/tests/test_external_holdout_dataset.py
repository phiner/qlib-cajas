from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.datasets.external_holdout_dataset import ExternalHoldoutDataset


class ExternalHoldoutDatasetTests(unittest.TestCase):
    def _write(self, path: Path, start: str, rows: int) -> None:
        ts = pd.date_range(start=start, periods=rows, freq="15min", tz="UTC")
        df = pd.DataFrame(
            {
                "datetime": ts,
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": range(rows),
                "f1": [float(i) for i in range(rows)],
                "future_close_8": 1.2,
                "future_return_8": 0.01,
                "future_direction_8": ["down", "flat", "up", "down", "up"][:rows],
            }
        )
        df.to_csv(path, index=False)

    def test_separate_train_holdout_and_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            t = Path(tmp) / "train.csv"
            h = Path(tmp) / "hold.csv"
            self._write(t, "2020-01-01", 5)
            self._write(h, "2025-01-01", 5)
            ds = ExternalHoldoutDataset(train_path=t, holdout_path=h)
            xtr, ytr = ds.prepare_train()
            xh, yh = ds.prepare_holdout()
            self.assertEqual(len(xtr), 5)
            self.assertEqual(len(xh), 5)
            self.assertNotIn("future_close_8", xtr.columns)
            payload = ds.summary().to_dict()
            json.dumps(payload)

    def test_overlap_detection(self) -> None:
        with TemporaryDirectory() as tmp:
            t = Path(tmp) / "train.csv"
            h = Path(tmp) / "hold.csv"
            self._write(t, "2025-01-01", 5)
            self._write(h, "2025-01-01", 5)
            with self.assertRaises(ValueError):
                ExternalHoldoutDataset(train_path=t, holdout_path=h)


if __name__ == "__main__":
    unittest.main()
