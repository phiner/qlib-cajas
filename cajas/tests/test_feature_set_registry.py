from __future__ import annotations

import unittest

from cajas.features.feature_set_registry import list_feature_sets, resolve_feature_columns_for_set


class FeatureSetRegistryTests(unittest.TestCase):
    def test_resolve_excludes_future_cols(self) -> None:
        cols = ["close", "future_return_8", "future_direction_8", "body_ratio", "datetime"]
        out = resolve_feature_columns_for_set(all_columns=cols, feature_set="structure_v1", label_col="future_direction_8")
        self.assertIn("body_ratio", out)
        self.assertNotIn("future_return_8", out)
        self.assertIn("minimal_v1", list_feature_sets())


if __name__ == "__main__":
    unittest.main()
