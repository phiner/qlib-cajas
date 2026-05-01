from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_adapter_contract_builder import build_qlib_adapter_contract


class QlibAdapterContractBuilderTests(unittest.TestCase):
    def test_build_contract_from_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            manifest = d / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "promotion_id": "p1",
                        "decision_packet_path": str(d / "decision.json"),
                        "status": "candidate_for_manual_review",
                    }
                ),
                encoding="utf-8",
            )
            contract, issues = build_qlib_adapter_contract(
                promotion_manifest_path=manifest,
                candidate_id="c1",
                dataset_version="dv1",
                feature_set_id="fs1",
                label_variant_id="lv1",
                target_name="future_direction_8",
                frequency="15m",
                prediction_horizon=8,
            )
            self.assertEqual(contract["candidate_id"], "c1")
            self.assertEqual(len([i for i in issues if i.severity == "error"]), 0)


if __name__ == "__main__":
    unittest.main()
