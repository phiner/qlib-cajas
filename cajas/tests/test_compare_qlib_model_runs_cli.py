from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.compare_qlib_model_runs import main


class CompareQlibModelRunsCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            reg = d / "registry.jsonl"
            reg.write_text(json.dumps({"run_id": "r1", "metrics": {"macro_f1": 0.5, "accuracy": 0.6}}) + "\n", encoding="utf-8")
            out = d / "comparison.json"
            code = main(["--registry", str(reg), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
