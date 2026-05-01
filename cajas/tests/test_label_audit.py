from __future__ import annotations

import unittest

import pandas as pd

from cajas.audits.label_audit import audit_labels


class LabelAuditTests(unittest.TestCase):
    def test_expected_classes_pass(self) -> None:
        s = pd.Series(["down", "flat", "up"] * 10)
        report = audit_labels(s, rare_class_min_count=2)
        self.assertFalse(any(i.severity == "error" for i in report.issues))

    def test_unknown_class_error(self) -> None:
        s = pd.Series(["down", "weird"])
        report = audit_labels(s, rare_class_min_count=1)
        self.assertTrue(any(i.code == "UNKNOWN_CLASS" for i in report.issues))

    def test_missing_labels_error(self) -> None:
        s = pd.Series(["down", None, "up"])
        report = audit_labels(s, rare_class_min_count=1)
        self.assertTrue(any(i.code == "MISSING_LABELS" for i in report.issues))

    def test_rare_class_warning(self) -> None:
        s = pd.Series(["down"] * 20 + ["up"] * 20 + ["flat"])
        report = audit_labels(s, rare_class_min_count=5)
        self.assertTrue(any(i.code == "RARE_CLASS" for i in report.issues))


if __name__ == "__main__":
    unittest.main()
