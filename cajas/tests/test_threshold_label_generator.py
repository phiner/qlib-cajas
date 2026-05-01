from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.datasets.threshold_label_generator import build_threshold_label_col, generate_threshold_labels


class ThresholdLabelGeneratorTests(unittest.TestCase):
    def test_generates_expected_label_cols(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "in.csv"
            pd.DataFrame({"close": [1.0, 1.1, 1.0, 1.2, 1.25]}).to_csv(p, index=False)
            out = Path(tmp) / "out.csv"
            rep = generate_threshold_labels(input_path=p, horizons=[4, 8], thresholds=[0.0, 0.0001], output_path=out)
            self.assertTrue(out.exists())
            self.assertIn(build_threshold_label_col(4, 0.0), rep.label_distributions)


if __name__ == "__main__":
    unittest.main()
