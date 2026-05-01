from __future__ import annotations

import json
import unittest

import numpy as np
import pandas as pd

from cajas.baseline.feature_value_audit import audit_feature_values


class FeatureValueAuditTests(unittest.TestCase):
    def test_detects_nan_inf_large(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, np.inf], "b": [0.0, -np.inf, 1e15]})
        rep = audit_feature_values(df)
        self.assertGreater(rep.nan_count, 0)
        self.assertGreater(rep.pos_inf_count, 0)
        self.assertGreater(rep.neg_inf_count, 0)
        self.assertGreater(rep.large_value_count, 0)

    def test_serialization(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0]})
        payload = audit_feature_values(df).to_dict()
        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
