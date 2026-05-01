from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildCandidatePromotionManifestCliTests(unittest.TestCase):
    def test_cli_outputs_manifest_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "research_decision_packet.json"
            packet.write_text(
                json.dumps({"final_decision": "candidate_for_qlib_trial", "run_id": "r2", "non_blocking_findings": []}),
                encoding="utf-8",
            )
            out = root / "manifest"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/build_candidate_promotion_manifest.py",
                    "--decision-packet",
                    str(packet),
                    "--out-dir",
                    str(out),
                    "--label-variant-id",
                    "label_x",
                    "--feature-set-id",
                    "feature_x",
                    "--target-name",
                    "future_direction_8",
                    "--horizon",
                    "8",
                    "--model-family",
                    "LightGBM",
                ],
                check=True,
            )
            self.assertTrue((out / "candidate_promotion_manifest.json").exists())
            self.assertTrue((out / "candidate_promotion_manifest.md").exists())


if __name__ == "__main__":
    unittest.main()

