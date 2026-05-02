from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


FIX = Path("cajas/data_examples/validation_fixtures/eurusd_tiny.csv")


class ColumnarCacheConversionTests(unittest.TestCase):
    def test_fallback_shards_and_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "cache"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/convert_csv_to_columnar_cache.py",
                    "--input",
                    str(FIX),
                    "--out-dir",
                    str(out),
                    "--chunk-size",
                    "2",
                    "--row-limit",
                    "3",
                    "--force",
                ],
                check=True,
            )
            manifest = json.loads((out / "columnar_cache_manifest.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(manifest["chunks"]), 1)


if __name__ == "__main__":
    unittest.main()
