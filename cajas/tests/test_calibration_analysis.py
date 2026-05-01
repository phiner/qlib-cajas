from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.calibration_analysis import analyze_calibration


class CalibrationAnalysisTests(unittest.TestCase):
    def test_ece_like(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "p.csv"
            pd.DataFrame(
                [
                    {"label": "up", "predicted_label": "up", "proba_up": 0.9, "proba_down": 0.1},
                    {"label": "down", "predicted_label": "up", "proba_up": 0.8, "proba_down": 0.2},
                ]
            ).to_csv(p, index=False)
            rep = analyze_calibration(prediction_csv=p, split="holdout", bucket_count=5)
            self.assertIn("ece_like", rep)


if __name__ == "__main__":
    unittest.main()
