from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.external_holdout_trainer import train_external_holdout_baseline


class ExternalHoldoutTrainerTests(unittest.TestCase):
    def _write(self, path: Path, start: str, rows: int) -> None:
        labels = ["down", "flat", "up"]
        ts = pd.date_range(start=start, periods=rows, freq="15min", tz="UTC")
        df = pd.DataFrame(
            {
                "datetime": ts,
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": [1.1 + i * 0.0001 for i in range(rows)],
                "high": [1.2 + i * 0.0001 for i in range(rows)],
                "low": [1.0 + i * 0.0001 for i in range(rows)],
                "close": [1.15 + i * 0.0001 for i in range(rows)],
                "volume": [100 + i for i in range(rows)],
                "f1": [float(i % 5) for i in range(rows)],
                "f2": [float((i * 2) % 7) for i in range(rows)],
                "future_close_8": 1.2,
                "future_return_8": 0.01,
                "future_direction_8": [labels[i % 3] for i in range(rows)],
            }
        )
        df.to_csv(path, index=False)

    def test_train_and_holdout_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            train = Path(tmp) / "train.csv"
            hold = Path(tmp) / "hold.csv"
            out = Path(tmp) / "out"
            self._write(train, "2020-01-01", 30)
            self._write(hold, "2025-01-01", 20)
            rep = train_external_holdout_baseline(
                train_path=train,
                holdout_path=hold,
                output_dir=out,
                run_name="r",
                model_family="RandomForest",
            )
            self.assertTrue(rep.training_executed)
            self.assertTrue(rep.holdout_evaluation_executed)
            self.assertIn("metrics_holdout.json", rep.artifact_files)
            self.assertIn("predictions_holdout.csv", rep.artifact_files)
            forbidden = {"profit", "return", "sharpe", "drawdown", "pnl", "win_rate"}
            self.assertTrue(forbidden.isdisjoint(rep.holdout_metrics.keys()))

    def test_refuse_overwrite(self) -> None:
        with TemporaryDirectory() as tmp:
            train = Path(tmp) / "train.csv"
            hold = Path(tmp) / "hold.csv"
            out = Path(tmp) / "out"
            self._write(train, "2020-01-01", 30)
            self._write(hold, "2025-01-01", 20)
            train_external_holdout_baseline(
                train_path=train,
                holdout_path=hold,
                output_dir=out,
                run_name="r",
                model_family="RandomForest",
            )
            with self.assertRaises(FileExistsError):
                train_external_holdout_baseline(
                    train_path=train,
                    holdout_path=hold,
                    output_dir=out,
                    run_name="r",
                    model_family="RandomForest",
                )


if __name__ == "__main__":
    unittest.main()
