from __future__ import annotations

import unittest

from cajas.reports.stable_reproducibility_explainer import build_stable_reproducibility_explanation


class StableReproducibilityExplainerTests(unittest.TestCase):
    def test_classifies_missing_artifacts(self) -> None:
        report = build_stable_reproducibility_explanation(
            left_fingerprint={"included_files": [{"relative_path": "a.json", "stable_hash": "1"}]},
            right_fingerprint={"included_files": []},
            stable_repro_report={"final_status": "not_stable_reproducible", "missing_left": ["a.json"], "missing_right": [], "changed_normalized_hashes": []},
        )
        self.assertEqual(report["classification"], "missing_artifact")

    def test_preserves_semantic_mismatch(self) -> None:
        report = build_stable_reproducibility_explanation(
            left_fingerprint={"included_files": [{"relative_path": "metrics.json", "stable_hash": "1"}]},
            right_fingerprint={"included_files": [{"relative_path": "metrics.json", "stable_hash": "2"}]},
            stable_repro_report={
                "final_status": "not_stable_reproducible",
                "missing_left": [],
                "missing_right": [],
                "changed_normalized_hashes": [{"relative_path": "metrics.json", "left": "1", "right": "2"}],
            },
        )
        self.assertEqual(report["classification"], "semantic_mismatch")


if __name__ == "__main__":
    unittest.main()

