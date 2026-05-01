from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.feature_set_comparison import run_feature_set_comparison


class FeatureSetComparisonTests(unittest.TestCase):
    def test_runs(self) -> None:
        with TemporaryDirectory() as tmp:
            tr = Path(tmp) / "tr.csv"
            ho = Path(tmp) / "ho.csv"
            rows = [{"open": 1 + i, "high": 2 + i, "low": 0.5 + i, "close": 1.2 + i, "body_ratio": 0.3, "future_direction_8": "up" if i % 2 == 0 else "down"} for i in range(40)]
            pd.DataFrame(rows).to_csv(tr, index=False)
            pd.DataFrame(rows).to_csv(ho, index=False)
            rep = run_feature_set_comparison(
                train_path=tr,
                holdout_path=ho,
                label_col="future_direction_8",
                feature_sets=["minimal_v1", "structure_v1"],
                output_dir=Path(tmp) / "out",
                run_name="r",
                model_family="RandomForest",
            )
            self.assertTrue(rep["rows"])


if __name__ == "__main__":
    unittest.main()
