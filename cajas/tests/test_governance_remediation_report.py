from __future__ import annotations

import unittest

from cajas.audits.governance_remediation_report import build_governance_remediation_report


class GovernanceRemediationReportTests(unittest.TestCase):
    def test_classifies_boundary_docs_and_true_violation(self) -> None:
        report = build_governance_remediation_report(
            governance_audit={
                "status": "fail",
                "findings": [
                    {"file": "cajas/README.md", "line": 1, "category": "live_trading", "severity": "warning", "snippet": "do not add live trading"},
                    {"file": "cajas/x.py", "line": 2, "category": "broker_integration", "severity": "error", "snippet": "submit_order(client, x)"},
                ],
            }
        )
        self.assertEqual(report["final_suggested_status"], "fail")
        self.assertGreaterEqual(report["finding_classification_counts"].get("true_violation", 0), 1)


if __name__ == "__main__":
    unittest.main()

