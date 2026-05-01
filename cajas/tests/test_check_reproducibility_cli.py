from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CheckReproducibilityCliTests(unittest.TestCase):
    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            l = d / "l.json"
            r = d / "r.json"
            l.write_text(json.dumps({"root": "a", "artifact_inventory": []}), encoding="utf-8")
            r.write_text(json.dumps({"root": "b", "artifact_inventory": []}), encoding="utf-8")
            out = d / "rep.json"
            subprocess.run([sys.executable, "cajas/scripts/check_reproducibility.py", "--left", str(l), "--right", str(r), "--out", str(out)], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
