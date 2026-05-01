from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.features.kline_structure_features import add_kline_structure_features


class KlineStructureFeaturesTests(unittest.TestCase):
    def test_adds_features(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "in.csv"
            pd.DataFrame({"open": [1, 2, 3], "high": [2, 3, 4], "low": [0.5, 1.5, 2.5], "close": [1.5, 2.5, 3.5]}).to_csv(p, index=False)
            out, rep = add_kline_structure_features(input_path=p)
            self.assertIn("body_abs", out.columns)
            self.assertGreater(len(rep.added_features), 0)


if __name__ == "__main__":
    unittest.main()
