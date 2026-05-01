from __future__ import annotations
import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from cajas.reports.stable_fingerprint import build_stable_fingerprint
class StableFingerprintTests(unittest.TestCase):
    def test_identical_semantic_json_hash(self) -> None:
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            Path(a,"x.json").write_text(json.dumps({"created_at_utc":"2026-01-01T00:00:00+00:00","status":"ok"}),encoding="utf-8")
            Path(b,"x.json").write_text(json.dumps({"created_at_utc":"2027-01-01T00:00:00+00:00","status":"ok"}),encoding="utf-8")
            self.assertEqual(build_stable_fingerprint(root=a)["aggregate_stable_hash"], build_stable_fingerprint(root=b)["aggregate_stable_hash"])
if __name__ == "__main__": unittest.main()
