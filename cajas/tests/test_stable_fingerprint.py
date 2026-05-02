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

    def test_jsonl_uuid_drift_normalized(self) -> None:
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            Path(a, "x.jsonl").write_text('{"run_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa","status":"ok"}\n', encoding="utf-8")
            Path(b, "x.jsonl").write_text('{"run_id":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","status":"ok"}\n', encoding="utf-8")
            self.assertEqual(build_stable_fingerprint(root=a)["aggregate_stable_hash"], build_stable_fingerprint(root=b)["aggregate_stable_hash"])

    def test_metric_difference_remains_semantic(self) -> None:
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            Path(a, "m.json").write_text(json.dumps({"metric": 1.0, "status": "ok"}), encoding="utf-8")
            Path(b, "m.json").write_text(json.dumps({"metric": 2.0, "status": "ok"}), encoding="utf-8")
            self.assertNotEqual(build_stable_fingerprint(root=a)["aggregate_stable_hash"], build_stable_fingerprint(root=b)["aggregate_stable_hash"])

    def test_blocked_actions_difference_remains_semantic(self) -> None:
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            Path(a, "f.json").write_text(json.dumps({"blocked_actions": ["no broker"]}), encoding="utf-8")
            Path(b, "f.json").write_text(json.dumps({"blocked_actions": ["no live trading"]}), encoding="utf-8")
            self.assertNotEqual(build_stable_fingerprint(root=a)["aggregate_stable_hash"], build_stable_fingerprint(root=b)["aggregate_stable_hash"])
if __name__ == "__main__": unittest.main()
