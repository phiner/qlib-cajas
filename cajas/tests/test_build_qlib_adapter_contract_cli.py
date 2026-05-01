from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildQlibAdapterContractCliTests(unittest.TestCase):
    def test_cli_outputs_contract_and_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps({"promotion_id": "p2", "decision_packet_path": str(root / "decision.json"), "status": "draft"}),
                encoding="utf-8",
            )
            out = root / "qlib_adapter_contract.json"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/build_qlib_adapter_contract.py",
                    "--promotion-manifest",
                    str(manifest),
                    "--out",
                    str(out),
                    "--candidate-id",
                    "candidate2",
                    "--feature-set-id",
                    "fs2",
                    "--label-variant-id",
                    "lv2",
                    "--target-name",
                    "future_direction_8",
                    "--frequency",
                    "15m",
                ],
                check=True,
            )
            self.assertTrue(out.exists())
            self.assertTrue((root / "qlib_adapter_contract.validation.json").exists())


if __name__ == "__main__":
    unittest.main()
