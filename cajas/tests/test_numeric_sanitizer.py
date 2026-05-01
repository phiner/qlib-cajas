from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from cajas.baseline.numeric_sanitizer import sanitize_features_for_model


class NumericSanitizerTests(unittest.TestCase):
    def test_replaces_and_clips_without_mutating(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, np.inf], "b": [-np.inf, 2e7, 3.0]})
        orig = df.copy(deep=True)
        out, rep = sanitize_features_for_model(df, clip_abs_value=1e6, fill_value=0.0)
        self.assertTrue(df.equals(orig))
        self.assertEqual(out.columns.tolist(), df.columns.tolist())
        self.assertEqual(out.index.tolist(), df.index.tolist())
        self.assertTrue(np.isfinite(out.to_numpy(dtype=float)).all())
        self.assertGreater(rep.nan_replaced, 0)
        self.assertGreater(rep.pos_inf_replaced, 0)
        self.assertGreater(rep.neg_inf_replaced, 0)


if __name__ == "__main__":
    unittest.main()
