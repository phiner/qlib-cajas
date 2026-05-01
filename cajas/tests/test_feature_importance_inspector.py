from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from sklearn.ensemble import RandomForestClassifier
import joblib
import pandas as pd

from cajas.baseline.feature_importance_inspector import inspect_feature_importance


class FeatureImportanceInspectorTests(unittest.TestCase):
    def test_inspect_importance(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            X = pd.DataFrame({"a": [0, 1, 0, 1], "b": [1, 0, 1, 0]})
            y = [0, 1, 0, 1]
            m = RandomForestClassifier(n_estimators=10, random_state=1).fit(X, y)
            joblib.dump(m, d / "model.joblib")
            (d / "feature_columns.json").write_text(json.dumps({"feature_columns": ["a", "b"]}), encoding="utf-8")
            rep = inspect_feature_importance(run_dir=d, top_k=2)
            self.assertTrue(rep.available)
            self.assertEqual(len(rep.top_features), 2)


if __name__ == "__main__":
    unittest.main()
