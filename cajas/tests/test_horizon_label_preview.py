from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.datasets.horizon_label_preview import preview_horizon_labels


class HorizonLabelPreviewTests(unittest.TestCase):
    def test_builds_distributions_for_multiple_horizons(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "prepared.csv"
            pd.DataFrame({"close": [1.0, 1.1, 1.05, 1.2, 1.2, 1.15, 1.25]}).to_csv(p, index=False)
            rep = preview_horizon_labels(input_path=p, horizons=[4, 8, 16])
            self.assertEqual([h.horizon for h in rep.horizons], [4, 8, 16])
            self.assertEqual(rep.horizons[1].row_count, 0)
            self.assertEqual(rep.horizons[2].row_count, 0)


if __name__ == "__main__":
    unittest.main()
