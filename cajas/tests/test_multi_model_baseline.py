from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.baseline.multi_model_baseline import run_multi_model_baseline


class MultiModelBaselineTests(unittest.TestCase):
    def test_runs_sklearn_models(self) -> None:
        cfg = "cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml"
        data = Path("tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv")
        if not data.exists():
            self.skipTest("prepared dataset not available")
        with TemporaryDirectory() as tmp:
            rep = run_multi_model_baseline(
                config_path=cfg,
                output_dir=tmp,
                run_name="multi",
                model_families=["RandomForest", "HistGradientBoosting"],
                input_override=str(data),
                random_state=2,
            )
            self.assertGreaterEqual(len(rep.model_runs), 1)
            self.assertFalse(rep.trading_metrics_present)
            self.assertTrue((Path(rep.output_dir) / "model_run_status.csv").exists())


if __name__ == "__main__":
    unittest.main()
