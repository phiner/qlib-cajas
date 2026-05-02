from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.data_io.dataset_cache_index import build_dataset_cache_index, detect_stale_cache
from cajas.data_io.dataset_file_manifest import build_dataset_file_manifest


class DatasetManifestCacheTests(unittest.TestCase):
    def test_manifest_and_cache_index(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv"
            src.write_text(
                "Time (UTC),Open,High,Low,Close,Volume\n2025.01.01 00:00:00,1,2,0.5,1.5,100\n",
                encoding="utf-8",
            )
            manifest = build_dataset_file_manifest(data_root=root, pattern="EURUSD_15 Mins_Bid_*.csv")
            self.assertEqual(len(manifest["source_files"]), 1)
            cache = build_dataset_cache_index(manifest=manifest, cache_root=root / "cache")
            self.assertEqual(len(cache["entries"]), 1)
            src.write_text(
                "Time (UTC),Open,High,Low,Close,Volume\n2025.01.01 00:00:00,1,2,0.5,1.5,100\n2025.01.01 00:15:00,1,2,0.5,1.5,100\n",
                encoding="utf-8",
            )
            refreshed = build_dataset_file_manifest(data_root=root, pattern="EURUSD_15 Mins_Bid_*.csv")
            stale = detect_stale_cache(cache_index=cache, refreshed_manifest=refreshed)
            self.assertEqual(stale["stale_entry_count"], 1)

    def test_manifest_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv"
            src.write_text("Time (UTC),Open,High,Low,Close,Volume\n2025.01.01 00:00:00,1,2,0.5,1.5,100\n", encoding="utf-8")
            out = root / "manifest.json"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/build_dataset_file_manifest.py",
                    "--data-root",
                    str(root),
                    "--pattern",
                    "EURUSD_15 Mins_Bid_*.csv",
                    "--out",
                    str(out),
                ],
                check=True,
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("source_files", payload)


if __name__ == "__main__":
    unittest.main()
