from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunQlibAdapterSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out_root = Path(tmp) / "smoke"
            subprocess.run([sys.executable, "cajas/scripts/run_qlib_adapter_smoke.py", "--out-root", str(out_root)], check=True)
            self.assertTrue((out_root / "contract" / "qlib_adapter_contract.json").exists())
            self.assertTrue((out_root / "packet" / "qlib_integration_packet.json").exists())
            self.assertTrue((out_root / "compat" / "qlib_compatibility_report.json").exists())


if __name__ == "__main__":
    unittest.main()
