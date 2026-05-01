from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.registry.registry_cleanup import classify_run_registry_records, write_filtered_registry_copy


class RegistryCleanupTests(unittest.TestCase):
    def test_classifies_temp_and_active(self) -> None:
        with TemporaryDirectory() as tmp:
            active_dir = Path(tmp) / "active"
            active_dir.mkdir()
            (active_dir / "run_manifest.json").write_text("{}", encoding="utf-8")
            reg = Path(tmp) / "runs.jsonl"
            rows = [
                {"run_name": "a", "run_id": "1", "output_dir": str(active_dir)},
                {"run_name": "b", "run_id": "2", "output_dir": "/tmp/tmp123/x"},
            ]
            reg.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            rep = classify_run_registry_records(registry_path=reg)
            kinds = {c.classification for c in rep.classifications}
            self.assertIn("active", kinds)
            self.assertIn("temp_test", kinds)

    def test_filtered_copy(self) -> None:
        with TemporaryDirectory() as tmp:
            reg = Path(tmp) / "runs.jsonl"
            rows = [
                {"run_name": "a", "run_id": "1", "output_dir": "/tmp/tmp123/x"},
                {"run_name": "b", "run_id": "2", "output_dir": "/home/u/keep"},
            ]
            reg.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            out = Path(tmp) / "filtered.jsonl"
            stats = write_filtered_registry_copy(registry_path=reg, output_path=out, exclude_temp_test=True)
            self.assertEqual(stats["removed"], 1)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
