from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.baseline.label_variant_trainer import train_label_variant_external_holdout


class LabelVariantTrainerTests(unittest.TestCase):
    def test_binary_drop_flat(self) -> None:
        with TemporaryDirectory() as tmp:
            tr = Path(tmp) / "tr.csv"
            ho = Path(tmp) / "ho.csv"
            rows = []
            for i in range(50):
                label = "flat" if i % 7 == 0 else ("up" if i % 2 == 0 else "down")
                rows.append({"f1": float(i), "f2": float(i % 3), "vlabel": label})
            pd.DataFrame(rows).to_csv(tr, index=False)
            pd.DataFrame(rows).to_csv(ho, index=False)
            rep = train_label_variant_external_holdout(
                train_path=tr,
                holdout_path=ho,
                label_col="vlabel",
                output_dir=Path(tmp) / "runs",
                run_name="r1",
                model_family="RandomForest",
                label_mode="binary_drop_flat",
            )
            self.assertEqual(rep.label_mode, "binary_drop_flat")
            self.assertTrue((Path(rep.output_dir) / "metrics_holdout.json").exists())


if __name__ == "__main__":
    unittest.main()
