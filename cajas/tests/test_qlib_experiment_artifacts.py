from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_experiment_artifacts import write_experiment_artifacts


class QlibExperimentArtifactsTests(unittest.TestCase):
    def test_write_json_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            rep = write_experiment_artifacts(out_dir=out, artifacts={"metrics.json": {"a": 1}})
            self.assertTrue(Path(rep["metrics.json"]).exists())


if __name__ == "__main__":
    unittest.main()
