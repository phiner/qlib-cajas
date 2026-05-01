from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildResearchGatePacketCliTests(unittest.TestCase):
    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            exp = d / "exp"
            exp.mkdir()
            (d / "contract.json").write_text("{}", encoding="utf-8")
            (exp / "experiment_manifest.json").write_text("{}", encoding="utf-8")
            (exp / "metrics.json").write_text(json.dumps({"valid": {"accuracy": 0.5, "macro_f1": 0.5}}), encoding="utf-8")
            (exp / "predictions.csv").write_text("split,y_true,y_pred\nvalid,up,up\n", encoding="utf-8")
            (exp / "split_summary.json").write_text(json.dumps({"train": 3, "valid": 1, "test": 1}), encoding="utf-8")
            out = d / "gate.json"
            subprocess.run([
                sys.executable, "cajas/scripts/build_research_gate_packet.py",
                "--contract", str(d / "contract.json"),
                "--experiment-dir", str(exp),
                "--out", str(out),
            ], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
