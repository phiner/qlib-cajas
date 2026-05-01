from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.flat_class_diagnosis import diagnose_flat_class


class FlatClassDiagnosisTests(unittest.TestCase):
    def test_detects_low_support_and_no_predictions(self) -> None:
        with TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "predictions_holdout.csv"
            pd.DataFrame(
                [
                    {"label": "up", "predicted_label": "up"},
                    {"label": "down", "predicted_label": "up"},
                    {"label": "flat", "predicted_label": "up"},
                ]
            ).to_csv(csv_path, index=False)
            rep = diagnose_flat_class(prediction_csv=csv_path, split="holdout")
            self.assertEqual(rep.flat_support, 1)
            self.assertEqual(rep.flat_predictions, 0)
            self.assertTrue(any("zero flat" in w for w in rep.warnings))
            self.assertFalse(rep.trading_conclusions_present)


if __name__ == "__main__":
    unittest.main()
