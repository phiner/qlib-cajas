from __future__ import annotations

import unittest

from cajas.reports.research_blocker_localizer import build_research_blocker_localization


class ResearchBlockerLocalizerTests(unittest.TestCase):
    def test_localizes_repro_and_gov_blockers(self) -> None:
        rep = build_research_blocker_localization(
            stable_repro_report={"final_status": "not_stable_reproducible", "changed_normalized_hashes": [{"relative_path": "manifests/run_a_manifest.json"}]},
            repro_explanation={"classification": "semantic_mismatch"},
            normalization_coverage={"supported_file_types": [".json"]},
            governance_audit={"status": "fail"},
            governance_remediation={
                "final_suggested_status": "fail",
                "true_violations": [{"file": "cajas/x.py", "line": 10, "category": "broker_integration"}],
            },
            final_readiness={"final_status": "blocked"},
        )
        self.assertEqual(rep["current_final_readiness"], "blocked")
        self.assertEqual(len(rep["repro_mismatch_blockers"]), 1)
        self.assertEqual(len(rep["governance_true_violations"]), 1)


if __name__ == "__main__":
    unittest.main()

