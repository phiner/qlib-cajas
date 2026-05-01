from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CompareQlibModelRunsCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            reg = d / "registry.jsonl"
            reg.write_text(json.dumps({"run_id": "r1", "metrics": {"macro_f1": 0.5, "accuracy": 0.6}}) + "\n", encoding="utf-8")
            out = d / "comparison.json"
            subprocess.run([
                sys.executable, "cajas/scripts/compare_qlib_model_runs.py", "--registry", str(reg), "--out", str(out)
            ], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
