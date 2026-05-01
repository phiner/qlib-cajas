from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.candidate_promotion_manifest import build_candidate_promotion_manifest


class CandidatePromotionManifestTests(unittest.TestCase):
    def test_blocked_when_decision_not_candidate(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            packet = base / "decision.json"
            packet.write_text(json.dumps({"final_decision": "reject", "run_id": "r1", "non_blocking_findings": []}), encoding="utf-8")
            manifest = build_candidate_promotion_manifest(
                decision_packet_path=packet,
                out_dir=base,
                label_variant_id="label_a",
                feature_set_id="feature_a",
                target_name="future_direction_8",
                horizon=8,
                model_family="LightGBM",
            )
            self.assertEqual(manifest["status"], "blocked")


if __name__ == "__main__":
    unittest.main()

