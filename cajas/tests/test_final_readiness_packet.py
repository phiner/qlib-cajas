from __future__ import annotations

import unittest

from cajas.reports.final_readiness_packet import build_final_readiness_packet


class FinalReadinessPacketTests(unittest.TestCase):
    def test_preserves_blocked_boundaries(self) -> None:
        packet = build_final_readiness_packet(
            gate_packet={"final_status": "blocked", "metric_summary": {}, "manual_review_checklist": []},
            no_broker_packet={"disabled_capabilities": ["no_broker"], "next_blocked_actions": ["no_broker"]},
            manifest={"missing_artifact_paths": [], "artifact_inventory": []},
            reproducibility_report={"final_status": "reproducible", "warnings": []},
            ci_plan={"tiers": []},
        )
        self.assertEqual(packet["final_status"], "blocked")

    def test_normalization_only_mismatch_needs_normalization_review(self) -> None:
        packet = build_final_readiness_packet(
            gate_packet={"final_status": "pass", "metric_summary": {}, "manual_review_checklist": []},
            no_broker_packet={"disabled_capabilities": ["no_broker"], "next_blocked_actions": ["no_broker"]},
            manifest={"missing_artifact_paths": [], "artifact_inventory": []},
            reproducibility_report={"final_status": "reproducible", "warnings": []},
            stable_reproducibility_report={"final_status": "stable_reproducible_with_warnings", "changed_normalized_hashes": []},
            stable_reproducibility_explanation={"classification": "normalization_gap"},
            governance_remediation_report={"final_suggested_status": "pass", "true_violations": [], "manual_review_findings": []},
            normalization_coverage_report={"supported_file_types": [".json"], "candidate_new_normalization_rules": []},
            ci_plan={"tiers": []},
        )
        self.assertEqual(packet["final_status"], "needs_normalization_review")


if __name__ == "__main__":
    unittest.main()
