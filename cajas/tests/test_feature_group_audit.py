from __future__ import annotations

import unittest

from cajas.baseline.feature_group_audit import build_feature_group_audit


class FeatureGroupAuditTests(unittest.TestCase):
    def test_classifies_known_columns(self) -> None:
        cols = [
            "close_return_1",
            "candle_body",
            "rolling_volatility_8",
            "rolling_mean_close_8",
            "session_hour",
            "custom_feature",
        ]
        rep = build_feature_group_audit(cols)
        self.assertEqual(rep["feature_count"], 6)
        self.assertIn("close_return_1", rep["groups"]["price_return"])
        self.assertIn("candle_body", rep["groups"]["range_body"])
        self.assertIn("rolling_volatility_8", rep["groups"]["volatility"])
        self.assertIn("rolling_mean_close_8", rep["groups"]["rolling_stats"])
        self.assertIn("session_hour", rep["groups"]["time_session"])
        self.assertIn("custom_feature", rep["groups"]["other"])


if __name__ == "__main__":
    unittest.main()
