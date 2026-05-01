from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.baseline.baseline_run_comparison import compare_baseline_runs


class BaselineRunComparisonTests(unittest.TestCase):
    def _mk_run(self, root: Path, name: str, macro: float) -> Path:
        d = root / name
        d.mkdir(parents=True, exist_ok=False)
        (d / "metrics_valid.json").write_text(json.dumps({"accuracy": 0.5, "macro_f1": 0.4, "weighted_f1": 0.45}), encoding="utf-8")
        (d / "metrics_test.json").write_text(json.dumps({"accuracy": 0.6, "macro_f1": macro, "weighted_f1": 0.55}), encoding="utf-8")
        (d / "model_metadata.json").write_text(json.dumps({"model_family_used": "RandomForest"}), encoding="utf-8")
        return d

    def test_compare_picks_best(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            r1 = self._mk_run(root, "r1", 0.31)
            r2 = self._mk_run(root, "r2", 0.42)
            rep = compare_baseline_runs(run_dirs=[r1, r2], primary_metric="test_macro_f1")
            self.assertEqual(rep.best_run, "r2")
            self.assertEqual(len(rep.rows), 2)


if __name__ == "__main__":
    unittest.main()
