from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.external_holdout_benchmark import build_external_holdout_benchmark


class ExternalHoldoutBenchmarkTests(unittest.TestCase):
    def test_distinguishes_internal_and_external(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            internal = root / "internal_run"
            internal.mkdir()
            (internal / "metrics_valid.json").write_text(json.dumps({"accuracy": 0.5}), encoding="utf-8")
            (internal / "metrics_test.json").write_text(json.dumps({"accuracy": 0.6, "macro_f1": 0.4, "weighted_f1": 0.5}), encoding="utf-8")
            (internal / "model_metadata.json").write_text(json.dumps({"model_family_used": "RF"}), encoding="utf-8")

            external = root / "external_run"
            external.mkdir()
            (external / "metrics_holdout.json").write_text(
                json.dumps({"accuracy": 0.7, "macro_f1": 0.55, "weighted_f1": 0.66}), encoding="utf-8"
            )
            (external / "model_metadata.json").write_text(json.dumps({"model_family_used": "RF"}), encoding="utf-8")

            rep = build_external_holdout_benchmark(run_dirs=[internal, external])
            self.assertEqual(rep.internal_split_count, 1)
            self.assertEqual(rep.external_holdout_count, 1)
            self.assertEqual(rep.best_external_holdout_by_macro_f1, "external_run")
            self.assertFalse(rep.trading_metrics_present)


if __name__ == "__main__":
    unittest.main()
