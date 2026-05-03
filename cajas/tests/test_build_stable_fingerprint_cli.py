from __future__ import annotations
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_stable_fingerprint import main


class BuildStableFingerprintCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            Path(d, "a.json").write_text("{}", encoding="utf-8")
            out = d / "fp.json"
            code = main(["--root", str(d), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
