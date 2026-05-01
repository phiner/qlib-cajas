from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.label_variant_comparison import compare_label_variant_runs


class LabelVariantComparisonTests(unittest.TestCase):
    def test_ranks_runs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, macro in [("a", 0.3), ("b", 0.4)]:
                d = root / name
                d.mkdir()
                (d / "metrics_holdout.json").write_text(json.dumps({"accuracy": 0.5, "macro_f1": macro, "weighted_f1": 0.45}), encoding="utf-8")
                (d / "model_metadata.json").write_text(json.dumps({"label_col": "future_direction_8_thr_0_00010", "label_mode": "multiclass"}), encoding="utf-8")
                (d / "label_distribution_train.json").write_text(json.dumps({"up": 10, "down": 10}), encoding="utf-8")
                (d / "label_distribution_holdout.json").write_text(json.dumps({"up": 10, "down": 10}), encoding="utf-8")
            rep = compare_label_variant_runs(run_dirs=[root / "a", root / "b"])
            self.assertEqual(rep["best_run"], "b")


if __name__ == "__main__":
    unittest.main()
