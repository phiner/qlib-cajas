from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.prediction_review import build_prediction_review


class PredictionReviewTests(unittest.TestCase):
    def _write_prediction_csv(self, path: Path, with_proba: bool) -> None:
        rows = [
            {
                "datetime": "2025-01-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "label": "down",
                "encoded_label": 0,
                "predicted_label": "down",
                "predicted_encoded_label": 0,
                "proba_down": 0.8,
                "proba_flat": 0.1,
                "proba_up": 0.1,
            },
            {
                "datetime": "2025-01-01T00:15:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "label": "up",
                "encoded_label": 2,
                "predicted_label": "down",
                "predicted_encoded_label": 0,
                "proba_down": 0.75,
                "proba_flat": 0.1,
                "proba_up": 0.15,
            },
            {
                "datetime": "2025-01-01T00:30:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "label": "flat",
                "encoded_label": 1,
                "predicted_label": "up",
                "predicted_encoded_label": 2,
                "proba_down": 0.2,
                "proba_flat": 0.3,
                "proba_up": 0.5,
            },
        ]
        df = pd.DataFrame(rows)
        if not with_proba:
            df = df.drop(columns=["proba_down", "proba_flat", "proba_up"])
        df.to_csv(path, index=False)

    def test_review_outputs_with_probabilities(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pred = Path(tmp_dir) / "pred.csv"
            out = Path(tmp_dir) / "out"
            self._write_prediction_csv(pred, with_proba=True)
            report = build_prediction_review(
                prediction_csv=pred,
                output_dir=out,
                split="valid",
                low_confidence_threshold=0.45,
                high_confidence_error_threshold=0.70,
            )
            self.assertEqual(report.total_rows, 3)
            self.assertEqual(report.error_rows, 2)
            self.assertGreaterEqual(report.high_confidence_error_count, 1)
            self.assertTrue((out / "valid_prediction_review_report.json").exists())

    def test_missing_probability_columns_warns(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pred = Path(tmp_dir) / "pred.csv"
            out = Path(tmp_dir) / "out"
            self._write_prediction_csv(pred, with_proba=False)
            report = build_prediction_review(prediction_csv=pred, output_dir=out, split="test")
            self.assertTrue(report.warnings)
            self.assertEqual(report.low_confidence_count, 0)
            self.assertEqual(report.high_confidence_error_count, 0)

    def test_no_trading_metric_keys(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pred = Path(tmp_dir) / "pred.csv"
            out = Path(tmp_dir) / "out"
            self._write_prediction_csv(pred, with_proba=True)
            payload = build_prediction_review(prediction_csv=pred, output_dir=out, split="valid").to_dict()
            json.dumps(payload)
            forbidden = {"profit", "return", "sharpe", "drawdown", "pnl", "win_rate"}
            self.assertTrue(forbidden.isdisjoint(payload.keys()))

    def test_row_limit_reduces_review_rows(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pred = Path(tmp_dir) / "pred.csv"
            out = Path(tmp_dir) / "out"
            self._write_prediction_csv(pred, with_proba=True)
            report = build_prediction_review(prediction_csv=pred, output_dir=out, split="valid", row_limit=2)
            self.assertEqual(report.total_rows, 2)


if __name__ == "__main__":
    unittest.main()
