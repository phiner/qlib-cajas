from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.registry.run_health_check import check_run_registry_health


class RunHealthCheckTests(unittest.TestCase):
    def test_missing_registry(self) -> None:
        with TemporaryDirectory() as tmp:
            rep = check_run_registry_health(registry_path=Path(tmp) / "missing.jsonl")
            self.assertGreater(rep.warning_count, 0)

    def test_detects_missing_artifact(self) -> None:
        with TemporaryDirectory() as tmp:
            reg = Path(tmp) / "runs.jsonl"
            rec = {"run_name": "r1", "output_dir": str(Path(tmp) / "nope"), "training_executed": True, "run_type": "x", "status": "completed"}
            reg.write_text(json.dumps(rec) + "\n", encoding="utf-8")
            rep = check_run_registry_health(registry_path=reg)
            self.assertGreater(rep.error_count, 0)

    def test_detects_suspicious_metric_and_trading_key(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "r"
            out.mkdir()
            (out / "model_metadata.json").write_text("{}", encoding="utf-8")
            (out / "metrics_valid.json").write_text("{}", encoding="utf-8")
            (out / "run_manifest.json").write_text("{}", encoding="utf-8")
            (out / "metrics_test.json").write_text(json.dumps({"accuracy": 1.2, "profit": 10}), encoding="utf-8")
            reg = Path(tmp) / "runs.jsonl"
            rec = {"run_name": "r1", "output_dir": str(out), "training_executed": True, "run_type": "x", "status": "completed"}
            reg.write_text(json.dumps(rec) + "\n", encoding="utf-8")
            rep = check_run_registry_health(registry_path=reg)
            self.assertGreaterEqual(rep.warning_count, 1)
            self.assertGreaterEqual(rep.error_count, 1)


if __name__ == "__main__":
    unittest.main()
