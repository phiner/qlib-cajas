from __future__ import annotations

import unittest

import pandas as pd

from cajas.audits.feature_audit import audit_features


class FeatureAuditTests(unittest.TestCase):
    def test_leakage_column_error(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0], "future_return_8": [0.1, 0.2]})
        report = audit_features(df, declared_leakage_columns=["future_return_8"])
        self.assertTrue(any(i.code == "LEAKAGE_COLUMN_FOUND" for i in report.issues))

    def test_non_numeric_error(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0], "tag": ["a", "b"]})
        report = audit_features(df, declared_leakage_columns=[])
        self.assertTrue(any(i.code == "NON_NUMERIC_FEATURE" for i in report.issues))

    def test_all_null_error(self) -> None:
        df = pd.DataFrame({"x": [None, None]})
        report = audit_features(df, declared_leakage_columns=[])
        self.assertTrue(any(i.code == "ALL_NULL_FEATURE" for i in report.issues))

    def test_constant_warning(self) -> None:
        df = pd.DataFrame({"x": [1.0, 1.0], "y": [1.0, 2.0]})
        report = audit_features(df, declared_leakage_columns=[])
        self.assertTrue(any(i.code == "CONSTANT_FEATURE" for i in report.issues))

    def test_clean_numeric_features(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0], "y": [2.0, 3.0]})
        report = audit_features(df, declared_leakage_columns=[])
        self.assertEqual(report.feature_count, 2)
        self.assertFalse(any(i.severity == "error" for i in report.issues))


if __name__ == "__main__":
    unittest.main()
