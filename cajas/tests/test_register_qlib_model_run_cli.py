from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RegisterQlibModelRunCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            exp = d / "exp"
            exp.mkdir()
            (exp / "experiment_manifest.json").write_text(json.dumps({"run_id": "r1"}), encoding="utf-8")
            (exp / "metrics.json").write_text(json.dumps({"valid": {"accuracy": 0.5, "macro_f1": 0.4}}), encoding="utf-8")
            (exp / "split_summary.json").write_text(json.dumps({"train": 10, "valid": 5, "test": 5}), encoding="utf-8")
            (exp / "feature_columns.json").write_text(json.dumps({"feature_columns": ["close"]}), encoding="utf-8")
            reg = d / "registry.jsonl"
            subprocess.run([
                sys.executable, "cajas/scripts/register_qlib_model_run.py", "--experiment-dir", str(exp), "--registry", str(reg)
            ], check=True)
            self.assertTrue(reg.exists())


if __name__ == "__main__":
    unittest.main()
