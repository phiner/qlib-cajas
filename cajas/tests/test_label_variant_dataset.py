from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.datasets.label_variant_dataset import LabelVariantExternalHoldoutDataset


class LabelVariantDatasetTests(unittest.TestCase):
    def test_excludes_future_columns(self) -> None:
        with TemporaryDirectory() as tmp:
            tr = Path(tmp) / "tr.csv"
            ho = Path(tmp) / "ho.csv"
            rows = [{"close": 1.0, "f1": 2.0, "future_return_8": 0.1, "future_direction_8": "up", "vlabel": "up"}]
            pd.DataFrame(rows).to_csv(tr, index=False)
            pd.DataFrame(rows).to_csv(ho, index=False)
            ds = LabelVariantExternalHoldoutDataset(train_path=tr, holdout_path=ho, label_col="vlabel")
            self.assertEqual(ds.feature_columns, ["close", "f1"])


if __name__ == "__main__":
    unittest.main()
