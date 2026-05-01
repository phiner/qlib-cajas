from __future__ import annotations

import unittest

from cajas.reports.qlib_adapter_contract import ContractIssue
from cajas.reports.qlib_compatibility_report import build_qlib_compatibility_report


class QlibCompatibilityReportTests(unittest.TestCase):
    def test_incompatible_with_blocking(self) -> None:
        rep = build_qlib_compatibility_report(
            contract={"promotion_status": "blocked"},
            issues=[ContractIssue("error", "missing", "x")],
        )
        self.assertEqual(rep["compatibility_decision"], "incompatible")


if __name__ == "__main__":
    unittest.main()
