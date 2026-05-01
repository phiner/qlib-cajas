from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.error_slice_analysis import analyze_error_slices


class ErrorSliceAnalysisTests(unittest.TestCase):
    def test_slices_written(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "pred.csv"
            pd.DataFrame(
                [
                    {"datetime": "2025-01-01T00:00:00+00:00", "label": "up", "predicted_label": "down", "proba_up": 0.4, "proba_down": 0.6},
                    {"datetime": "2025-01-01T01:00:00+00:00", "label": "up", "predicted_label": "up", "proba_up": 0.8, "proba_down": 0.2},
                ]
            ).to_csv(p, index=False)
            rep = analyze_error_slices(prediction_csv=p, output_dir=Path(tmp), run_name="r")
            self.assertTrue(rep["slices"])


if __name__ == "__main__":
    unittest.main()
