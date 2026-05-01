from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_gate_builder import build_research_gate_packet


class ResearchGateBuilderTests(unittest.TestCase):
    def test_builder_complete_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            exp = d / "exp"
            exp.mkdir()
            (d / "contract.json").write_text("{}", encoding="utf-8")
            (exp / "experiment_manifest.json").write_text("{}", encoding="utf-8")
            (exp / "metrics.json").write_text(json.dumps({"valid": {"accuracy": 0.5, "macro_f1": 0.5}}), encoding="utf-8")
            (exp / "predictions.csv").write_text("split,y_true,y_pred\nvalid,up,up\n", encoding="utf-8")
            (exp / "split_summary.json").write_text(json.dumps({"train": 3, "valid": 1, "test": 1}), encoding="utf-8")
            reg = d / "reg.jsonl"
            reg.write_text(json.dumps({"run_id": "r1"}) + "\n", encoding="utf-8")
            comp = d / "comp.json"
            comp.write_text(json.dumps({"ranked_runs": [{"run_id": "r1"}]}), encoding="utf-8")
            p = build_research_gate_packet(contract_path=d / "contract.json", experiment_dir=exp, registry_path=reg, comparison_path=comp)
            self.assertIn(p["final_status"], {"offline_review_ready", "needs_manual_review", "blocked"})

    def test_missing_required_artifact_blocks(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            p = build_research_gate_packet(contract_path=d / "missing.json", experiment_dir=d / "exp")
            self.assertEqual(p["final_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
