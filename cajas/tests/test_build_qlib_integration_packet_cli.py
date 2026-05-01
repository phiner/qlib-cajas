from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildQlibIntegrationPacketCliTests(unittest.TestCase):
    def test_cli_outputs_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "contract.json"
            contract.write_text(
                json.dumps(
                    {
                        "contract_version": "v1",
                        "candidate_id": "c",
                        "research_run_id": "r",
                        "dataset_version": "d",
                        "feature_set_id": "f",
                        "label_variant_id": "l",
                        "target_name": "future_direction_8",
                        "prediction_horizon": 8,
                        "instrument_universe": ["EURUSD"],
                        "frequency": "15m",
                        "required_feature_columns": ["close"],
                        "required_label_columns": ["future_direction_8"],
                        "artifact_paths": {"decision_packet_path": str(root / "dp.json")},
                        "promotion_status": "candidate_for_manual_review",
                        "created_at_utc": "2026-01-01T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            out = root / "out"
            subprocess.run(
                [sys.executable, "cajas/scripts/build_qlib_integration_packet.py", "--adapter-contract", str(contract), "--out-dir", str(out)],
                check=True,
            )
            self.assertTrue((out / "qlib_integration_packet.json").exists())
            self.assertTrue((out / "qlib_integration_packet.md").exists())


if __name__ == "__main__":
    unittest.main()
