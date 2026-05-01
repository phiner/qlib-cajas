from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.seed_stability import run_seed_stability_experiment


class SeedStabilityTests(unittest.TestCase):
    def test_runs_small_seed_set(self) -> None:
        with TemporaryDirectory() as tmp:
            tr = Path(tmp) / "tr.csv"
            ho = Path(tmp) / "ho.csv"
            rows = [{"f1": float(i), "f2": float(i % 5), "future_direction_8": "up" if i % 2 == 0 else "down"} for i in range(60)]
            pd.DataFrame(rows).to_csv(tr, index=False)
            pd.DataFrame(rows).to_csv(ho, index=False)
            rep = run_seed_stability_experiment(
                train_path=tr,
                holdout_path=ho,
                label_col="future_direction_8",
                output_dir=Path(tmp) / "out",
                run_name="r",
                seeds=[7],
                model_family="RandomForest",
            )
            self.assertEqual(len(rep["rows"]), 1)


if __name__ == "__main__":
    unittest.main()
