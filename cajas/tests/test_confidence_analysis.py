from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.confidence_analysis import analyze_prediction_confidence


class ConfidenceAnalysisTests(unittest.TestCase):
    def test_bucket_metrics(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "pred.csv"
            pd.DataFrame(
                [
                    {"label": "up", "predicted_label": "up", "proba_up": 0.9, "proba_down": 0.1},
                    {"label": "down", "predicted_label": "up", "proba_up": 0.6, "proba_down": 0.4},
                ]
            ).to_csv(p, index=False)
            rep = analyze_prediction_confidence(prediction_csv=p, split="test")
            self.assertEqual(rep.total_rows, 2)
            self.assertTrue(rep.buckets)
            self.assertFalse(rep.trading_thresholds_created)

    def test_missing_proba_warning(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "pred.csv"
            pd.DataFrame([{"label": "up", "predicted_label": "up"}]).to_csv(p, index=False)
            rep = analyze_prediction_confidence(prediction_csv=p, split="test")
            self.assertTrue(rep.warnings)


if __name__ == "__main__":
    unittest.main()
